from datetime import UTC, date, datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.database import get_session
from app.models import UsageDaily, UsageModel
from app.schemas import DailyUsageResponse, DimensionUsageResponse, ModelUsageResponse, SummaryResponse, UserResponse

router = APIRouter(tags=["usage"])


def _user_id(user_id: str | None, user_id_camel: str | None) -> str | None:
    return user_id or user_id_camel


def _filtered_usage(
    *,
    user_id: str | None = None,
    project: str | None = None,
    source: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
) -> Select[tuple[UsageDaily]]:
    stmt = select(UsageDaily)
    if user_id:
        stmt = stmt.where(UsageDaily.user_id == user_id)
    if project:
        stmt = stmt.where(UsageDaily.project == project)
    if source:
        stmt = stmt.where(UsageDaily.source == source)
    if from_date:
        stmt = stmt.where(UsageDaily.date >= from_date)
    if to_date:
        stmt = stmt.where(UsageDaily.date <= to_date)
    return stmt


def _sum_columns() -> tuple:
    return (
        func.coalesce(func.sum(UsageDaily.input_tokens), 0).label("input_tokens"),
        func.coalesce(func.sum(UsageDaily.output_tokens), 0).label("output_tokens"),
        func.coalesce(func.sum(UsageDaily.cache_creation_tokens), 0).label("cache_creation_tokens"),
        func.coalesce(func.sum(UsageDaily.cache_read_tokens), 0).label("cache_read_tokens"),
        func.coalesce(func.sum(UsageDaily.total_tokens), 0).label("total_tokens"),
        func.coalesce(func.sum(UsageDaily.total_cost), 0.0).label("cost_usd"),
    )


@router.get("/api/users", response_model=list[UserResponse])
def list_users(session: Session = Depends(get_session)) -> list[UserResponse]:
    rows = session.execute(select(UsageDaily.user_id).distinct().order_by(UsageDaily.user_id)).all()
    return [UserResponse(id=row.user_id, name=row.user_id, githubUsername=row.user_id) for row in rows]


@router.get("/api/summary", response_model=SummaryResponse)
def summary(
    user_id: str | None = Query(default=None),
    user_id_camel: str | None = Query(default=None, alias="userId"),
    session: Session = Depends(get_session),
) -> SummaryResponse:
    resolved_user_id = _user_id(user_id, user_id_camel)
    today = datetime.now(UTC).date()
    month_start = today.replace(day=1)

    total_stmt = select(
        func.coalesce(func.sum(UsageDaily.total_tokens), 0),
        func.coalesce(func.sum(UsageDaily.total_cost), 0.0),
    )
    monthly_stmt = select(func.coalesce(func.sum(UsageDaily.total_tokens), 0)).where(UsageDaily.date >= month_start)
    today_stmt = select(func.coalesce(func.sum(UsageDaily.total_tokens), 0)).where(UsageDaily.date == today)

    top_model_stmt = (
        select(UsageModel.model, func.coalesce(func.sum(UsageModel.total_tokens), 0).label("tokens"))
        .join(UsageDaily, UsageDaily.id == UsageModel.usage_id)
        .group_by(UsageModel.model)
        .order_by(func.sum(UsageModel.total_tokens).desc())
        .limit(1)
    )

    if resolved_user_id:
        total_stmt = total_stmt.where(UsageDaily.user_id == resolved_user_id)
        monthly_stmt = monthly_stmt.where(UsageDaily.user_id == resolved_user_id)
        today_stmt = today_stmt.where(UsageDaily.user_id == resolved_user_id)
        top_model_stmt = top_model_stmt.where(UsageDaily.user_id == resolved_user_id)

    total_tokens, cost_usd = session.execute(total_stmt).one()
    monthly_tokens = session.scalar(monthly_stmt) or 0
    today_tokens = session.scalar(today_stmt) or 0
    top_model = session.execute(top_model_stmt).first()

    return SummaryResponse(
        user_id=resolved_user_id or "all",
        today_tokens=int(today_tokens),
        monthly_tokens=int(monthly_tokens),
        total_tokens=int(total_tokens),
        cost_usd=float(cost_usd),
        most_used_model=top_model.model if top_model else "unknown",
    )


@router.get("/api/usage/daily", response_model=list[DailyUsageResponse])
def usage_by_date(
    user_id: str | None = Query(default=None),
    user_id_camel: str | None = Query(default=None, alias="userId"),
    project: str | None = None,
    source: str | None = None,
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    session: Session = Depends(get_session),
) -> list[DailyUsageResponse]:
    base = _filtered_usage(
        user_id=_user_id(user_id, user_id_camel),
        project=project,
        source=source,
        from_date=from_date,
        to_date=to_date,
    ).subquery()

    rows = session.execute(
        select(
            base.c.date,
            func.coalesce(func.sum(base.c.input_tokens), 0).label("input_tokens"),
            func.coalesce(func.sum(base.c.output_tokens), 0).label("output_tokens"),
            func.coalesce(func.sum(base.c.cache_creation_tokens), 0).label("cache_creation_tokens"),
            func.coalesce(func.sum(base.c.cache_read_tokens), 0).label("cache_read_tokens"),
            func.coalesce(func.sum(base.c.total_tokens), 0).label("total_tokens"),
            func.coalesce(func.sum(base.c.total_cost), 0.0).label("cost_usd"),
        )
        .group_by(base.c.date)
        .order_by(base.c.date)
    ).all()

    return [DailyUsageResponse(**row._mapping) for row in rows]


def _dimension_usage(
    *,
    dimension: Literal["project", "source"],
    user_id: str | None,
    from_date: date | None,
    to_date: date | None,
    session: Session,
) -> list[DimensionUsageResponse]:
    field = UsageDaily.project if dimension == "project" else UsageDaily.source
    stmt = select(field.label("name"), *_sum_columns()).group_by(field).order_by(func.sum(UsageDaily.total_tokens).desc())
    if user_id:
        stmt = stmt.where(UsageDaily.user_id == user_id)
    if from_date:
        stmt = stmt.where(UsageDaily.date >= from_date)
    if to_date:
        stmt = stmt.where(UsageDaily.date <= to_date)
    return [DimensionUsageResponse(**row._mapping) for row in session.execute(stmt).all()]


@router.get("/api/usage/projects", response_model=list[DimensionUsageResponse])
def usage_by_project(
    user_id: str | None = Query(default=None),
    user_id_camel: str | None = Query(default=None, alias="userId"),
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    session: Session = Depends(get_session),
) -> list[DimensionUsageResponse]:
    return _dimension_usage(
        dimension="project",
        user_id=_user_id(user_id, user_id_camel),
        from_date=from_date,
        to_date=to_date,
        session=session,
    )


@router.get("/api/usage/sources", response_model=list[DimensionUsageResponse])
def usage_by_source(
    user_id: str | None = Query(default=None),
    user_id_camel: str | None = Query(default=None, alias="userId"),
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    session: Session = Depends(get_session),
) -> list[DimensionUsageResponse]:
    return _dimension_usage(
        dimension="source",
        user_id=_user_id(user_id, user_id_camel),
        from_date=from_date,
        to_date=to_date,
        session=session,
    )


@router.get("/api/usage/aggregate", response_model=list[DimensionUsageResponse])
def usage_aggregate(
    group_by: Literal["project", "source"] = "project",
    user_id: str | None = Query(default=None),
    user_id_camel: str | None = Query(default=None, alias="userId"),
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    session: Session = Depends(get_session),
) -> list[DimensionUsageResponse]:
    return _dimension_usage(
        dimension=group_by,
        user_id=_user_id(user_id, user_id_camel),
        from_date=from_date,
        to_date=to_date,
        session=session,
    )


@router.get("/api/usage/models", response_model=list[ModelUsageResponse])
def usage_by_model(
    user_id: str | None = Query(default=None),
    user_id_camel: str | None = Query(default=None, alias="userId"),
    project: str | None = None,
    source: str | None = None,
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    session: Session = Depends(get_session),
) -> list[ModelUsageResponse]:
    stmt = (
        select(
            UsageModel.model,
            func.coalesce(func.sum(UsageModel.total_tokens), 0).label("total_tokens"),
            func.coalesce(func.sum(UsageModel.total_cost), 0.0).label("cost_usd"),
        )
        .join(UsageDaily, UsageDaily.id == UsageModel.usage_id)
        .group_by(UsageModel.model)
        .order_by(func.sum(UsageModel.total_tokens).desc())
    )
    resolved_user_id = _user_id(user_id, user_id_camel)
    if resolved_user_id:
        stmt = stmt.where(UsageDaily.user_id == resolved_user_id)
    if project:
        stmt = stmt.where(UsageDaily.project == project)
    if source:
        stmt = stmt.where(UsageDaily.source == source)
    if from_date:
        stmt = stmt.where(UsageDaily.date >= from_date)
    if to_date:
        stmt = stmt.where(UsageDaily.date <= to_date)

    return [ModelUsageResponse(**row._mapping) for row in session.execute(stmt).all()]


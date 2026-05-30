from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_session
from app.models import UsageDaily
from app.schemas import BadgeStyle, BadgeType
from app.svg import auto_color, compact_number, render_badge

router = APIRouter(tags=["badges"])


def _badge_totals(
    session: Session,
    *,
    user_id: str | None,
    badge_type: BadgeType,
    project: str | None,
    source: str | None,
) -> tuple[int, float]:
    today = datetime.now(UTC).date()
    stmt = select(
        func.coalesce(func.sum(UsageDaily.total_tokens), 0),
        func.coalesce(func.sum(UsageDaily.total_cost), 0.0),
    )

    if user_id:
        stmt = stmt.where(UsageDaily.user_id == user_id)
    if project:
        stmt = stmt.where(UsageDaily.project == project)
    if source:
        stmt = stmt.where(UsageDaily.source == source)
    if badge_type == "daily":
        stmt = stmt.where(UsageDaily.date == today)
    elif badge_type == "monthly":
        stmt = stmt.where(UsageDaily.date >= today.replace(day=1))

    tokens, cost = session.execute(stmt).one()
    return int(tokens), float(cost)


def _badge_response(
    *,
    user_id: str | None,
    badge_type: BadgeType,
    style: BadgeStyle,
    color: str,
    project: str | None,
    source: str | None,
    session: Session,
) -> Response:
    tokens, cost = _badge_totals(
        session,
        user_id=user_id,
        badge_type=badge_type,
        project=project,
        source=source,
    )
    label = f"{user_id or 'all'} {badge_type}"
    if badge_type == "cost":
        message = f"${cost:.2f}"
    elif tokens == 0:
        message = "no data"
    else:
        message = f"{compact_number(tokens)} tokens"

    resolved_color = auto_color(tokens) if color == "auto" else color
    svg = render_badge(label=label, message=message, color=resolved_color, style=style)
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": "max-age=300"},
    )


@router.get("/api/badge.svg")
def api_badge(
    user_id: str | None = Query(default=None),
    user_id_camel: str | None = Query(default=None, alias="userId"),
    badge_type: BadgeType = Query(default="monthly", alias="type"),
    style: BadgeStyle = "flat",
    color: str = "auto",
    project: str | None = None,
    source: str | None = None,
    session: Session = Depends(get_session),
) -> Response:
    return _badge_response(
        user_id=user_id or user_id_camel,
        badge_type=badge_type,
        style=style,
        color=color,
        project=project,
        source=source,
        session=session,
    )


@router.get("/badge/{user_id}.svg")
@router.get("/badge/{user_id}")
def public_badge(
    user_id: str,
    badge_type: BadgeType = Query(default="monthly", alias="type"),
    style: BadgeStyle = "flat",
    color: str = "auto",
    project: str | None = None,
    source: str | None = None,
    session: Session = Depends(get_session),
) -> Response:
    return _badge_response(
        user_id=user_id,
        badge_type=badge_type,
        style=style,
        color=color,
        project=project,
        source=source,
        session=session,
    )


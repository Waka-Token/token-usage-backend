import json

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_session
from app.models import UsageDaily, UsageModel
from app.normalizer import normalize_ccusage_daily
from app.schemas import CollectRequest, CollectResponse, NormalizedUsageEntry

router = APIRouter(tags=["collection"])


def _upsert_entry(session: Session, entry: NormalizedUsageEntry, hostname: str | None) -> str:
    existing = session.scalar(
        select(UsageDaily).where(
            UsageDaily.user_id == entry.user_id,
            UsageDaily.date == entry.date,
            UsageDaily.project == entry.project,
            UsageDaily.source == entry.source,
        )
    )

    status = "updated" if existing else "inserted"
    record = existing or UsageDaily(
        user_id=entry.user_id,
        date=entry.date,
        project=entry.project,
        source=entry.source,
    )

    record.input_tokens = entry.input_tokens
    record.output_tokens = entry.output_tokens
    record.cache_creation_tokens = entry.cache_creation_tokens
    record.cache_read_tokens = entry.cache_read_tokens
    record.total_tokens = entry.total_tokens
    record.total_cost = entry.total_cost
    record.models_json = json.dumps(entry.models, ensure_ascii=False)
    record.raw_json = json.dumps(entry.raw, ensure_ascii=False)
    record.hostname = hostname

    if existing is None:
        session.add(record)
        session.flush()
    else:
        session.query(UsageModel).filter(UsageModel.usage_id == record.id).delete(synchronize_session=False)

    for model in entry.model_breakdowns:
        session.add(
            UsageModel(
                usage_id=record.id,
                model=model.model,
                input_tokens=model.input_tokens,
                output_tokens=model.output_tokens,
                cache_creation_tokens=model.cache_creation_tokens,
                cache_read_tokens=model.cache_read_tokens,
                total_tokens=model.total_tokens,
                total_cost=model.total_cost,
            )
        )
    return status


@router.post("/api/collect", response_model=CollectResponse, status_code=202)
@router.post("/api/reports", response_model=CollectResponse, status_code=202)
@router.post("/api/usage/upload", response_model=CollectResponse, status_code=202)
def collect_usage(payload: CollectRequest, session: Session = Depends(get_session)) -> CollectResponse:
    raw = payload.raw_ccusage()
    entries = normalize_ccusage_daily(user_id=payload.user_id, source=payload.source, raw=raw)

    inserted = 0
    updated = 0
    for entry in entries:
        status = _upsert_entry(session, entry, payload.hostname)
        if status == "inserted":
            inserted += 1
        else:
            updated += 1

    session.commit()
    return CollectResponse(accepted=len(entries), inserted=inserted, updated=updated)


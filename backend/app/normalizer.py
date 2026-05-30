import json
from datetime import date
from typing import Any

from app.schemas import ModelUsageIn, NormalizedUsageEntry


def _int_value(data: dict[str, Any], *keys: str) -> int:
    for key in keys:
        value = data.get(key)
        if value is not None:
            return int(value)
    return 0


def _float_value(data: dict[str, Any], *keys: str) -> float:
    for key in keys:
        value = data.get(key)
        if value is not None:
            return float(value)
    return 0.0


def _entry_date(data: dict[str, Any]) -> date | None:
    value = data.get("date") or data.get("period")
    if not value:
        return None
    return date.fromisoformat(str(value)[:10])


def _models(data: dict[str, Any]) -> list[str]:
    models = data.get("modelsUsed") or data.get("models") or []
    if isinstance(models, str):
        return [models]
    if isinstance(models, list):
        return [str(model) for model in models]
    return []


def _model_breakdowns(data: dict[str, Any], models: list[str]) -> list[ModelUsageIn]:
    breakdown = data.get("breakdown") or data.get("modelBreakdowns") or data.get("model_breakdowns")
    parsed: list[ModelUsageIn] = []

    if isinstance(breakdown, dict):
        for model, values in breakdown.items():
            if isinstance(values, dict):
                parsed.append(_model_usage(str(model), values))
    elif isinstance(breakdown, list):
        for item in breakdown:
            if not isinstance(item, dict):
                continue
            model = item.get("model") or item.get("modelName") or item.get("name")
            if model:
                parsed.append(_model_usage(str(model), item))

    if parsed:
        return parsed

    if len(models) == 1:
        return [_model_usage(models[0], data)]
    if models:
        return [ModelUsageIn(model="combined", total_tokens=_int_value(data, "totalTokens", "total_tokens"))]
    return []


def _model_usage(model: str, data: dict[str, Any]) -> ModelUsageIn:
    input_tokens = _int_value(data, "inputTokens", "input_tokens")
    output_tokens = _int_value(data, "outputTokens", "output_tokens")
    cache_creation_tokens = _int_value(data, "cacheCreationTokens", "cache_creation_tokens", "cachedInputTokens")
    cache_read_tokens = _int_value(data, "cacheReadTokens", "cache_read_tokens")
    total_tokens = _int_value(data, "totalTokens", "total_tokens")
    if total_tokens == 0:
        total_tokens = input_tokens + output_tokens + cache_creation_tokens + cache_read_tokens
    return ModelUsageIn(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_creation_tokens=cache_creation_tokens,
        cache_read_tokens=cache_read_tokens,
        total_tokens=total_tokens,
        total_cost=_float_value(data, "totalCost", "costUSD", "cost_usd", "total_cost"),
    )


def _daily_items(raw: dict[str, Any] | list[dict[str, Any]]) -> list[tuple[str, dict[str, Any]]]:
    if isinstance(raw, list):
        return [("default", item) for item in raw if isinstance(item, dict)]

    projects = raw.get("projects")
    if isinstance(projects, dict):
        items: list[tuple[str, dict[str, Any]]] = []
        for project, project_entries in projects.items():
            if isinstance(project_entries, dict):
                project_entries = project_entries.get("daily") or project_entries.get("data") or []
            if isinstance(project_entries, list):
                items.extend((str(project), entry) for entry in project_entries if isinstance(entry, dict))
        return items

    daily = raw.get("daily") or raw.get("data") or []
    if isinstance(daily, list):
        return [(str(raw.get("project") or "default"), item) for item in daily if isinstance(item, dict)]

    return []


def normalize_ccusage_daily(
    *,
    user_id: str,
    source: str,
    raw: dict[str, Any] | list[dict[str, Any]],
) -> list[NormalizedUsageEntry]:
    normalized: list[NormalizedUsageEntry] = []
    for project, item in _daily_items(raw):
        parsed_date = _entry_date(item)
        if parsed_date is None:
            continue

        input_tokens = _int_value(item, "inputTokens", "input_tokens")
        output_tokens = _int_value(item, "outputTokens", "output_tokens")
        cache_creation_tokens = _int_value(item, "cacheCreationTokens", "cache_creation_tokens", "cachedInputTokens")
        cache_read_tokens = _int_value(item, "cacheReadTokens", "cache_read_tokens")
        total_tokens = _int_value(item, "totalTokens", "total_tokens")
        if total_tokens == 0:
            total_tokens = input_tokens + output_tokens + cache_creation_tokens + cache_read_tokens
        models = _models(item)
        normalized.append(
            NormalizedUsageEntry(
                user_id=user_id,
                date=parsed_date,
                project=str(item.get("project") or item.get("instance") or project or "default"),
                source=str(item.get("source") or item.get("agent") or source or "ccusage"),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_creation_tokens=cache_creation_tokens,
                cache_read_tokens=cache_read_tokens,
                total_tokens=total_tokens,
                total_cost=_float_value(item, "totalCost", "costUSD", "cost_usd", "total_cost"),
                models=models,
                model_breakdowns=_model_breakdowns(item, models),
                raw=json.loads(json.dumps(item, default=str)),
            )
        )
    return normalized


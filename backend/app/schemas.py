from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field


class CollectRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    source: str = Field(default="ccusage", min_length=1, max_length=128)
    hostname: str | None = None
    ccusage: dict[str, Any] | None = None
    raw: dict[str, Any] | None = None
    data: dict[str, Any] | list[dict[str, Any]] | None = None

    model_config = ConfigDict(extra="allow")

    def raw_ccusage(self) -> dict[str, Any] | list[dict[str, Any]]:
        if self.ccusage is not None:
            return self.ccusage
        if self.raw is not None:
            return self.raw
        if self.data is not None:
            return self.data
        extra = self.model_extra or {}
        if "projects" in extra or "daily" in extra or "totals" in extra:
            return dict(extra)
        return {}


class ModelUsageIn(BaseModel):
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0


class NormalizedUsageEntry(BaseModel):
    user_id: str
    date: date
    project: str
    source: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    models: list[str] = Field(default_factory=list)
    model_breakdowns: list[ModelUsageIn] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class CollectResponse(BaseModel):
    accepted: int
    inserted: int
    updated: int
    skipped: int = 0
    upsert_key: str = "user_id + date + project + source"


class UserResponse(BaseModel):
    id: str
    name: str
    githubUsername: str


class SummaryResponse(BaseModel):
    user_id: str
    today_tokens: int
    monthly_tokens: int
    total_tokens: int
    cost_usd: float
    most_used_model: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def userId(self) -> str:
        return self.user_id

    @computed_field  # type: ignore[prop-decorator]
    @property
    def todayTokens(self) -> int:
        return self.today_tokens

    @computed_field  # type: ignore[prop-decorator]
    @property
    def monthlyTokens(self) -> int:
        return self.monthly_tokens

    @computed_field  # type: ignore[prop-decorator]
    @property
    def totalTokens(self) -> int:
        return self.total_tokens

    @computed_field  # type: ignore[prop-decorator]
    @property
    def costUsd(self) -> float:
        return self.cost_usd

    @computed_field  # type: ignore[prop-decorator]
    @property
    def mostUsedModel(self) -> str:
        return self.most_used_model


class DailyUsageResponse(BaseModel):
    date: date
    input_tokens: int
    output_tokens: int
    cache_creation_tokens: int
    cache_read_tokens: int
    total_tokens: int
    cost_usd: float

    @computed_field  # type: ignore[prop-decorator]
    @property
    def totalTokens(self) -> int:
        return self.total_tokens

    @computed_field  # type: ignore[prop-decorator]
    @property
    def costUsd(self) -> float:
        return self.cost_usd


class DimensionUsageResponse(BaseModel):
    name: str
    input_tokens: int
    output_tokens: int
    cache_creation_tokens: int
    cache_read_tokens: int
    total_tokens: int
    cost_usd: float


class ModelUsageResponse(BaseModel):
    model: str
    total_tokens: int
    cost_usd: float

    @computed_field  # type: ignore[prop-decorator]
    @property
    def totalTokens(self) -> int:
        return self.total_tokens


BadgeType = Literal["daily", "monthly", "total", "cost"]
BadgeStyle = Literal["flat", "flat-square", "for-the-badge"]


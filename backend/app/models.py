from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def new_id() -> str:
    return uuid4().hex


class UsageDaily(Base):
    __tablename__ = "usage_daily"
    __table_args__ = (
        UniqueConstraint("user_id", "date", "project", "source", name="uq_usage_user_date_project_source"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    project: Mapped[str] = mapped_column(String(512), index=True, default="default")
    source: Mapped[str] = mapped_column(String(128), index=True, default="ccusage")
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_creation_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_read_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0)
    models_json: Mapped[str] = mapped_column(Text, default="[]")
    raw_json: Mapped[str] = mapped_column(Text, default="{}")
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    models: Mapped[list["UsageModel"]] = relationship(
        back_populates="usage",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class UsageModel(Base):
    __tablename__ = "usage_models"
    __table_args__ = (UniqueConstraint("usage_id", "model", name="uq_usage_model"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    usage_id: Mapped[str] = mapped_column(ForeignKey("usage_daily.id", ondelete="CASCADE"), index=True)
    model: Mapped[str] = mapped_column(String(255), index=True)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_creation_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_read_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0)

    usage: Mapped[UsageDaily] = relationship(back_populates="models")


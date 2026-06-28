from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    machine_id: Mapped[str] = mapped_column(String(100), index=True)
    image_path: Mapped[str] = mapped_column(Text)
    predicted_class: Mapped[str] = mapped_column(String(50), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    risk_level: Mapped[str] = mapped_column(String(20), index=True)
    symptoms: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="open", index=True)
    model_version: Mapped[str] = mapped_column(String(100), default="unknown")
    analysis_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    work_orders: Mapped[list[WorkOrder]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    machine_id: Mapped[str] = mapped_column(String(100), index=True)
    priority: Mapped[str] = mapped_column(String(20), index=True)
    actions_json: Mapped[str] = mapped_column(Text)
    approved_by: Mapped[str] = mapped_column(String(100), default="human-operator")
    status: Mapped[str] = mapped_column(String(30), default="created", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    incident: Mapped[Incident] = relationship(back_populates="work_orders")

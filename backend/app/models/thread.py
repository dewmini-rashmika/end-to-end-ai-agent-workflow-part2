"""
Thread model — one thread per trip planning session per user.
Threads contain messages and a shared state (TravelState).
"""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Thread(Base):
    __tablename__ = "threads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(256), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="active"
    )
    # status: active | awaiting_hitl | completed | rejected | error

    # Stored TravelState snapshot — updated after each agent run
    travel_state: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=True, default=dict
    )

    # HITL metadata
    hitl_status: Mapped[str] = mapped_column(
        String(32), nullable=True
    )
    # hitl_status: pending | approved | changes_requested | rejected
    hitl_feedback: Mapped[str] = mapped_column(Text, nullable=True)
    hitl_requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    hitl_resolved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="threads")  # noqa: F821
    messages: Mapped[list["Message"]] = relationship(  # noqa: F821
        "Message", back_populates="thread", cascade="all, delete-orphan",
        order_by="Message.created_at"
    )
    checkpoints: Mapped[list["AgentCheckpoint"]] = relationship(  # noqa: F821
        "AgentCheckpoint", back_populates="thread", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Thread id={self.id} user={self.user_id} status={self.status}>"

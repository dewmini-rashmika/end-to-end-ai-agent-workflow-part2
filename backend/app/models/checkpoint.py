"""
Agent checkpoint — snapshots of agent state for resume / rollback.
Enables HITL re-invocation and partial replanning.
"""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AgentCheckpoint(Base):
    __tablename__ = "agent_checkpoints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Which agent produced this checkpoint
    agent_name: Mapped[str] = mapped_column(String(64), nullable=False)
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Full agent output snapshot
    state_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="completed"
    )
    # status: running | completed | failed | rolled_back

    error_detail: Mapped[str] = mapped_column(String(1024), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    thread: Mapped["Thread"] = relationship(  # noqa: F821
        "Thread", back_populates="checkpoints"
    )

    def __repr__(self) -> str:
        return (
            f"<AgentCheckpoint id={self.id} agent={self.agent_name} "
            f"step={self.step_number} status={self.status}>"
        )

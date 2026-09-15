"""
Message model — individual chat messages within a thread.
Roles: user | assistant | system | tool | agent
"""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(32), nullable=False
    )
    # role: user | assistant | system | tool | agent | hitl

    content: Mapped[str] = mapped_column(Text, nullable=False)
    agent_name: Mapped[str] = mapped_column(
        String(64), nullable=True
    )  # which agent produced this message

    # Structured payload (tool calls, agent results, guardrail verdict, etc.)
    # NOTE: "metadata" is reserved by SQLAlchemy — we use "msg_metadata" as the
    # Python attribute but map it to the "metadata" column in the DB.
    msg_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=True, default=dict
    )

    # Token usage tracking
    prompt_tokens: Mapped[int] = mapped_column(nullable=True)
    completion_tokens: Mapped[int] = mapped_column(nullable=True)
    model_used: Mapped[str] = mapped_column(String(128), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    thread: Mapped["Thread"] = relationship("Thread", back_populates="messages")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Message id={self.id} role={self.role} thread={self.thread_id}>"

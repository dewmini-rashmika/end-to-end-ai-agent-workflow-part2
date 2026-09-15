"""
Thread service — manages conversation threads (one per trip planning session).
Each user account gets isolated threads with full message history.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.thread import Thread
from app.models.message import Message
from app.models.checkpoint import AgentCheckpoint
from app.agents.state import TravelState
from app.config.logging_config import get_logger

logger = get_logger(__name__)


# ── Thread CRUD ───────────────────────────────────────────────────────────────

async def create_thread(
    db: AsyncSession,
    user_id: str,
    title: str | None = None,
) -> Thread:
    """Create a new trip planning thread for a user."""
    thread = Thread(
        user_id=user_id,
        title=title or "New Trip",
        status="active",
    )
    db.add(thread)
    await db.flush()
    logger.info("thread_created", thread_id=str(thread.id), user_id=user_id)
    return thread


async def get_thread(
    db: AsyncSession, thread_id: str, user_id: str
) -> Thread | None:
    """Get a thread by ID, scoped to a specific user."""
    result = await db.execute(
        select(Thread).where(
            Thread.id == thread_id,
            Thread.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def get_thread_with_messages(
    db: AsyncSession, thread_id: str, user_id: str
) -> Thread | None:
    """Get thread with all messages eagerly loaded."""
    result = await db.execute(
        select(Thread)
        .options(selectinload(Thread.messages))
        .where(Thread.id == thread_id, Thread.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def list_threads(
    db: AsyncSession,
    user_id: str,
    limit: int = 20,
    offset: int = 0,
    status: str | None = None,
) -> list[Thread]:
    """List all threads for a user, newest first."""
    query = (
        select(Thread)
        .where(Thread.user_id == user_id)
        .order_by(desc(Thread.updated_at))
        .limit(limit)
        .offset(offset)
    )
    if status:
        query = query.where(Thread.status == status)

    result = await db.execute(query)
    return list(result.scalars().all())


async def update_thread_state(
    db: AsyncSession,
    thread_id: str,
    state: TravelState,
    status: str | None = None,
) -> Thread | None:
    """Persist updated TravelState to a thread."""
    result = await db.execute(select(Thread).where(Thread.id == thread_id))
    thread = result.scalar_one_or_none()
    if not thread:
        return None

    thread.travel_state = state.to_db_dict()
    if status:
        thread.status = status
    if state.hitl_status:
        thread.hitl_status = state.hitl_status
    if state.hitl_feedback:
        thread.hitl_feedback = state.hitl_feedback

    # Auto-generate title from destination if not set
    if thread.title in (None, "New Trip") and state.trip_constraints.destination:
        dest = state.trip_constraints.destination
        dates = state.trip_constraints.departure_date or ""
        thread.title = f"Trip to {dest}" + (f" ({dates})" if dates else "")

    await db.flush()
    return thread


async def delete_thread(
    db: AsyncSession, thread_id: str, user_id: str
) -> bool:
    """Delete a thread (cascade deletes messages + checkpoints)."""
    thread = await get_thread(db, thread_id, user_id)
    if not thread:
        return False
    await db.delete(thread)
    await db.flush()
    logger.info("thread_deleted", thread_id=thread_id)
    return True


# ── Message CRUD ──────────────────────────────────────────────────────────────

async def add_message(
    db: AsyncSession,
    thread_id: str,
    role: str,
    content: str,
    agent_name: str | None = None,
    metadata: dict | None = None,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    model_used: str | None = None,
) -> Message:
    """Append a message to a thread."""
    msg = Message(
        thread_id=thread_id,
        role=role,
        content=content,
        agent_name=agent_name,
        msg_metadata=metadata or {},
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        model_used=model_used,
    )
    db.add(msg)
    await db.flush()
    return msg


async def get_thread_messages(
    db: AsyncSession,
    thread_id: str,
    limit: int = 100,
    offset: int = 0,
) -> list[Message]:
    """Get messages for a thread in chronological order."""
    result = await db.execute(
        select(Message)
        .where(Message.thread_id == thread_id)
        .order_by(Message.created_at)
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


# ── Checkpoints ───────────────────────────────────────────────────────────────

async def save_checkpoint(
    db: AsyncSession,
    thread_id: str,
    agent_name: str,
    step_number: int,
    state_snapshot: dict,
    status: str = "completed",
    error_detail: str | None = None,
) -> AgentCheckpoint:
    """Save an agent checkpoint for resume/rollback."""
    checkpoint = AgentCheckpoint(
        thread_id=thread_id,
        agent_name=agent_name,
        step_number=step_number,
        state_snapshot=state_snapshot,
        status=status,
        error_detail=error_detail,
    )
    db.add(checkpoint)
    await db.flush()
    return checkpoint


async def get_latest_checkpoint(
    db: AsyncSession, thread_id: str, agent_name: str | None = None
) -> AgentCheckpoint | None:
    """Get the most recent checkpoint for a thread/agent."""
    query = (
        select(AgentCheckpoint)
        .where(AgentCheckpoint.thread_id == thread_id)
        .order_by(desc(AgentCheckpoint.created_at))
        .limit(1)
    )
    if agent_name:
        query = query.where(AgentCheckpoint.agent_name == agent_name)
    result = await db.execute(query)
    return result.scalar_one_or_none()

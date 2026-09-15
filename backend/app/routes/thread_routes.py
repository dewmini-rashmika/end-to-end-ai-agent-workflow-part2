"""
Thread / History routes — list threads, get thread detail, messages, delete.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.models.user import User
from app.services.thread_service import (
    list_threads,
    get_thread_with_messages,
    get_thread_messages,
    delete_thread,
)
from app.utils.dependencies import get_current_active_user
from app.utils.schemas import (
    ThreadListResponse,
    ThreadSummary,
    ThreadDetailResponse,
    MessageSchema,
)
from app.config.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/threads", tags=["Thread History"])


@router.get("", response_model=ThreadListResponse)
async def list_user_threads(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all trip planning threads for the current user.
    Used by the History page — shows thread IDs, titles, dates.
    """
    offset = (page - 1) * page_size
    threads = await list_threads(
        db,
        user_id=str(current_user.id),
        limit=page_size,
        offset=offset,
        status=status,
    )

    # Build summaries with destination from travel_state
    summaries = []
    for t in threads:
        destination = None
        departure_date = None
        if t.travel_state:
            tc = t.travel_state.get("trip_constraints", {})
            destination = tc.get("destination")
            departure_date = tc.get("departure_date")

        summaries.append(
            ThreadSummary(
                id=t.id,
                title=t.title,
                status=t.status,
                hitl_status=t.hitl_status,
                created_at=t.created_at,
                updated_at=t.updated_at,
                destination=destination,
                departure_date=departure_date,
            )
        )

    return ThreadListResponse(
        threads=summaries,
        total=len(summaries),
        page=page,
        page_size=page_size,
    )


@router.get("/{thread_id}", response_model=ThreadDetailResponse)
async def get_thread_detail(
    thread_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get full thread detail including all messages.
    Used when user clicks a history entry.
    """
    thread = await get_thread_with_messages(
        db, thread_id=thread_id, user_id=str(current_user.id)
    )
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found.")

    return thread


@router.get("/{thread_id}/messages", response_model=list[MessageSchema])
async def get_messages(
    thread_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get paginated messages for a thread.
    Verifies thread ownership before returning messages.
    """
    from app.services.thread_service import get_thread
    thread = await get_thread(db, thread_id, str(current_user.id))
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found.")

    messages = await get_thread_messages(db, thread_id, limit=limit, offset=offset)
    return messages


@router.delete("/{thread_id}", status_code=204)
async def remove_thread(
    thread_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a trip planning thread and all its history."""
    deleted = await delete_thread(db, thread_id, str(current_user.id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Thread not found.")

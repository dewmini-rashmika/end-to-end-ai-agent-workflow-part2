"""
Trip planning routes — start a plan, stream SSE progress, HITL decisions.
"""
import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.models.user import User
from app.services.trip_orchestrator import trip_orchestrator
from app.hitl.hitl_service import HITLDecision
from app.utils.dependencies import get_current_active_user
from app.utils.schemas import PlanTripRequest, HITLDecisionRequest, PlanResponse
from app.config.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/trips", tags=["Trip Planning"])


@router.post("/plan", response_model=PlanResponse)
async def plan_trip(
    body: PlanTripRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Start a new trip planning session.
    
    Runs: guardrails → supervisor → specialist agents → requests HITL review.
    Returns thread_id and hitl_payload for frontend review.
    """
    logger.info("plan_trip_request", user_id=str(current_user.id))

    result = await trip_orchestrator.start_plan(
        db=db,
        user_id=str(current_user.id),
        user_input=body.user_input,
    )
    return PlanResponse(**result)


@router.post("/hitl", response_model=PlanResponse)
async def hitl_decision(
    body: HITLDecisionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a HITL review decision for a trip plan.
    
    - approve: generates final response
    - request_changes: replans with feedback
    - reject: closes the thread
    """
    decision = HITLDecision(
        thread_id=body.thread_id,
        decision=body.decision,
        feedback=body.feedback,
        change_agents=body.change_agents,
    )

    result = await trip_orchestrator.process_hitl(
        db=db,
        user_id=str(current_user.id),
        decision=decision,
    )
    return PlanResponse(**result)


@router.get("/stream/{thread_id}")
async def stream_thread_updates(
    thread_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    SSE endpoint — stream real-time agent progress updates for a thread.
    Frontend connects here after starting a plan.
    """
    from sqlalchemy import select
    from app.models.thread import Thread

    # Verify thread ownership
    result = await db.execute(
        select(Thread).where(
            Thread.id == thread_id,
            Thread.user_id == str(current_user.id),
        )
    )
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found.")

    async def event_generator() -> AsyncGenerator[str, None]:
        """Poll thread status and emit SSE events."""
        last_status = None
        last_message_count = 0
        polls = 0
        max_polls = 120  # 2 min timeout at 1s intervals

        while polls < max_polls:
            async with db.__class__(db.bind) as poll_db:  # type: ignore[attr-defined]
                from sqlalchemy import select
                from app.models.thread import Thread
                from app.models.message import Message

                t_result = await poll_db.execute(
                    select(Thread).where(Thread.id == thread_id)
                )
                t = t_result.scalar_one_or_none()
                if not t:
                    break

                # Emit status change
                if t.status != last_status:
                    last_status = t.status
                    event = {"type": "status", "status": t.status, "thread_id": thread_id}
                    yield f"data: {json.dumps(event)}\n\n"

                # Emit new messages
                m_result = await poll_db.execute(
                    select(Message)
                    .where(Message.thread_id == thread_id)
                    .order_by(Message.created_at)
                )
                messages = m_result.scalars().all()
                if len(messages) > last_message_count:
                    for msg in messages[last_message_count:]:
                        event = {
                            "type": "message",
                            "role": msg.role,
                            "content": msg.content[:500],
                            "agent_name": msg.agent_name,
                            "created_at": msg.created_at.isoformat(),
                        }
                        yield f"data: {json.dumps(event)}\n\n"
                    last_message_count = len(messages)

                # Terminal states
                if t.status in ("completed", "rejected", "error"):
                    if t.status == "completed" and t.travel_state:
                        state_data = t.travel_state
                        final = state_data.get("final_response")
                        if final:
                            event = {"type": "complete", "final_response": final}
                            yield f"data: {json.dumps(event)}\n\n"
                    yield f"data: {json.dumps({'type': 'end', 'status': t.status})}\n\n"
                    break

                if t.status == "awaiting_hitl":
                    event = {
                        "type": "hitl_required",
                        "thread_id": thread_id,
                        "hitl_status": t.hitl_status,
                    }
                    yield f"data: {json.dumps(event)}\n\n"

            await asyncio.sleep(1)
            polls += 1

        if polls >= max_polls:
            yield f"data: {json.dumps({'type': 'timeout'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

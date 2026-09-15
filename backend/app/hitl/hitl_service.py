"""
HITL (Human-in-the-Loop) Service

Manages the review workflow:
  - When a plan is ready, the thread status is set to 'awaiting_hitl'
  - The frontend polls/subscribes and shows the review card
  - User sends APPROVE / REQUEST_CHANGES / REJECT
  - This service processes the decision and triggers the appropriate next step
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import TravelState
from app.config.settings import settings
from app.config.logging_config import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


class HITLDecision(BaseModel):
    """Payload sent by the user from the review UI."""
    thread_id: str
    decision: str                       # "approve" | "request_changes" | "reject"
    feedback: str = ""                  # Required when decision == "request_changes"
    change_agents: list[str] = []       # Which agents to re-run (auto-detected if empty)


class HITLService:
    """
    Manages the HITL workflow state transitions.
    Works with the thread table to track review state.
    """

    async def request_review(
        self, state: TravelState, db: AsyncSession
    ) -> TravelState:
        """
        Mark a plan as ready for human review.
        Updates thread in DB and returns mutated state.
        """
        from app.models.thread import Thread
        from sqlalchemy import select

        now = datetime.now(timezone.utc)
        state.hitl_status = "pending"

        result = await db.execute(
            select(Thread).where(Thread.id == state.thread_id)
        )
        thread = result.scalar_one_or_none()
        if thread:
            thread.status = "awaiting_hitl"
            thread.hitl_status = "pending"
            thread.hitl_requested_at = now
            thread.travel_state = state.to_db_dict()
            await db.flush()

        logger.info("hitl_review_requested", thread=state.thread_id)
        return state

    async def process_decision(
        self,
        decision: HITLDecision,
        state: TravelState,
        db: AsyncSession,
    ) -> TravelState:
        """
        Process a HITL decision from the user.
        Returns updated state ready for the next pipeline step.
        """
        from app.models.thread import Thread
        from sqlalchemy import select

        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(Thread).where(Thread.id == decision.thread_id)
        )
        thread = result.scalar_one_or_none()

        match decision.decision.lower():
            case "approve":
                state.hitl_status = "approved"
                state.hitl_feedback = None
                if thread:
                    thread.hitl_status = "approved"
                    thread.hitl_resolved_at = now
                logger.info("hitl_approved", thread=decision.thread_id)

            case "request_changes":
                if not decision.feedback:
                    raise ValueError("Feedback is required when requesting changes.")
                state.hitl_status = "changes_requested"
                state.hitl_feedback = decision.feedback

                # Auto-detect which agents to re-run if not specified
                if decision.change_agents:
                    state.hitl_change_agents = decision.change_agents
                else:
                    from app.agents.supervisor_agent import SupervisorAgent
                    supervisor = SupervisorAgent()
                    state.hitl_change_agents = supervisor._determine_change_agents(
                        decision.feedback
                    )

                if thread:
                    thread.hitl_status = "changes_requested"
                    thread.hitl_feedback = decision.feedback
                    thread.hitl_resolved_at = now
                logger.info(
                    "hitl_changes_requested",
                    thread=decision.thread_id,
                    agents=state.hitl_change_agents,
                )

            case "reject":
                state.hitl_status = "rejected"
                state.is_complete = True
                if thread:
                    thread.status = "rejected"
                    thread.hitl_status = "rejected"
                    thread.hitl_resolved_at = now
                logger.info("hitl_rejected", thread=decision.thread_id)

            case _:
                raise ValueError(f"Unknown HITL decision: {decision.decision}")

        if thread:
            thread.travel_state = state.to_db_dict()
            await db.flush()

        return state

    async def wait_for_decision(
        self, thread_id: str, timeout_seconds: int | None = None
    ) -> str | None:
        """
        Async wait for a HITL decision via Redis pub/sub.
        Returns the decision string or None if timed out.

        In production, this integrates with a Redis subscriber.
        For simplicity, this polls the DB (replace with Redis Pub/Sub).
        """
        timeout = timeout_seconds or settings.HITL_TIMEOUT_SECONDS
        logger.info("hitl_waiting", thread=thread_id, timeout=timeout)
        # Redis pub/sub implementation placeholder
        # The route handler returns immediately; polling/WebSocket handles real-time
        return None

    async def get_review_payload(self, state: TravelState) -> dict:
        """
        Build the payload sent to the frontend review card.
        """
        return {
            "thread_id": state.thread_id,
            "hitl_status": state.hitl_status,
            "itinerary_plan": state.itinerary_plan,
            "flight_results": state.flight_results,
            "hotel_results": state.hotel_results,
            "weather_results": state.weather_results,
            "budget_analysis": state.budget_analysis,
            "trip_constraints": state.trip_constraints.model_dump(),
            "supervisor_reasoning": state.supervisor_reasoning,
            "agent_results": [r.model_dump() for r in state.agent_results],
        }


# Singleton
hitl_service = HITLService()

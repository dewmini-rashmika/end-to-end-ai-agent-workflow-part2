"""
Trip Orchestrator — the top-level service that wires together:
  guardrails → supervisor → specialist agents → HITL → final agent

Called by the trip route handler. Manages the full async pipeline
and persists state at each step.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import TravelState
from app.agents.supervisor_agent import SupervisorAgent
from app.agents.final_agent import FinalResponseAgent
from app.guardrails.input_guardrail import input_guardrail
from app.hitl.hitl_service import hitl_service, HITLDecision
from app.services.thread_service import (
    create_thread,
    update_thread_state,
    add_message,
    save_checkpoint,
)
from app.config.logging_config import get_logger

logger = get_logger(__name__)

supervisor = SupervisorAgent()
final_agent = FinalResponseAgent()


class TripOrchestrator:
    """Coordinates the full end-to-end trip planning pipeline."""

    async def start_plan(
        self,
        db: AsyncSession,
        user_id: str,
        user_input: str,
    ) -> dict:
        """
        Entry point: validate input → create thread → run planning pipeline.
        Returns a dict with thread_id and current status.
        """
        # 1. Input guardrail
        guard_result = await input_guardrail.validate(user_input)
        if guard_result.decision == "BLOCK":
            return {
                "status": "blocked",
                "reason": guard_result.reason,
                "risk_level": guard_result.risk_level,
                "thread_id": None,
            }

        clean_input = guard_result.sanitised_input or user_input

        # 2. Create thread
        thread = await create_thread(db, user_id)
        thread_id = str(thread.id)

        # 3. Persist user message
        await add_message(db, thread_id, role="user", content=clean_input)

        # 4. Build initial TravelState
        state = TravelState(
            thread_id=thread_id,
            user_id=user_id,
            user_input=clean_input,
        )

        # 5. Run supervisor + specialist agents
        try:
            state = await supervisor.plan(state)

            # Save checkpoint after planning
            await save_checkpoint(
                db,
                thread_id=thread_id,
                agent_name="supervisor",
                step_number=state.current_step,
                state_snapshot=state.to_db_dict(),
            )

            # Persist planning messages
            if state.supervisor_reasoning:
                await add_message(
                    db, thread_id,
                    role="agent",
                    content=f"Supervisor selected agents: {', '.join(state.selected_agents)}",
                    agent_name="supervisor",
                    metadata={"reasoning": state.supervisor_reasoning},
                )

        except Exception as e:
            logger.error("plan_pipeline_error", thread=thread_id, error=str(e))
            state.hitl_status = "error"
            await update_thread_state(db, thread_id, state, status="error")
            return {
                "status": "error",
                "thread_id": thread_id,
                "message": str(e),
            }

        # 6. Request HITL review
        state = await hitl_service.request_review(state, db)
        await update_thread_state(db, thread_id, state, status="awaiting_hitl")

        return {
            "status": "awaiting_review",
            "thread_id": thread_id,
            "hitl_payload": await hitl_service.get_review_payload(state),
        }

    async def process_hitl(
        self,
        db: AsyncSession,
        user_id: str,
        decision: HITLDecision,
    ) -> dict:
        """
        Process a HITL decision from the user.
        - approve → run FinalResponseAgent
        - request_changes → replan with supervisor.replan()
        - reject → close thread
        """
        from sqlalchemy import select
        from app.models.thread import Thread

        # Load thread + state
        result = await db.execute(
            select(Thread).where(
                Thread.id == decision.thread_id,
                Thread.user_id == user_id,
            )
        )
        thread = result.scalar_one_or_none()
        if not thread:
            return {"status": "error", "message": "Thread not found"}

        state = TravelState.from_db_dict(thread.travel_state or {})
        if not state.thread_id:
            state.thread_id = decision.thread_id
        if not state.user_id:
            state.user_id = user_id

        # Persist HITL feedback message
        if decision.feedback:
            await add_message(
                db, decision.thread_id,
                role="hitl",
                content=decision.feedback,
                metadata={"decision": decision.decision},  # maps to msg_metadata
            )

        # Process the decision
        state = await hitl_service.process_decision(decision, state, db)

        match decision.decision.lower():
            case "approve":
                # Generate final response
                state = await final_agent.generate(state)
                await update_thread_state(db, decision.thread_id, state, status="completed")

                await add_message(
                    db, decision.thread_id,
                    role="assistant",
                    content=state.final_response or "Your travel plan is ready.",
                    agent_name="final_agent",
                )
                return {
                    "status": "completed",
                    "thread_id": decision.thread_id,
                    "final_response": state.final_response,
                }

            case "request_changes":
                # Replan with feedback
                state = await supervisor.replan(state)
                state = await hitl_service.request_review(state, db)
                await update_thread_state(db, decision.thread_id, state, status="awaiting_hitl")

                return {
                    "status": "awaiting_review",
                    "thread_id": decision.thread_id,
                    "hitl_payload": await hitl_service.get_review_payload(state),
                }

            case "reject":
                await update_thread_state(db, decision.thread_id, state, status="rejected")
                return {
                    "status": "rejected",
                    "thread_id": decision.thread_id,
                    "message": "Trip plan rejected. You can start a new plan anytime.",
                }

            case _:
                return {"status": "error", "message": "Unknown decision"}


# Singleton
trip_orchestrator = TripOrchestrator()

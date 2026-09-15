"""
Supervisor Agent — orchestrates the full planning pipeline.

Responsibilities:
  1. Parse user intent → extract TripConstraints
  2. Decide which specialist agents to invoke (dynamic selection)
  3. Run agents sequentially, sharing state between them
  4. Gate on HITL before finalisation
  5. Re-run changed agents if HITL requests modifications
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from app.agents.state import TravelState, TripConstraints
from app.clients.llm_client import supervisor_llm
from app.config.system_prompts import SUPERVISOR_SYSTEM_PROMPT
from app.config.logging_config import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)

# ── Agent registry ────────────────────────────────────────────────────────────
# Lazy imports to avoid circular dependencies
def _get_agent_registry() -> dict:
    from app.agents.flight_agent import FlightAgent
    from app.agents.hotel_agent import HotelAgent
    from app.agents.weather_agent import WeatherAgent
    from app.agents.budget_agent import BudgetAgent
    from app.agents.itinerary_agent import ItineraryAgent

    return {
        "flight_agent": FlightAgent(),
        "hotel_agent": HotelAgent(),
        "weather_agent": WeatherAgent(),
        "budget_agent": BudgetAgent(),
        "itinerary_agent": ItineraryAgent(),
    }


class SupervisorAgent:
    """
    Orchestrates the full multi-agent planning pipeline.
    """

    def __init__(self):
        self.llm = supervisor_llm

    # ── Public entry points ───────────────────────────────────────────────────

    async def plan(self, state: TravelState) -> TravelState:
        """
        Full planning run: supervisor → specialists → state returned for HITL.
        Does NOT produce the final response — that happens after HITL approval.
        """
        logger.info("supervisor_plan_start", thread=state.thread_id)

        # Step 1: Understand intent and select agents
        state = await self._run_supervision(state)

        # Step 2: Run selected specialist agents in order
        registry = _get_agent_registry()
        for agent_name in state.selected_agents:
            if agent_name == "itinerary_agent":
                continue   # itinerary runs last after RAG injection
            agent = registry.get(agent_name)
            if agent:
                state = await agent.run(state)
            else:
                logger.warning("unknown_agent", agent=agent_name)

        # Step 3: Inject RAG context before itinerary
        from app.rag.retriever import inject_rag_context
        state = await inject_rag_context(state)

        # Step 4: Run itinerary agent (synthesis)
        if "itinerary_agent" in state.selected_agents:
            itinerary_agent = registry["itinerary_agent"]
            state = await itinerary_agent.run(state)

        # Mark as awaiting HITL
        state.hitl_status = "pending"
        logger.info("supervisor_plan_complete", thread=state.thread_id)
        return state

    async def replan(self, state: TravelState) -> TravelState:
        """
        Re-run only the agents flagged by HITL for changes.
        Called when hitl_status == 'changes_requested'.
        """
        logger.info(
            "supervisor_replan_start",
            thread=state.thread_id,
            change_agents=state.hitl_change_agents,
        )
        registry = _get_agent_registry()

        # Re-run flagged agents (excluding itinerary — runs last)
        for agent_name in state.hitl_change_agents:
            if agent_name == "itinerary_agent":
                continue
            agent = registry.get(agent_name)
            if agent:
                state = await agent.run(state)

        # Always re-run itinerary to reflect changes
        state = await registry["itinerary_agent"].run(state)
        state.hitl_status = "pending"
        return state

    # ── Private ───────────────────────────────────────────────────────────────

    async def _run_supervision(self, state: TravelState) -> TravelState:
        """Call the supervisor LLM to parse intent and select agents."""
        messages = [
            {"role": "system", "content": SUPERVISOR_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"User travel request: {state.user_input}\n\n"
                    "Analyse this request and return a JSON plan as described in your instructions."
                ),
            },
        ]

        try:
            result = await self.llm.complete_json(messages=messages)
            logger.info("supervisor_decision", result=result)

            # Apply supervisor outputs to state
            state.selected_agents = result.get(
                "selected_agents",
                ["flight_agent", "hotel_agent", "weather_agent", "budget_agent", "itinerary_agent"],
            )
            state.supervisor_reasoning = result.get("reasoning", "")

            # Parse trip constraints
            constraints_data = result.get("trip_constraints", {})
            if constraints_data:
                # Merge parsed constraints with any already-set values
                existing = state.trip_constraints.model_dump()
                merged = {**existing, **{k: v for k, v in constraints_data.items() if v is not None}}
                state.trip_constraints = TripConstraints.model_validate(merged)

                # Calculate duration if dates are available
                if state.trip_constraints.departure_date and state.trip_constraints.return_date:
                    from datetime import date
                    try:
                        dep = date.fromisoformat(state.trip_constraints.departure_date)
                        ret = date.fromisoformat(state.trip_constraints.return_date)
                        state.trip_constraints.duration_days = (ret - dep).days
                    except ValueError:
                        pass

        except Exception as e:
            logger.error("supervisor_llm_error", error=str(e))
            # Fallback: run all agents
            state.selected_agents = [
                "flight_agent", "hotel_agent", "weather_agent",
                "budget_agent", "itinerary_agent",
            ]

        return state

    def _determine_change_agents(self, feedback: str) -> list[str]:
        """
        Heuristic: determine which agents need to re-run based on HITL feedback.
        In production you could use an LLM for this too.
        """
        agents = []
        feedback_lower = feedback.lower()
        if any(w in feedback_lower for w in ["flight", "airline", "fare", "seats"]):
            agents.append("flight_agent")
        if any(w in feedback_lower for w in ["hotel", "accommodation", "room", "stay"]):
            agents.append("hotel_agent")
        if any(w in feedback_lower for w in ["weather", "forecast", "packing", "rain"]):
            agents.append("weather_agent")
        if any(w in feedback_lower for w in ["budget", "cost", "price", "money", "expensive"]):
            agents.append("budget_agent")
        # Always re-run itinerary
        agents.append("itinerary_agent")
        return list(dict.fromkeys(agents))  # deduplicate preserving order

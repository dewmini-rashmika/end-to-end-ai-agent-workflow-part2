"""
Final Response Agent — composes the polished, user-facing travel plan
after HITL approval. Produces rich markdown output.
"""
import json

from app.agents.state import TravelState
from app.clients.llm_client import final_llm
from app.config.system_prompts import FINAL_RESPONSE_AGENT_SYSTEM_PROMPT
from app.config.logging_config import get_logger

logger = get_logger(__name__)


class FinalResponseAgent:
    """
    Takes all approved agent outputs and generates the final travel plan.
    Does not inherit BaseAgent as it doesn't use tool-calling.
    """

    def __init__(self):
        self.llm = final_llm

    async def generate(self, state: TravelState) -> TravelState:
        """Generate the final formatted travel plan and store in state."""
        logger.info("final_agent_start", thread=state.thread_id)

        try:
            messages = [
                {"role": "system", "content": FINAL_RESPONSE_AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": self._build_prompt(state)},
            ]

            response = await self.llm.complete(
                messages=messages,
                temperature=0.4,
                max_tokens=6000,
            )

            state.final_response = response.content
            state.is_complete = True
            state.hitl_status = "approved"

            state.update_agent_result(
                "final_agent",
                status="completed",
                output={"final_response": response.content[:500] + "..."},
                model_used=response.model,
                prompt_tokens=response.prompt_tokens,
                completion_tokens=response.completion_tokens,
            )

            logger.info(
                "final_agent_complete",
                thread=state.thread_id,
                tokens=response.total_tokens,
            )

        except Exception as e:
            logger.error("final_agent_error", error=str(e))
            state.update_agent_result("final_agent", status="failed", error=str(e))

        return state

    def _build_prompt(self, state: TravelState) -> str:
        tc = state.trip_constraints
        parts = [
            f"## Original Request\n{state.user_input}",
            f"## Trip Overview\n"
            f"- From: {tc.origin} → {tc.destination}\n"
            f"- Dates: {tc.departure_date} – {tc.return_date} ({tc.duration_days} days)\n"
            f"- Travellers: {tc.travelers}\n"
            f"- Budget: {f'${tc.budget_usd} USD ({tc.budget_level})' if tc.budget_usd else tc.budget_level}",
        ]

        if state.flight_results:
            flights = state.flight_results.get("flights", [])
            if flights:
                best = flights[0]
                parts.append(
                    f"## Selected Flight\n"
                    f"- {best.get('airline')} {best.get('flight_number')} — "
                    f"${best.get('total_price_usd')} total\n"
                    f"- Departs {best.get('departure_time')} → Arrives {best.get('arrival_time')}\n"
                    f"- {best.get('stops', 0)} stops, {best.get('duration_minutes', 0)} min"
                )

        if state.hotel_results:
            hotels = state.hotel_results.get("hotels", [])
            if hotels:
                best = hotels[0]
                parts.append(
                    f"## Selected Accommodation\n"
                    f"- {best.get('name')} ({'⭐' * best.get('star_rating', 4)})\n"
                    f"- ${best.get('price_per_night_usd')}/night — ${best.get('total_price_usd')} total\n"
                    f"- {'Free cancellation ✓' if best.get('free_cancellation') else 'Check cancellation policy'}"
                )

        if state.weather_results:
            parts.append(
                f"## Weather & Packing\n"
                f"```json\n{json.dumps(state.weather_results.get('daily_forecast', [])[:3], indent=2)}\n```\n"
                f"**Packing:** {', '.join(state.weather_results.get('packing_suggestions', [])[:8])}"
            )

        if state.budget_analysis:
            ba = state.budget_analysis
            parts.append(
                f"## Budget Summary\n"
                f"- Total estimated: ${ba.get('total_estimated_usd', 'N/A')}\n"
                f"- Status: {ba.get('budget_status', 'N/A')}\n"
                f"- Per person: ${ba.get('cost_per_person_usd', 'N/A')}"
            )

        if state.itinerary_plan:
            parts.append(
                f"## Day-by-Day Itinerary\n"
                f"```json\n{json.dumps(state.itinerary_plan, indent=2)}\n```"
            )

        if state.hitl_feedback:
            parts.append(
                f"## Applied User Modifications\n{state.hitl_feedback}"
            )

        parts.append(
            "\n\nNow generate a beautifully formatted, complete travel plan in markdown. "
            "Be thorough, practical, and engaging. Use the exact data provided above."
        )

        return "\n\n".join(parts)

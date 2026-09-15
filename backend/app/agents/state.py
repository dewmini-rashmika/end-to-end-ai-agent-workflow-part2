"""
TravelState — the shared context object passed between all agents.
Pydantic model so it serialises cleanly to/from JSONB in PostgreSQL.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class TripConstraints(BaseModel):
    """Extracted trip parameters from the user's request."""
    origin: Optional[str] = None
    origin_iata: Optional[str] = None
    destination: Optional[str] = None
    destination_iata: Optional[str] = None
    departure_date: Optional[str] = None          # YYYY-MM-DD
    return_date: Optional[str] = None             # YYYY-MM-DD
    duration_days: Optional[int] = None
    travelers: int = 1
    budget_usd: Optional[float] = None
    budget_level: str = "mid"                     # budget | mid | luxury
    interests: list[str] = Field(default_factory=list)
    accommodation_type: str = "hotel"
    cabin_class: str = "economy"
    special_requirements: Optional[str] = None


class AgentResult(BaseModel):
    """Result from a single specialist agent run."""
    agent_name: str
    status: str = "pending"                       # pending | running | completed | failed
    output: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    model_used: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0


class TravelState(BaseModel):
    """
    Full shared state passed between all agents in a planning session.
    Stored as JSONB in the threads.travel_state column.
    """
    thread_id: str
    user_id: str
    user_input: str                               # original raw user request

    # Supervisor outputs
    selected_agents: list[str] = Field(default_factory=list)
    trip_constraints: TripConstraints = Field(default_factory=TripConstraints)
    supervisor_reasoning: Optional[str] = None

    # Per-agent results (keyed by agent name)
    flight_results: Optional[dict[str, Any]] = None
    hotel_results: Optional[dict[str, Any]] = None
    weather_results: Optional[dict[str, Any]] = None
    budget_analysis: Optional[dict[str, Any]] = None
    itinerary_plan: Optional[dict[str, Any]] = None

    # RAG context injected before itinerary planning
    rag_context: Optional[str] = None

    # Agent execution tracking
    agent_results: list[AgentResult] = Field(default_factory=list)
    current_step: int = 0

    # HITL
    hitl_status: Optional[str] = None            # pending | approved | changes_requested | rejected
    hitl_feedback: Optional[str] = None
    hitl_change_agents: list[str] = Field(default_factory=list)  # agents to re-run

    # Final output
    final_response: Optional[str] = None
    is_complete: bool = False

    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    def update_agent_result(
        self,
        agent_name: str,
        status: str,
        output: dict | None = None,
        error: str | None = None,
        model_used: str | None = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ) -> None:
        """Upsert an agent result entry."""
        now = datetime.utcnow().isoformat()
        for r in self.agent_results:
            if r.agent_name == agent_name:
                r.status = status
                r.output = output
                r.error = error
                r.model_used = model_used
                r.prompt_tokens = prompt_tokens
                r.completion_tokens = completion_tokens
                r.completed_at = now
                self.updated_at = now
                return
        # New entry
        self.agent_results.append(
            AgentResult(
                agent_name=agent_name,
                status=status,
                output=output,
                error=error,
                started_at=now,
                completed_at=now if status != "running" else None,
                model_used=model_used,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
        )
        self.updated_at = now

    def to_db_dict(self) -> dict:
        return self.model_dump(mode="json")

    @classmethod
    def from_db_dict(cls, data: dict) -> "TravelState":
        return cls.model_validate(data)

"""
Pydantic request/response schemas for all API routes.
Separated from DB models to keep API contracts stable.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_\-]+$")
    password: str = Field(min_length=8, max_length=128)
    full_name: Optional[str] = Field(default=None, max_length=256)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int   # seconds


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=256)
    avatar_url: Optional[str] = Field(default=None, max_length=512)


# ── Trip / Planning ───────────────────────────────────────────────────────────

class PlanTripRequest(BaseModel):
    user_input: str = Field(
        min_length=10,
        max_length=2000,
        description="Natural language trip description",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_input": "Plan a 5-day trip from London to Dubai in October 2026 for 2 people with a mid-range budget. We love food and beaches."
            }
        }
    }


class HITLDecisionRequest(BaseModel):
    thread_id: str
    decision: str = Field(pattern=r"^(approve|request_changes|reject)$")
    feedback: str = Field(default="", max_length=2000)
    change_agents: list[str] = Field(default_factory=list)


class AgentResultSchema(BaseModel):
    agent_name: str
    status: str
    error: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    model_used: Optional[str] = None


class PlanResponse(BaseModel):
    status: str
    thread_id: Optional[str] = None
    reason: Optional[str] = None           # if blocked
    risk_level: Optional[str] = None       # if blocked
    hitl_payload: Optional[dict[str, Any]] = None
    final_response: Optional[str] = None
    message: Optional[str] = None


# ── Thread / History ──────────────────────────────────────────────────────────

class ThreadSummary(BaseModel):
    id: uuid.UUID
    title: Optional[str]
    status: str
    hitl_status: Optional[str]
    created_at: datetime
    updated_at: datetime
    destination: Optional[str] = None
    departure_date: Optional[str] = None

    model_config = {"from_attributes": True}


class MessageSchema(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    agent_name: Optional[str]
    created_at: datetime
    msg_metadata: Optional[dict[str, Any]] = Field(default=None, alias="msg_metadata")
    model_used: Optional[str] = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class ThreadDetailResponse(BaseModel):
    id: uuid.UUID
    title: Optional[str]
    status: str
    hitl_status: Optional[str]
    hitl_feedback: Optional[str]
    travel_state: Optional[dict[str, Any]]
    messages: list[MessageSchema]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ThreadListResponse(BaseModel):
    threads: list[ThreadSummary]
    total: int
    page: int
    page_size: int


# ── RAG ───────────────────────────────────────────────────────────────────────

class IngestDocumentRequest(BaseModel):
    content: str = Field(min_length=10)
    destination: str
    source: str = "manual"
    doc_id: Optional[str] = None


class RAGQueryRequest(BaseModel):
    query: str = Field(min_length=3)
    destination: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=20)

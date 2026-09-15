"""
Input Guardrail Service
Validates and sanitises user input before it reaches any agent.

Pipeline:
  1. Keyword / pattern check (fast, no LLM)
  2. LLM-based safety & relevance classification
  3. Return GuardrailResult with PASS/BLOCK decision
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from app.clients.llm_client import guardrail_llm
from app.config.settings import settings
from app.config.system_prompts import GUARDRAIL_SYSTEM_PROMPT
from app.config.logging_config import get_logger

logger = get_logger(__name__)


class GuardrailResult(BaseModel):
    decision: str                           # "PASS" | "BLOCK"
    reason: str
    risk_level: str = "none"               # none | low | medium | high
    sanitised_input: Optional[str] = None
    blocked_by: str = "llm"               # "keyword" | "llm"


def _load_blocked_patterns() -> list[str]:
    """Load blocked keyword patterns from config file."""
    try:
        path = Path(settings.BLOCKED_KEYWORDS_FILE)
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return [p.lower() for p in data.get("blocked_patterns", [])]
    except Exception as e:
        logger.warning("blocked_keywords_load_error", error=str(e))
    return []


_BLOCKED_PATTERNS: list[str] = _load_blocked_patterns()


def _keyword_check(user_input: str) -> GuardrailResult | None:
    """
    Fast pre-check against known blocked patterns.
    Returns a BLOCK result if matched, else None (proceed to LLM check).
    """
    lowered = user_input.lower()
    for pattern in _BLOCKED_PATTERNS:
        if pattern in lowered:
            return GuardrailResult(
                decision="BLOCK",
                reason=f"Input contains a blocked pattern. Please rephrase your travel request.",
                risk_level="high",
                sanitised_input=None,
                blocked_by="keyword",
            )
    return None


def _sanitise(text: str) -> str:
    """Basic input sanitisation: strip excessive whitespace, truncate."""
    text = re.sub(r"\s+", " ", text).strip()
    return text[:2000]  # Prevent prompt injection via very long inputs


class InputGuardrailService:
    """
    Validates user input before it enters the agent pipeline.
    """

    async def validate(self, user_input: str) -> GuardrailResult:
        """
        Run full validation pipeline on user input.

        Returns GuardrailResult with decision PASS or BLOCK.
        """
        if not user_input or not user_input.strip():
            return GuardrailResult(
                decision="BLOCK",
                reason="Empty input — please describe your travel plans.",
                risk_level="none",
                blocked_by="keyword",
            )

        sanitised = _sanitise(user_input)

        # Stage 1: fast keyword check
        keyword_result = _keyword_check(sanitised)
        if keyword_result:
            logger.warning(
                "guardrail_keyword_block",
                pattern_matched=True,
                input_preview=sanitised[:80],
            )
            return keyword_result

        # Stage 2: LLM classification
        messages = [
            {"role": "system", "content": GUARDRAIL_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Evaluate this user input:\n\n{sanitised}",
            },
        ]

        try:
            result = await guardrail_llm.complete_json(
                messages=messages, temperature=0.1
            )
            decision = result.get("decision", "BLOCK").upper()
            reason = result.get("reason", "Unable to validate input.")
            risk = result.get("risk_level", "medium")
            clean = result.get("sanitised_input", sanitised if decision == "PASS" else None)

            llm_result = GuardrailResult(
                decision=decision,
                reason=reason,
                risk_level=risk,
                sanitised_input=clean,
                blocked_by="llm",
            )

            log_fn = logger.info if decision == "PASS" else logger.warning
            log_fn(
                "guardrail_result",
                decision=decision,
                risk=risk,
                input_preview=sanitised[:80],
            )
            return llm_result

        except Exception as e:
            logger.error("guardrail_llm_error", error=str(e))
            # Fail open with a warning — don't block valid travel requests
            # due to LLM failures; log for monitoring
            return GuardrailResult(
                decision="PASS",
                reason="Guardrail LLM unavailable — input passed with warning.",
                risk_level="low",
                sanitised_input=sanitised,
                blocked_by="llm",
            )

    async def validate_batch(self, inputs: list[str]) -> list[GuardrailResult]:
        """Validate multiple inputs concurrently."""
        import asyncio
        return await asyncio.gather(*[self.validate(inp) for inp in inputs])


# Singleton
input_guardrail = InputGuardrailService()

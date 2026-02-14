# app/services/ai_service.py
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings


GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent"

# Reasonable safety net for external calls
DEFAULT_TIMEOUT_SECONDS = 15.0


class AIService:
    """
    Isolated service for Google Gemini integration.

    - No database or FastAPI dependencies
    - All methods are async and safe to call from background tasks or routes
    - Never raises for expected network / API problems; returns fallback JSON instead
    """

    def __init__(self, api_key: Optional[str] = None, timeout: float = DEFAULT_TIMEOUT_SECONDS):
        self.api_key = api_key or settings.gemini_api_key
        self.timeout = timeout

    # ---------- Public API ----------

    async def analyze_operational_risk(
        self,
        *,
        unanswered_count: int,
        unanswered_threshold: int,
        no_show_rate: float,
        no_show_threshold: float,
        pending_forms: int,
        pending_forms_threshold: int,
        low_stock_items: List[Dict[str, Any]],
        booking_trends: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        High-level risk assessment over core operational signals.
        """
        prompt = self._build_operational_risk_prompt(
            unanswered_count=unanswered_count,
            unanswered_threshold=unanswered_threshold,
            no_show_rate=no_show_rate,
            no_show_threshold=no_show_threshold,
            pending_forms=pending_forms,
            pending_forms_threshold=pending_forms_threshold,
            low_stock_items=low_stock_items,
            booking_trends=booking_trends,
        )

        schema_hint = {
            "type": "object",
            "properties": {
                "overall_risk_level": {"type": "string"},  # low | medium | high | critical
                "summary": {"type": "string"},
                "risks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "area": {"type": "string"},
                            "severity": {"type": "string"},
                            "reason": {"type": "string"},
                            "metric": {"type": "string"},
                            "value": {},
                            "threshold": {},
                        },
                    },
                },
                "recommendations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "area": {"type": "string"},
                            "action": {"type": "string"},
                            "priority": {"type": "string"},
                        },
                    },
                },
            },
        }

        return await self._call_gemini_json(
            prompt=prompt,
            schema_hint=schema_hint,
            fallback={
                "ok": False,
                "overall_risk_level": "unknown",
                "summary": "AI analysis unavailable; show basic metrics only.",
                "risks": [],
                "recommendations": [],
            },
        )

    # ---------- Internal helpers: Gemini HTTP wrapper ----------

    logger = logging.getLogger(__name__)

    async def _call_gemini_json(
        self,
        *,
        prompt: str,
        schema_hint: Optional[Dict[str, Any]],
        fallback: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Low-level call to Gemini that:
        - uses async HTTP with timeout
        - asks for JSON
        - returns parsed dict or a safe fallback
        """
        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}

        body: Dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
        }

        # --- LOG: before request ---
        logger.info("Sending prompt to Gemini:\n%s", prompt)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    GEMINI_ENDPOINT,
                    headers=headers,
                    params=params,
                    json=body,
                )
                resp.raise_for_status()
                data = resp.json()

            # --- LOG: raw response ---
            logger.info("Gemini raw response: %s", json.dumps(data, indent=2))

        except (httpx.RequestError, httpx.HTTPStatusError, asyncio.TimeoutError) as e:
            fb = dict(fallback)
            fb.setdefault("ok", False)
            fb.setdefault("error", f"ai_request_failed: {str(e)}")
            logger.error("Gemini request failed: %s", str(e))
            return fb

        # --- LOG: trying to extract text ---
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            logger.info("Gemini extracted text:\n%s", text)
        except (KeyError, IndexError, TypeError) as e:
            fb = dict(fallback)
            fb.setdefault("ok", False)
            fb.setdefault("error", "ai_response_unexpected")
            logger.error("Failed to extract text from Gemini response: %s", str(e))
            return fb

        # --- LOG: attempting JSON parse ---
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                parsed.setdefault("ok", True)
                logger.info("Gemini parsed JSON successfully: %s", parsed)
                return parsed
        except json.JSONDecodeError as e:
            logger.warning("Gemini response not JSON: %s", str(e))

        fb = dict(fallback)
        fb.setdefault("ok", False)
        fb.setdefault("error", "ai_response_not_json")
        fb.setdefault("raw_text", text)
        logger.warning("Returning fallback with raw_text: %s", text)
        return fb

    # ---------- Internal helpers: prompt builders ----------

    def _build_operational_risk_prompt(self, **metrics: Any) -> str:
        return (
            "You are an operations consultant for a service business SaaS.\n"
            "You will receive JSON metrics and must return a JSON object describing "
            "operational risk.\n\n"
            "Metrics JSON:\n"
            f"{json.dumps(metrics, indent=2)}\n\n"
            "Evaluate:\n"
            "- Unanswered messages\n"
            "- No-show rate\n"
            "- Pending forms\n"
            "- Inventory risk (low_stock_items)\n"
            "- Booking trends\n\n"
            "Respond ONLY with JSON, matching the provided schema (overall_risk_level, "
            "summary, risks, recommendations)."
        )

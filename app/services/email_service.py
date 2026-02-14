# app/services/email_service.py
from __future__ import annotations

from typing import Any, Dict, Optional, Sequence

import httpx
from loguru import logger  # or stdlib logging if you prefer

from app.core.config import settings


class EmailService:
    """
    Thin, isolated wrapper around Resend's email API.

    - Synchronous, safe to call from background tasks or request handlers
    - NEVER raises on network / API failures for normal callers
    - Returns structured result: {ok, message_id, error}
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.resend.com",
        timeout_seconds: float = 10.0,
    ) -> None:
        self.api_key = api_key or settings.resend_api_key
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def send_email(
        self,
        *,
        from_email: str,
        to: Sequence[str] | str,
        subject: str,
        html: Optional[str] = None,
        text: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Send an email via Resend.

        Returns:
        {
          "ok": bool,
          "message_id": Optional[str],
          "error": Optional[str],
          "status_code": Optional[int],
        }
        """
        if isinstance(to, str):
            to_list = [to]
        else:
            to_list = list(to)

        body: Dict[str, Any] = {
            "from": from_email,
            "to": to_list,
            "subject": subject,
        }
        if html:
            body["html"] = html
        if text:
            body["text"] = text
        if tags:
            # Resend supports 'tags' as a list of {name, value}
            body["tags"] = [
                {"name": k, "value": v} for k, v in tags.items()
            ]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}/emails"

        try:
            resp = httpx.post(
                url,
                json=body,
                headers=headers,
                timeout=self.timeout_seconds,
            )
        except httpx.RequestError as exc:
            logger.error(f"Resend request error: {exc}")
            return {
                "ok": False,
                "message_id": None,
                "error": "network_error",
                "status_code": None,
            }

        if resp.status_code >= 400:
            logger.error(
                "Resend email failed",
                extra={"status_code": resp.status_code, "body": resp.text},
            )
            error_code = "resend_http_error"
            try:
                data = resp.json()
                error_code = data.get("error", {}).get("type", error_code)
            except Exception:  # noqa: BLE001
                pass

            return {
                "ok": False,
                "message_id": None,
                "error": error_code,
                "status_code": resp.status_code,
            }

        try:
            data = resp.json()
            message_id = data.get("id") or data.get("message_id")
        except Exception:  # noqa: BLE001
            logger.warning("Resend response not JSON-decoding cleanly")
            return {
                "ok": True,
                "message_id": None,
                "error": None,
                "status_code": resp.status_code,
            }

        return {
            "ok": True,
            "message_id": message_id,
            "error": None,
            "status_code": resp.status_code,
        }
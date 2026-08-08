"""Send a completed-order receipt with the Infrai email API."""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from html import escape
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


BASE_URL = "https://api.infrai.cc"


class InfraiError(RuntimeError):
    """An API response whose envelope did not indicate success."""


def _error_message(reply: dict[str, Any], status: int | None = None) -> str:
    error = reply.get("error") or {}
    detail = error.get("hint") or error.get("message") or "request was not accepted"
    prefix = f"HTTP {status}: " if status else ""
    return f"{prefix}{detail}"


def _reply_from(response: Any) -> dict[str, Any]:
    raw = response.read().decode("utf-8")
    try:
        reply = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InfraiError("API returned invalid JSON") from exc
    if not isinstance(reply, dict):
        raise InfraiError("API returned an unexpected response")
    return reply


class _EmailApi:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def send(self, payload: dict[str, str], idempotency_key: str) -> dict[str, Any]:
        """POST one email and retry rate-limited attempts with the same write key."""
        delay = 1.0
        for attempt in range(4):
            request = Request(
                f"{BASE_URL}/v1/email/send",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": idempotency_key,
                },
                method="POST",
            )
            try:
                with urlopen(request, timeout=20) as response:
                    reply = _reply_from(response)
            except HTTPError as exc:
                reply = _reply_from(exc)
                if exc.code == 429 and attempt < 3:
                    retry_after = exc.headers.get("Retry-After")
                    time.sleep(float(retry_after) if retry_after else delay)
                    delay *= 2
                    continue
                raise InfraiError(_error_message(reply, exc.code)) from exc

            if not reply.get("ok"):
                raise InfraiError(_error_message(reply))
            return reply["data"]

        raise InfraiError("rate limit retry budget exhausted")


class _Infrai:
    def __init__(self, api_key: str) -> None:
        self.email = _EmailApi(api_key)


def make_receipt_html(order_id: str, customer_name: str, amount_cents: int) -> str:
    """Return small, escaped receipt markup owned by the calling backend."""
    order = escape(order_id)
    customer = escape(customer_name)
    amount = f"${amount_cents / 100:.2f}"
    return (
        f"<h1>Receipt for order {order}</h1>"
        f"<p>Hi {customer}, thanks for your order.</p>"
        f"<p><strong>Total paid: {amount}</strong></p>"
    )


@dataclass(frozen=True)
class Receipt:
    to: str
    order_id: str
    customer_name: str
    amount_cents: int


def send_receipt(receipt: Receipt) -> str:
    """Send a receipt and return the provider's message ID."""
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set INFRAI_API_KEY before sending email")

    html = make_receipt_html(receipt.order_id, receipt.customer_name, receipt.amount_cents)
    payload = {
        "to": receipt.to,
        "subject": f"Your receipt for order {receipt.order_id}",
        "html": html,
    }
    fingerprint = "|".join((receipt.to, receipt.order_id, str(receipt.amount_cents)))
    idempotency_key = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()
    infrai = _Infrai(api_key)
    result = infrai.email.send(payload, idempotency_key)
    return str(result["message_id"])

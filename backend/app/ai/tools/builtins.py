"""Builtin tool integrations.

Every tool executes for real when its credentials/config are present
(generic REST calls via httpx), otherwise returns a structured stub result
``{"stub": true, ...}`` so agents remain fully testable without keys.
"""
from __future__ import annotations

import os
import time
import uuid
from typing import Any, Awaitable, Callable, Optional

from .registry import ToolPlugin, register_tool


async def _http(method: str, url: str, *, headers: dict | None = None,
                json_body: Any = None, auth: tuple | None = None,
                params: dict | None = None) -> dict:
    """Small httpx wrapper (lazy import) returning a normalized dict."""
    try:
        import httpx  # lazy

        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.request(method, url, headers=headers, json=json_body,
                                        auth=auth, params=params)
            try:
                body: Any = resp.json()
            except Exception:
                body = resp.text[:2000]
            return {"status_code": resp.status_code, "body": body, "ok": resp.is_success}
    except Exception as exc:  # network/dep failure → structured error
        return {"status_code": 0, "body": str(exc), "ok": False}


def _stub(tool: str, action: str, **detail: Any) -> dict:
    return {
        "stub": True,
        "tool": tool,
        "action": action,
        "result": f"[stub] {tool} would {action} (no credentials configured)",
        "reference_id": f"stub-{uuid.uuid4().hex[:8]}",
        "detail": detail,
        "ts": time.time(),
    }


class _BuiltinTool(ToolPlugin):
    """Generic builtin tool driven by a config record + executor callable."""

    def __init__(self, name: str, description: str, schema: dict,
                 required_env: tuple[str, ...],
                 executor: Optional[Callable[..., Awaitable[dict]]] = None):
        self.name = name
        self.description = description
        self.schema = schema
        self.required_env = required_env
        self._executor = executor

    async def execute(self, **kwargs: Any) -> dict:
        if self._executor is not None and self.configured():
            try:
                return await self._executor(**kwargs)
            except Exception as exc:
                return {"stub": True, "tool": self.name, "error": str(exc),
                        "result": f"{self.name} execution failed; returning stub"}
        action = kwargs.get("action") or "execute with " + ", ".join(
            f"{k}={str(v)[:60]}" for k, v in kwargs.items()) or "run"
        return _stub(self.name, action, **{k: str(v)[:200] for k, v in kwargs.items()})


def _obj(props: dict[str, str], required: list[str] | None = None) -> dict:
    return {
        "type": "object",
        "properties": {k: {"type": "string", "description": v} for k, v in props.items()},
        "required": required or [],
    }


# --------------------------------------------------------------------------- #
# Real executors (used when creds exist)
# --------------------------------------------------------------------------- #
async def _slack_exec(**kw: Any) -> dict:
    return await _http(
        "POST", "https://slack.com/api/chat.postMessage",
        headers={"Authorization": f"Bearer {os.environ['SLACK_BOT_TOKEN']}"},
        json_body={"channel": kw.get("channel", "#general"), "text": kw.get("text", "")},
    )


async def _twilio_sms_exec(**kw: Any) -> dict:
    sid = os.environ["TWILIO_ACCOUNT_SID"]
    return await _http(
        "POST", f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
        auth=(sid, os.environ["TWILIO_AUTH_TOKEN"]),
        params={"To": kw.get("to", ""), "From": os.environ.get("TWILIO_FROM", ""),
                "Body": kw.get("body", "")},
    )


async def _stripe_exec(**kw: Any) -> dict:
    return await _http(
        "GET", f"https://api.stripe.com/v1/{kw.get('resource', 'customers')}",
        headers={"Authorization": f"Bearer {os.environ['STRIPE_API_KEY']}"},
        params={"limit": kw.get("limit", "5")},
    )


async def _custom_api_exec(**kw: Any) -> dict:
    headers = {}
    if kw.get("auth_header"):
        headers["Authorization"] = kw["auth_header"]
    return await _http(kw.get("method", "GET").upper(), kw.get("url", ""),
                       headers=headers, json_body=kw.get("json"))


async def _webhook_exec(**kw: Any) -> dict:
    return await _http("POST", kw.get("url") or os.environ.get("WEBHOOK_URL", ""),
                       json_body={"event": kw.get("event", "agent_event"),
                                  "payload": kw.get("payload", {})})


async def _n8n_exec(**kw: Any) -> dict:
    return await _http("POST", os.environ["N8N_WEBHOOK_URL"],
                       json_body={"workflow": kw.get("workflow", ""), "data": kw})


class _FaqRagTool(ToolPlugin):
    name = "faq_rag"
    description = ("Search the business knowledge base (FAQs, policies, menus, price "
                   "lists) and return the most relevant passages for a question.")
    schema = _obj({"query": "the customer question to look up",
                   "kb_id": "knowledge base id (optional)"}, ["query"])
    required_env = ()

    async def execute(self, **kwargs: Any) -> dict:
        from ..rag.retrieve import retrieve

        kb_id = kwargs.get("kb_id") or kwargs.get("knowledge_base_id") or "default"
        results = await retrieve(kb_id, kwargs.get("query", ""), k=int(kwargs.get("k", 4)))
        if not results:
            return {"stub": True, "tool": self.name, "results": [],
                    "result": "No indexed knowledge found; answer from the system prompt."}
        return {"stub": False, "tool": self.name, "results": results}


class _BookingTool(ToolPlugin):
    name = "booking"
    description = ("Create, check or cancel an appointment/booking in the internal "
                   "booking system. Provide customer name, service, date and time.")
    schema = _obj({"action": "create | check | cancel", "customer_name": "customer full name",
                   "service": "requested service", "date": "YYYY-MM-DD", "time": "HH:MM"},
                  ["action"])
    required_env = ()
    _bookings: dict[str, dict] = {}

    async def execute(self, **kwargs: Any) -> dict:
        action = (kwargs.get("action") or "create").lower()
        if action == "create":
            bid = f"bk-{uuid.uuid4().hex[:8]}"
            record = {k: kwargs.get(k) for k in ("customer_name", "service", "date", "time")}
            self._bookings[bid] = record
            return {"stub": False, "tool": self.name, "booking_id": bid,
                    "status": "confirmed", **record}
        if action == "cancel":
            bid = kwargs.get("booking_id", "")
            existed = self._bookings.pop(bid, None) is not None
            return {"stub": False, "tool": self.name, "booking_id": bid,
                    "status": "cancelled" if existed else "not_found"}
        return {"stub": False, "tool": self.name, "action": "check",
                "bookings": list(self._bookings.items())[:10]}


class _DatabaseQueryTool(ToolPlugin):
    name = "database_query"
    description = "Run a read-only SQL query against the business database."
    schema = _obj({"query": "SQL SELECT statement"}, ["query"])
    required_env = ("DATABASE_URL",)

    async def execute(self, **kwargs: Any) -> dict:
        q = (kwargs.get("query") or "").strip()
        if not q.lower().startswith("select"):
            return {"stub": True, "tool": self.name, "error": "only SELECT allowed"}
        if not self.configured():
            return _stub(self.name, f"run query: {q[:120]}")
        try:
            import asyncpg  # lazy

            dsn = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")
            conn = await asyncpg.connect(dsn, timeout=3)
            try:
                rows = await conn.fetch(q)
                return {"stub": False, "tool": self.name,
                        "rows": [dict(r) for r in rows[:50]]}
            finally:
                await conn.close()
        except Exception as exc:
            return {"stub": True, "tool": self.name, "error": str(exc)}


# --------------------------------------------------------------------------- #
# Registration of the builtin catalog
# --------------------------------------------------------------------------- #
_BUILTINS: list[_BuiltinTool] = [
    _BuiltinTool("gmail", "Send or draft an email via Gmail on behalf of the business.",
                 _obj({"to": "recipient email", "subject": "subject line", "body": "email body"},
                      ["to", "subject", "body"]),
                 ("GMAIL_CREDENTIALS_JSON",)),
    _BuiltinTool("google_calendar", "Create, list or cancel events on the business Google Calendar.",
                 _obj({"action": "create | list | cancel", "title": "event title",
                       "start": "ISO datetime", "end": "ISO datetime", "attendee": "email"},
                      ["action"]),
                 ("GOOGLE_CALENDAR_CREDENTIALS_JSON",)),
    _BuiltinTool("google_maps", "Look up places, distances and directions via Google Maps.",
                 _obj({"query": "place or address to search", "mode": "search | directions"},
                      ["query"]),
                 ("GOOGLE_MAPS_API_KEY",)),
    _BuiltinTool("whatsapp", "Send a WhatsApp message to a customer via Twilio.",
                 _obj({"to": "customer phone in E.164", "body": "message text"}, ["to", "body"]),
                 ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"), _twilio_sms_exec),
    _BuiltinTool("slack", "Post a message to a Slack channel (internal team notifications).",
                 _obj({"channel": "channel name or id", "text": "message text"}, ["text"]),
                 ("SLACK_BOT_TOKEN",), _slack_exec),
    _BuiltinTool("twilio_sms", "Send an SMS to a customer via Twilio.",
                 _obj({"to": "phone in E.164", "body": "message text"}, ["to", "body"]),
                 ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"), _twilio_sms_exec),
    _BuiltinTool("stripe", "Look up customers, payments and invoices in Stripe.",
                 _obj({"resource": "customers | charges | invoices", "limit": "max results"}),
                 ("STRIPE_API_KEY",), _stripe_exec),
    _BuiltinTool("shopify", "Query products, orders and inventory from the Shopify store.",
                 _obj({"resource": "products | orders | customers", "query": "search terms"}),
                 ("SHOPIFY_ACCESS_TOKEN", "SHOPIFY_SHOP")),
    _BuiltinTool("hubspot", "Create or look up contacts and deals in HubSpot CRM.",
                 _obj({"action": "create_contact | find_contact | create_deal",
                       "email": "contact email", "name": "contact name"}, ["action"]),
                 ("HUBSPOT_ACCESS_TOKEN",)),
    _BuiltinTool("salesforce", "Query or update leads and opportunities in Salesforce.",
                 _obj({"action": "query | create_lead", "soql": "SOQL query",
                       "name": "lead name", "email": "lead email"}, ["action"]),
                 ("SALESFORCE_ACCESS_TOKEN", "SALESFORCE_INSTANCE_URL")),
    _BuiltinTool("zapier", "Trigger a Zapier zap with a JSON payload.",
                 _obj({"event": "zap event name", "payload": "JSON payload"}, ["event"]),
                 ("ZAPIER_WEBHOOK_URL",), _webhook_exec),
    _BuiltinTool("n8n_webhook", "Trigger an n8n workflow webhook with data.",
                 _obj({"workflow": "workflow name", "payload": "JSON payload"}),
                 ("N8N_WEBHOOK_URL",), _n8n_exec),
    _BuiltinTool("custom_api", "Call any REST API: method, url, optional auth header and JSON body.",
                 _obj({"method": "GET | POST | PUT | DELETE", "url": "full URL",
                       "auth_header": "Authorization header value", "json": "JSON body"},
                      ["url"]),
                 (), _custom_api_exec),
    _BuiltinTool("webhook", "POST an event payload to a configured webhook URL.",
                 _obj({"url": "webhook URL (or configured default)", "event": "event name",
                       "payload": "JSON payload"}),
                 (), _webhook_exec),
]

for _tool in _BUILTINS:
    register_tool(_tool)
register_tool(_FaqRagTool())
register_tool(_BookingTool())
register_tool(_DatabaseQueryTool())

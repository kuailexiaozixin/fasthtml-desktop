from __future__ import annotations
import base64, hashlib, hmac, json, os, time

_seen: dict[str, int] = {}

def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))

def verify_suite_ticket(ticket: str) -> dict | None:
    secret = os.getenv("FASTOFFICE_SSO_SECRET", "")
    if not secret or "." not in ticket:
        return None
    raw, signature = ticket.rsplit(".", 1)
    expected = hmac.new(secret.encode(), raw.encode(), hashlib.sha256).hexdigest()
    try:
        if not hmac.compare_digest(expected, signature):
            return None
        payload = json.loads(_b64decode(raw))
    except (ValueError, TypeError, json.JSONDecodeError):
        return None
    now = int(time.time())
    ticket_id = str(payload.get("jti", ""))
    if payload.get("aud") != "wiki" or int(payload.get("exp", 0)) < now or not ticket_id or ticket_id in _seen:
        return None
    _seen[ticket_id] = int(payload["exp"])
    for key, expiry in list(_seen.items()):
        if expiry < now:
            _seen.pop(key, None)
    required = {"sub", "email", "org_id", "role"}
    return payload if required <= payload.keys() else None

def api_authorized(authorization: str | None) -> bool:
    token = os.getenv("FASTSME_API_TOKEN", "")
    return bool(token and authorization == f"Bearer {token}")

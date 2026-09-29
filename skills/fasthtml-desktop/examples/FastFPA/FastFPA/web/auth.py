"""Google OIDC and replay-safe FastOffice suite handoff."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import db


def google_enabled() -> bool:
    return bool(os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET"))


def new_state() -> str:
    return secrets.token_urlsafe(32)


def callback_uri(request) -> str:
    configured = os.getenv("GOOGLE_REDIRECT_URI", "")
    if configured:
        return configured
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
    return f"{proto}://{host}/auth/google/callback"


def google_authorize_url(request, state: str) -> str:
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
        "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
        "redirect_uri": callback_uri(request),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    })


def _json_request(url: str, *, data=None, token=None):
    body = urlencode(data).encode() if data else None
    headers = {"Accept": "application/json"}
    if data:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(url, data=body, headers=headers), timeout=20) as response:
        return json.loads(response.read())


def exchange_google(request, code: str) -> dict | None:
    try:
        token = _json_request(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
                "redirect_uri": callback_uri(request),
                "grant_type": "authorization_code",
            },
        )
        info = _json_request(
            "https://openidconnect.googleapis.com/v1/userinfo",
            token=token.get("access_token"),
        )
    except (HTTPError, URLError, TimeoutError, ValueError):
        return None
    email = (info.get("email") or "").strip().lower()
    if not email or info.get("email_verified") is False:
        return None
    domains = {value.strip().lower() for value in os.getenv("GOOGLE_ALLOWED_DOMAINS", "").split(",") if value.strip()}
    emails = {value.strip().lower() for value in os.getenv("GOOGLE_ALLOWED_EMAILS", "").split(",") if value.strip()}
    if domains or emails:
        domain = email.rsplit("@", 1)[-1]
        if email not in emails and domain not in domains:
            return None
    return {"email": email, "name": info.get("name") or email}


def redeem_suite_ticket(token: str, audience: str = "fpa") -> dict | None:
    secret = os.getenv("FASTOFFICE_SSO_SECRET", "")
    if not secret:
        return None
    try:
        encoded, supplied = token.split(".", 1)
        expected = hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, supplied):
            return None
        payload = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
        now = int(time.time())
        required = {"sub", "email", "name", "org_id", "org_name", "role", "jti", "exp", "aud"}
        if not required.issubset(payload) or payload["aud"] != audience or payload["exp"] < now:
            return None
        digest = hashlib.sha256(payload["jti"].encode()).hexdigest()
        with db.connection() as con:
            con.execute("DELETE FROM suite_ticket_redemptions WHERE expires_at<?", (now,))
            if con.execute(
                "SELECT 1 FROM suite_ticket_redemptions WHERE jti_hash=?", (digest,)
            ).fetchone():
                return None
            con.execute(
                "INSERT INTO suite_ticket_redemptions(jti_hash,expires_at,redeemed_at) VALUES (?,?,?)",
                (digest, payload["exp"], now),
            )
        return payload
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return None

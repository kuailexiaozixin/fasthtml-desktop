"""Safe public-demo adapters for FastERP, FastHRM, and FastCRM."""
from __future__ import annotations

import httpx

import db


FALLBACK_COUNTS = {"erp": 22, "hrm": 48, "crm": 36}


def refresh_all() -> list[dict]:
    for integration in db.integrations():
        try:
            response = httpx.get(integration["endpoint"], params={"limit": 100}, timeout=12)
            response.raise_for_status()
            payload = response.json()
            data = payload.get("data", payload if isinstance(payload, list) else [])
            count = len(data)
            db.record_integration(
                integration["key"],
                "Connected",
                count,
                f"Live synthetic API read succeeded from {integration['product']}",
            )
        except (httpx.HTTPError, ValueError, TypeError):
            db.record_integration(
                integration["key"],
                "Fixture fallback",
                FALLBACK_COUNTS[integration["key"]],
                "Source unavailable; deterministic local fixture remains active",
            )
    return db.integrations()

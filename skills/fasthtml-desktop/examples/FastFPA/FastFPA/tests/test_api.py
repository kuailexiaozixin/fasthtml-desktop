from __future__ import annotations

from fastapi.testclient import TestClient

import db
from web.api import api


def test_public_api_contract(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "api-test.sqlite")
    db.seed()
    client = TestClient(api)

    health = client.get("/v1/health")
    assert health.status_code == 200
    assert health.json()["synthetic"] is True

    scenarios = client.get("/v1/scenarios")
    assert scenarios.status_code == 200
    assert len(scenarios.json()["data"]) == 5

    statements = client.get("/v1/statements/baseline")
    assert statements.status_code == 200
    payload = statements.json()
    assert payload["currency"] == "GBP"
    assert payload["summary"]["balance_check"] <= 0.02
    assert payload["summary"]["cash_check"] <= 0.02

    assert client.get("/v1/statements/missing").status_code == 404


def test_crawler_routes_precede_static_file_fallback():
    from web_app import app

    client = TestClient(app)
    sitemap = client.get("/sitemap.xml")
    assert sitemap.status_code == 200
    assert "https://fpa.fastsme.com/" in sitemap.text
    robots = client.get("/robots.txt")
    assert robots.status_code == 200
    assert "Sitemap: https://fpa.fastsme.com/sitemap.xml" in robots.text

"""Versioned public synthetic-demo API."""
from __future__ import annotations

import os
import secrets

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import db

api = FastAPI(
    title="FastFPA API",
    version="1.0.0",
    description="Synthetic financial planning, scenario, and statement data.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


class ScenarioDraftRequest(BaseModel):
    scenario: str = Field(default="baseline")
    question: str = Field(min_length=3, max_length=1000)


@api.get("/")
def discovery():
    return {
        "product": "FastFPA",
        "version": "v1",
        "synthetic": True,
        "resources": [
            "/api/v1/scenarios",
            "/api/v1/statements/{scenario}",
            "/api/v1/variances",
            "/api/v1/integrations",
            "/api/v1/recurring/{scenario}",
        ],
    }


@api.get("/v1/health")
def health():
    return {"status": "ok", "product": "FastFPA", "synthetic": True}


@api.get("/v1/scenarios")
def scenarios():
    return {"data": db.scenarios()}


@api.get("/v1/statements/{scenario}")
def statements(scenario: str):
    if not db.get_scenario(scenario):
        raise HTTPException(status_code=404, detail="scenario_not_found")
    return db.api_snapshot(scenario)


@api.get("/v1/variances")
def variances(left: str = "baseline", right: str = "budget"):
    if not db.get_scenario(left) or not db.get_scenario(right):
        raise HTTPException(status_code=404, detail="scenario_not_found")
    return {"left": left, "right": right, "data": db.comparison(left, right), "currency": "GBP"}


@api.get("/v1/integrations")
def integrations():
    return {"data": db.integrations()}


@api.get("/v1/recurring/{scenario}")
def recurring(scenario: str):
    if not db.get_scenario(scenario):
        raise HTTPException(status_code=404, detail="scenario_not_found")
    return {"scenario": scenario, "currency": "GBP", "data": db.recurring(scenario)}


@api.post("/v1/scenario-drafts")
def scenario_draft(payload: ScenarioDraftRequest, request: Request):
    """Return a reviewable draft only; never mutate an authoritative plan."""
    configured = os.getenv("FASTSME_API_TOKEN", "")
    if not configured:
        raise HTTPException(status_code=503, detail="writes_disabled")
    supplied = request.headers.get("authorization", "").removeprefix("Bearer ").strip()
    if not supplied or not secrets.compare_digest(supplied, configured):
        raise HTTPException(status_code=401, detail="invalid_token")
    if not db.get_scenario(payload.scenario):
        raise HTTPException(status_code=404, detail="scenario_not_found")
    return {
        "status": "draft",
        "scenario": payload.scenario,
        "request": payload.question,
        "proposed_changes": [],
        "applied": False,
        "requires_review": True,
    }

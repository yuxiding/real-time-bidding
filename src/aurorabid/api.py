"""Stateless quote API. The caller owns campaign state and settlement."""
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
import os
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, model_validator
from .auction import BudgetController
from .features import encode_requests
from .models import load_models
from .policies import ValuePolicy, PPOAgent
from .environment import make_observation


class BidRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    request_id: str = Field(min_length=1, max_length=128)
    timestamp: AwareDatetime
    age: int = Field(ge=18, le=100)
    segment: int = Field(ge=0, le=2)
    adslot_id: int = Field(ge=0, le=3)
    floor_price: float = Field(ge=0)
    prior_impressions: float = Field(ge=0, default=0)
    prior_clicks: float = Field(ge=0, default=0)
    prior_conversions: float = Field(ge=0, default=0)
    clicks_last_hour: float = Field(ge=0, default=0)
    seconds_since_click: float = Field(ge=0, default=86400)
    remaining_budget: float = Field(ge=0)
    initial_budget: float = Field(gt=0)
    time_remaining: float = Field(ge=0, le=1)
    strategy: Literal["value", "ppo"] = "value"

    @model_validator(mode="after")
    def validate_history_and_budget(self):
        if self.remaining_budget > self.initial_budget:
            raise ValueError("remaining_budget cannot exceed initial_budget")
        if not self.prior_conversions <= self.prior_clicks <= self.prior_impressions:
            raise ValueError("History requires conversions <= clicks <= impressions")
        if self.clicks_last_hour > self.prior_clicks:
            raise ValueError("Recent clicks cannot exceed total prior clicks")
        return self


def create_app(model_dir=None):
    directory = Path(model_dir or os.environ.get("AURORABID_MODEL_DIR", "outputs/models"))

    @asynccontextmanager
    async def lifespan(app):
        bundle = load_models(directory)  # Fail at startup; never serve random weights.
        app.state.bundle = bundle
        app.state.ppo = PPOAgent.load(directory / "ppo.zip") if (directory / "ppo.zip").is_file() else None
        yield

    application = FastAPI(title="AuroraBid", version="0.2.0", lifespan=lifespan,
                          description="Synthetic-auction bidding quotes. Stateless; not a production exchange.")

    @application.get("/health")
    def health(request: Request):
        return {"status": "ok", "model_source_sha256": request.app.state.bundle["metadata"]["source_sha256"]}

    @application.post("/bid")
    def bid(payload: BidRequest, request: Request):
        bundle = request.app.state.bundle
        metadata, models = bundle["metadata"], bundle["models"]
        features = encode_requests(pd.DataFrame([payload.model_dump()]))
        pctr = float(models["ctr"].predict(features)[0])
        pcvr = float(models["cvr"].predict(features)[0])
        observation = make_observation(pctr, pcvr, payload.floor_price, payload.remaining_budget,
                                       payload.initial_budget, payload.time_remaining, metadata["max_bid"],
                                       metadata["conversion_value"])
        if payload.strategy == "ppo":
            policy = request.app.state.ppo
            if policy is None:
                raise HTTPException(503, "PPO checkpoint is unavailable. Run aurorabid reproduce.")
        else:
            policy = ValuePolicy(metadata["value_multiplier"])
        controller = BudgetController(payload.remaining_budget, metadata["max_bid"])
        quote = controller.cap(policy.bid(observation, metadata["conversion_value"]))
        if quote < payload.floor_price or payload.time_remaining == 0:
            quote = 0.
        return {"request_id": payload.request_id, "bid": quote, "pctr": pctr,
                "pcvr_given_click": pcvr, "strategy": payload.strategy,
                "model_source_sha256": metadata["source_sha256"]}

    return application


app = create_app()

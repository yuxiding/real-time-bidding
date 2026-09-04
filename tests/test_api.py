import json
import joblib
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from aurorabid.api import create_app
from aurorabid.data import generate_data
from aurorabid.features import build_features, build_history
from aurorabid.models import ProbabilityModel, save_models


@pytest.fixture
def served(tmp_path):
    data = generate_data(1000, seed=4)
    features = build_features(data.opportunities, data.activity)
    ctr = ProbabilityModel().fit(features, data.opportunities.clicked)
    mask = data.opportunities.clicked == 1
    cvr = ProbabilityModel().fit(features[mask], data.opportunities.loc[mask, "converted"])
    save_models({"ctr": ctr, "cvr": cvr}, tmp_path,
                {"max_bid": 5., "conversion_value": 30., "value_multiplier": 1., "source_sha256": "test"})
    raw = data.opportunities.iloc[[100]]
    sample = raw.join(build_history(raw, data.activity)).iloc[0]
    payload = {k: int(sample[k]) for k in ["age", "segment", "adslot_id"]}
    payload.update({k: float(sample[k]) for k in ["floor_price", "prior_impressions", "prior_clicks", "prior_conversions", "clicks_last_hour", "seconds_since_click"]})
    payload.update({"request_id": "example", "timestamp": sample.timestamp.isoformat(),
                    "remaining_budget": 5., "initial_budget": 10., "time_remaining": .5})
    return tmp_path, payload, ctr.predict(features.iloc[[100]])[0]


def test_api_prediction_matches_offline_model_and_request_is_not_hardcoded(served):
    directory, payload, expected = served
    with TestClient(create_app(directory)) as client:
        assert client.get("/health").status_code == 200
        response = client.post("/bid", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["pctr"] == pytest.approx(expected)
        assert body["request_id"] == "example"
        assert 0 <= body["bid"] <= 5.
        altered = dict(payload, request_id="other", age=65, segment=0)
        assert client.post("/bid", json=altered).json()["pctr"] != body["pctr"]
        assert client.post("/bid", json=dict(payload, remaining_budget=0)).json()["bid"] == 0.
        assert client.post("/bid", json=dict(payload, time_remaining=0)).json()["bid"] == 0.
        assert client.post("/bid", json=dict(payload, strategy="ppo")).status_code == 503


def test_validation_and_checkpoint_failures_are_explicit(served, tmp_path):
    directory, payload, _ = served
    with TestClient(create_app(directory)) as client:
        for changes in [{"remaining_budget": -1}, {"remaining_budget": 11}, {"segment": 99},
                        {"market_price": 100}, {"prior_conversions": 10000}]:
            assert client.post("/bid", json=dict(payload, **changes)).status_code == 422
    with pytest.raises(FileNotFoundError):
        with TestClient(create_app(tmp_path / "missing")):
            pass
    path = directory / "probability_models.joblib"
    bundle = joblib.load(path)
    bundle["schema"] = list(reversed(bundle["schema"]))
    joblib.dump(bundle, path)
    with pytest.raises(ValueError, match="schema"):
        with TestClient(create_app(directory)):
            pass

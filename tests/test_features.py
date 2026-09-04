import numpy as np
import pandas as pd
from aurorabid.data import generate_data, chronological_split
from aurorabid.features import build_features, build_history, encode_requests, ordered_features, FEATURE_COLUMNS


def test_outcomes_are_not_features_and_generation_is_reproducible():
    a, b = generate_data(500, 17), generate_data(500, 17)
    pd.testing.assert_frame_equal(a.opportunities, b.opportunities)
    pd.testing.assert_frame_equal(a.activity, b.activity)
    expected = build_features(a.opportunities, a.activity)
    changed = a.opportunities.copy()
    changed["clicked"] = 1 - changed.clicked
    changed["converted"] = 1 - changed.converted
    changed["market_price"] *= 100
    pd.testing.assert_frame_equal(expected, build_features(changed, a.activity))


def test_delayed_feedback_and_strict_event_time_boundary():
    base = pd.Timestamp("2025-01-01", tz="UTC")
    events = pd.DataFrame([{"user_id": "u", "impression_timestamp": base,
        "click_timestamp": base + pd.Timedelta(minutes=5),
        "conversion_timestamp": base + pd.Timedelta(minutes=10), "clicked": True, "converted": True}])
    requests = pd.DataFrame({"user_id": ["u"] * 4,
        "timestamp": [base, base + pd.Timedelta(minutes=5), base + pd.Timedelta(minutes=6), base + pd.Timedelta(minutes=11)]})
    hist = build_history(requests, events)
    assert hist.prior_impressions.tolist() == [0, 1, 1, 1]
    assert hist.prior_clicks.tolist() == [0, 0, 1, 1]
    assert hist.prior_conversions.tolist() == [0, 0, 0, 1]
    assert hist.seconds_since_click.iloc[2] == 60


def test_api_encoding_matches_training_and_named_order_is_stable():
    data = generate_data(500, 8)
    raw = data.opportunities.iloc[[100]]
    offline = build_features(raw, data.activity)
    serving = encode_requests(raw.join(build_history(raw, data.activity)))
    pd.testing.assert_frame_equal(offline, serving)
    shuffled = serving.loc[:, list(reversed(FEATURE_COLUMNS))]
    np.testing.assert_array_equal(offline, ordered_features(shuffled))


def test_splits_are_temporal_and_do_not_split_equal_timestamps():
    data = generate_data(500).opportunities
    data.loc[300, "timestamp"] = data.loc[299, "timestamp"]
    train, validation, test = chronological_split(data.sample(frac=1, random_state=3))
    assert train.timestamp.max() < validation.timestamp.min()
    assert validation.timestamp.max() < test.timestamp.min()
    assert len(train) + len(validation) + len(test) == len(data)

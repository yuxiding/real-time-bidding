"""One named schema shared by training, replay and API inference."""
import numpy as np
import pandas as pd

FEATURE_COLUMNS = (
    "age", "segment_0", "segment_1", "segment_2",
    "slot_0", "slot_1", "slot_2", "slot_3", "hour_sin", "hour_cos",
    "floor_price", "prior_impressions", "prior_clicks", "prior_conversions",
    "clicks_last_hour", "seconds_since_click",
)
HISTORY_COLUMNS = FEATURE_COLUMNS[11:]


def build_history(opportunities: pd.DataFrame, activity: pd.DataFrame) -> pd.DataFrame:
    """Use only background events strictly earlier than the request timestamp.

    A click becomes available at click_timestamp, not impression_timestamp.
    No target-outcome columns from opportunities are read here.
    """
    result = pd.DataFrame(0., index=opportunities.index, columns=HISTORY_COLUMNS)
    result["seconds_since_click"] = 86400.
    groups = {uid: group for uid, group in activity.groupby("user_id")}
    for uid, requests in opportunities.groupby("user_id"):
        events = groups.get(uid)
        if events is None:
            continue
        times = pd.to_datetime(requests.timestamp, utc=True).astype("int64").to_numpy()
        def event_times(column, mask=None):
            rows = events if mask is None else events.loc[mask]
            return np.sort(pd.to_datetime(rows[column], utc=True).dropna().astype("int64").to_numpy())
        impressions = event_times("impression_timestamp")
        clicks = event_times("click_timestamp", events.clicked.astype(bool))
        conversions = event_times("conversion_timestamp", events.converted.astype(bool))
        n_clicks = np.searchsorted(clicks, times, side="left")
        result.loc[requests.index, "prior_impressions"] = np.searchsorted(impressions, times, side="left")
        result.loc[requests.index, "prior_clicks"] = n_clicks
        result.loc[requests.index, "prior_conversions"] = np.searchsorted(conversions, times, side="left")
        result.loc[requests.index, "clicks_last_hour"] = n_clicks - np.searchsorted(clicks, times - 3600 * 10**9, side="left")
        if len(clicks):
            gap = np.where(n_clicks > 0, (times - clicks[np.maximum(n_clicks - 1, 0)]) / 1e9, 86400.)
            result.loc[requests.index, "seconds_since_click"] = np.minimum(gap, 86400.)
    return result


def build_features(opportunities: pd.DataFrame, activity: pd.DataFrame) -> pd.DataFrame:
    history = build_history(opportunities, activity)
    return encode_requests(opportunities.join(history))


def encode_requests(frame: pd.DataFrame) -> pd.DataFrame:
    """Encode request fields and already-available history; no learned encoder."""
    out = pd.DataFrame(index=frame.index)
    out["age"] = frame.age / 100.
    for i in range(3):
        out[f"segment_{i}"] = (frame.segment == i).astype(float)
    for i in range(4):
        out[f"slot_{i}"] = (frame.adslot_id == i).astype(float)
    ts = pd.to_datetime(frame.timestamp, utc=True)
    hours = ts.dt.hour + ts.dt.minute / 60
    out["hour_sin"] = np.sin(hours / 24 * 2 * np.pi)
    out["hour_cos"] = np.cos(hours / 24 * 2 * np.pi)
    out["floor_price"] = frame.floor_price
    for col in HISTORY_COLUMNS:
        if col == "seconds_since_click":
            out[col] = np.minimum(frame[col], 86400.) / 86400.
        else:
            out[col] = np.log1p(frame[col])
    return ordered_features(out)


def ordered_features(frame: pd.DataFrame) -> pd.DataFrame:
    missing = set(FEATURE_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing features: {sorted(missing)}")
    result = frame.loc[:, FEATURE_COLUMNS].astype(float)
    if not np.isfinite(result.to_numpy()).all():
        raise ValueError("Features must be finite.")
    return result

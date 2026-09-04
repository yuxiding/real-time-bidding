"""Seeded synthetic opportunities and a separate background activity stream.

Every opportunity has a potential outcome, including auctions a bidder loses.
Those outcomes are simulator-only and never become model inputs. Background
activity is exogenous: it is not affected by the bidding policy being evaluated.
"""
from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass
class SyntheticData:
    opportunities: pd.DataFrame
    activity: pd.DataFrame


def generate_data(n: int = 15000, seed: int = 2026) -> SyntheticData:
    if n < 500:
        raise ValueError("Use at least 500 opportunities for chronological splits.")
    rng = np.random.default_rng(seed)
    n_users = 250
    age = rng.integers(18, 66, n_users)
    segments = rng.integers(0, 3, n_users)
    start = pd.Timestamp("2025-01-01", tz="UTC")
    user = rng.integers(0, n_users, n)
    slot = rng.integers(0, 4, n)
    timestamp = start + pd.to_timedelta(np.arange(n) * 30, unit="s")
    hour = timestamp.hour.to_numpy()
    segment = segments[user]
    sigmoid = lambda x: 1 / (1 + np.exp(-x))
    # Controlled structure gives models learnable, imperfect signals.
    p_click = sigmoid(-2.7 + 1.1 * (segment == 2) + .55 * (slot == 2)
                      + .5 * (age[user] < 35) + .25 * np.sin(hour / 24 * 2 * np.pi))
    p_conversion_given_click = sigmoid(-1.8 + .9 * (segment == 2)
                                       + .6 * (slot == 1) + .35 * (age[user] > 35))
    clicked = rng.random(n) < p_click
    converted = clicked & (rng.random(n) < p_conversion_given_click)
    floor = rng.uniform(.05, .35, n)
    market = rng.lognormal(-.45 + .18 * (slot == 2), .55, n)
    opportunities = pd.DataFrame({
        "request_id": [f"req{i:06d}" for i in range(n)],
        "user_id": [f"u{i:04d}" for i in user],
        "timestamp": timestamp, "age": age[user], "segment": segment,
        "adslot_id": slot, "floor_price": floor,
        "market_price": market, "clicked": clicked.astype(int),
        "converted": converted.astype(int),
    })
    # Separate publisher-wide interactions; availability is event-time based.
    count = n * 2
    background_user = rng.integers(0, n_users, count)
    seconds = rng.integers(-86400, n * 30, count)
    background_click = rng.random(count) < (.06 + .09 * (segments[background_user] == 2))
    background_conversion = background_click & (rng.random(count) < .2)
    activity = pd.DataFrame({
        "user_id": [f"u{i:04d}" for i in background_user],
        "impression_timestamp": start + pd.to_timedelta(seconds, unit="s"),
        "click_timestamp": start + pd.to_timedelta(seconds + rng.integers(1, 120, count), unit="s"),
        "conversion_timestamp": start + pd.to_timedelta(seconds + 120 + rng.integers(1, 3600, count), unit="s"),
        "clicked": background_click, "converted": background_conversion,
    })
    return SyntheticData(opportunities, activity)


def chronological_split(frame: pd.DataFrame):
    """Split whole timestamp groups; equal-time events cannot cross boundaries."""
    ordered = frame.sort_values(["timestamp", "request_id"]).reset_index(drop=True)
    times = ordered.timestamp.drop_duplicates().sort_values().to_numpy()
    if len(times) < 5:
        raise ValueError("Need at least five distinct timestamps.")
    train_end, validation_end = times[int(len(times) * .6)], times[int(len(times) * .8)]
    return (ordered[ordered.timestamp < train_end].copy(),
            ordered[(ordered.timestamp >= train_end) & (ordered.timestamp < validation_end)].copy(),
            ordered[ordered.timestamp >= validation_end].copy())

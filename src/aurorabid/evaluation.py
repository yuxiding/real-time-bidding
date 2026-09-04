"""All policies replay the same immutable holdout opportunities."""
import numpy as np
import pandas as pd
from .environment import AuctionEnv


def evaluate(policy, frame, **env_kwargs):
    env = AuctionEnv(frame, **env_kwargs)
    observation, _ = env.reset(seed=0)
    trace = []
    done = False
    while not done:
        bid = policy.bid(observation, env.conversion_value)
        observation, _, done, _, info = env.step_bid(bid)
        trace.append(info)
    trace = pd.DataFrame(trace)
    totals = trace.sum()
    spend = float(totals.cost)
    wins, clicks, conversions = int(totals.won), int(totals.clicks), int(totals.conversions)
    metrics = {
        "opportunities": len(frame), "wins": wins, "clicks": clicks, "conversions": conversions,
        "spend": spend, "budget": env.budget, "budget_utilization": spend / env.budget,
        "revenue": float(totals.revenue), "profit": float(totals.profit),
        "roi": float(totals.profit) / spend if spend else None,
        "ctr": clicks / wins if wins else 0., "cvr": conversions / clicks if clicks else 0.,
        "cpm": spend / wins * 1000 if wins else 0., "win_rate": wins / len(frame),
    }
    if spend > env.budget + 1e-8 or trace.bid.max() > env.max_bid + 1e-8:
        raise AssertionError("Auction replay violated a spending constraint.")
    trace["cumulative_spend"] = trace.cost.cumsum()
    trace["cumulative_profit"] = trace.profit.cumsum()
    return metrics, trace


def attach_probabilities(frame, models):
    result = frame.copy()
    result["pctr"] = models["ctr"].predict(frame)
    result["pcvr"] = models["cvr"].predict(frame)
    return result


def select_value_multiplier(validation, candidates, env_kwargs):
    from .policies import ValuePolicy
    scores = [(evaluate(ValuePolicy(m), validation, **env_kwargs)[0]["profit"], m) for m in candidates]
    # Only validation is used to select the scalar.
    return max(scores, key=lambda pair: pair[0])[1], scores

import numpy as np
import pandas as pd
import pytest
from gymnasium.utils.env_checker import check_env
from aurorabid.auction import BudgetController, clear_auction
from aurorabid.environment import AuctionEnv
from aurorabid.policies import ConstantPolicy, LinUCBAgent, PPOAgent
from aurorabid.evaluation import evaluate


@pytest.fixture
def frame():
    return pd.DataFrame({"pctr": [.2] * 20, "pcvr": [.3] * 20, "floor_price": [.1] * 20,
                         "market_price": [.8] * 20, "clicked": [1, 0] * 10, "converted": [1, 0] * 10})


def test_floor_zero_bid_and_tie_rules():
    assert clear_auction(.5, .2, .6) == (False, 0.)
    assert clear_auction(.6, .2, .6) == (True, .6)
    assert clear_auction(0., 0.) == (False, 0.)
    assert clear_auction(1., 1.) == (True, 1.)


def test_settlement_and_pacing_cannot_exceed_limits():
    budget = BudgetController(10., 5., spent=9.9)
    assert budget.cap(6.) == pytest.approx(.1)
    with pytest.raises(ValueError):
        budget.charge(1.)
    budget.charge(budget.remaining)
    assert budget.spent == 10.
    assert budget.cap(10.) == 0.
    assert BudgetController(100., 5.).cap(6.) == 5.
    with pytest.raises(ValueError):
        budget.cap(float("nan"))


def test_gym_contract_and_hidden_outcomes(frame):
    env = AuctionEnv(frame)
    check_env(env, skip_render_check=True)
    obs, _ = env.reset(seed=42)
    changed = frame.copy()
    changed.market_price = 100.
    changed.clicked = 0
    changed.converted = 0
    other, _ = AuctionEnv(changed).reset(seed=42)
    np.testing.assert_array_equal(obs, other)


def test_metrics_count_only_won_outcomes_and_respect_budget(frame):
    metrics, trace = evaluate(ConstantPolicy(100.), frame, budget_per_opportunity=.1)
    assert metrics["wins"] == 2
    assert metrics["clicks"] == 1
    assert metrics["conversions"] == 1
    assert metrics["spend"] == pytest.approx(1.6)
    assert metrics["profit"] == pytest.approx(30. - 1.6)
    assert metrics["ctr"] == .5
    assert trace.cumulative_spend.max() <= metrics["budget"]
    empty, _ = evaluate(ConstantPolicy(0.), frame)
    assert empty["roi"] is None and empty["wins"] == 0


def test_bandit_learns_action_specific_rewards_without_test_updates(frame):
    agent = LinUCBAgent()
    obs, _ = AuctionEnv(frame).reset(seed=1)
    for _ in range(10):
        agent.update(obs, 4, 1.)
    assert agent.select_action(obs) == 4
    before = agent.b.copy()
    evaluate(agent, frame)
    np.testing.assert_array_equal(before, agent.b)


def test_real_ppo_training_and_checkpoint_roundtrip(frame, tmp_path):
    env = AuctionEnv(frame)
    agent = PPOAgent.train(env, timesteps=512)
    obs, _ = env.reset(seed=2)
    before = agent.bid(obs, 30.)
    agent.save(str(tmp_path / "ppo.zip"))
    restored = PPOAgent.load(tmp_path / "ppo.zip")
    assert restored.bid(obs, 30.) == before
    metrics, _ = evaluate(restored, frame)
    assert metrics["spend"] <= metrics["budget"]

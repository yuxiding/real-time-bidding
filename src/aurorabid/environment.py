"""Gymnasium environment; hidden prices/outcomes are excluded from observations."""
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from .auction import BudgetController, clear_auction

MULTIPLIERS = np.array([0., .5, 1., 1.5, 2.])
OBSERVATION_COLUMNS = ["pctr", "pcvr", "normalized_value", "normalized_floor",
                       "budget_remaining_fraction", "time_remaining_fraction"]


def make_observation(pctr, pcvr, floor, remaining, initial_budget, time_remaining,
                     max_bid, conversion_value):
    return np.array([pctr, pcvr, min(1., pctr * pcvr * conversion_value / max_bid),
                     min(1., floor / max_bid), remaining / initial_budget,
                     time_remaining], dtype=np.float32)


class AuctionEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, frame, budget_per_opportunity=.35, max_bid=5., conversion_value=30.,
                 episode_size=None, random_start=False):
        super().__init__()
        if len(frame) == 0 or budget_per_opportunity <= 0 or max_bid <= 0 or conversion_value <= 0:
            raise ValueError("Nonempty data and positive finite limits are required.")
        if not np.isfinite([budget_per_opportunity, max_bid, conversion_value]).all():
            raise ValueError("Limits must be finite.")
        self.frame = frame.reset_index(drop=True)
        self.values = self.frame[["pctr", "pcvr", "floor_price", "market_price", "clicked", "converted"]].to_numpy(float)
        self.size = len(frame) if episode_size is None else min(episode_size, len(frame))
        if self.size < 1:
            raise ValueError("episode_size must be positive.")
        self.budget = self.size * budget_per_opportunity
        self.max_bid, self.conversion_value = max_bid, conversion_value
        self.random_start = random_start
        self.observation_space = spaces.Box(0., 1., shape=(6,), dtype=np.float32)
        self.action_space = spaces.Discrete(len(MULTIPLIERS))
        self.ended = True

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.start = int(self.np_random.integers(0, len(self.frame) - self.size + 1)) if self.random_start else 0
        self.idx = 0
        self.controller = BudgetController(self.budget, self.max_bid)
        self.ended = False
        return self.observation(), {}

    def observation(self):
        if self.ended:
            return np.zeros(6, dtype=np.float32)
        pctr, pcvr, floor = self.values[self.start + self.idx, :3]
        return make_observation(pctr, pcvr, floor, self.controller.remaining, self.budget,
                                1 - self.idx / self.size, self.max_bid, self.conversion_value)

    def step(self, action):
        if not self.action_space.contains(action):
            raise ValueError("Action must be a valid multiplier index.")
        pctr, pcvr = self.values[self.start + self.idx, :2]
        return self.step_bid(float(MULTIPLIERS[action] * pctr * pcvr * self.conversion_value))

    def step_bid(self, proposed_bid):
        """Shared settlement path for learned policies and direct-bid baselines."""
        if self.ended:
            raise RuntimeError("Call reset() before stepping a finished episode.")
        _, _, floor, market, clicked, converted = self.values[self.start + self.idx]
        bid = self.controller.cap(proposed_bid)
        won, cost = clear_auction(bid, market, floor)
        self.controller.charge(cost)
        clicks, conversions = int(won and clicked), int(won and converted)
        revenue = conversions * self.conversion_value
        info = {"bid": bid, "won": int(won), "cost": cost, "clicks": clicks,
                "conversions": conversions, "revenue": revenue, "profit": revenue - cost}
        self.idx += 1
        self.ended = self.idx >= self.size
        return self.observation(), (revenue - cost) / self.conversion_value, self.ended, False, info

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Dict
from src.simulation.bid_simulator import BidSimulator
from src.simulation.auction_engine import SecondPriceAuction
from src.features.feature_store import LocalFeatureStore


class AuctionEnv(gym.Env):
    """
    RL训练环境：广告竞价环境，基于OpenAI Gym封装
    - 状态：特征向量（user + context + history）
    - 动作：bid_ratio（0~1）
    - 奖励：点击价值 - 出价成本（如果中标）
    """
    def __init__(self, imp_df, feature_store: LocalFeatureStore,
                 bid_simulator: BidSimulator,
                 auction_engine: SecondPriceAuction,
                 max_bid: float = 10.0,
                 click_value: float = 50.0):
        super(AuctionEnv, self).__init__()

        self.imp_df = imp_df.reset_index(drop=True)
        self.feature_store = feature_store
        self.bid_simulator = bid_simulator
        self.auction_engine = auction_engine
        self.max_bid = max_bid
        self.click_value = click_value

        self.state_dim = len(feature_store.get_combined_feature(
            user_id=self.imp_df.iloc[0]["user_id"],
            adslot_id=self.imp_df.iloc[0]["adslot_id"],
            request_id=self.imp_df.iloc[0]["request_id"]
        ))

        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(self.state_dim,), dtype=np.float32)
        self.action_space = spaces.Box(low=0.0, high=1.0, shape=(1,), dtype=np.float32)

        self.idx = 0
        self.done = False

    def reset(self):
        self.idx = 0
        self.done = False
        return self._get_state(), {}

    def _get_state(self):
        row = self.imp_df.iloc[self.idx]
        feature = self.feature_store.get_combined_feature(row["user_id"], row["adslot_id"], row["request_id"])
        return np.array(list(feature.values()), dtype=np.float32)

    def step(self, action):
        bid_ratio = np.clip(action[0], 0, 1)
        bid_price = bid_ratio * self.max_bid

        row = self.imp_df.iloc[self.idx]
        uid, slot, req_id = row["user_id"], row["adslot_id"], row["request_id"]
        market_price = self.bid_simulator.sample_market_price()

        win, clear_price = self.auction_engine.execute(bid_price, [market_price])
        clicked = row.get("clicked", False)  # assume imp_df includes click flag

        reward = 0
        cost = 0
        if win:
            cost = clear_price
            reward = self.click_value if clicked else 0
            reward -= cost  # reward = value - cost

        self.idx += 1
        if self.idx >= len(self.imp_df):
            self.done = True

        next_state = self._get_state() if not self.done else np.zeros(self.state_dim)
        return next_state, reward, self.done, False, {"cost": cost, "clicked": clicked}


if __name__ == '__main__':
    import pandas as pd
    fs = LocalFeatureStore("data/processed")
    fs.load()
    imp_df = pd.read_csv("data/raw/impressions.csv").head(100)
    imp_df["clicked"] = np.random.rand(len(imp_df)) < 0.1

    sim = BidSimulator("artifacts/bid_landscape.pkl")
    engine = SecondPriceAuction()
    env = AuctionEnv(imp_df, fs, sim, engine)

    state, _ = env.reset()
    done = False
    while not done:
        action = env.action_space.sample()
        state, reward, done, _, info = env.step(action)
        print(f"Bid: {action[0]:.2f}, Reward: {reward:.2f}, Cost: {info['cost']:.2f}, Clicked: {info['clicked']}")

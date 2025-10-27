import pandas as pd
import numpy as np
from src.features.feature_store import LocalFeatureStore
from src.simulation.bid_simulator import BidSimulator
from src.simulation.auction_engine import SecondPriceAuction
from src.simulation.market_env import AuctionEnv
from src.models.rl_agent import PPOAgent
import tqdm


# ------------------------ Config ------------------------
INPUT_DIM = 26
MAX_BID = 5.0
EPISODES = 10
STEP_PER_EPISODE = 1000
CLICK_VALUE = 50.0

# ------------------------ Prepare Components ------------------------
imp_df = pd.read_csv("data/raw/impressions.csv", parse_dates=['timestamp']).head(10000)
clk_df = pd.read_csv("data/raw/clicks.csv")
imp_df["clicked"] = imp_df["request_id"].isin(set(clk_df.request_id.values))

fs = LocalFeatureStore("data/processed")
fs.load()
sim = BidSimulator("artifacts/bid_landscape.pkl")
engine = SecondPriceAuction()

env = AuctionEnv(
    imp_df=imp_df,
    feature_store=fs,
    bid_simulator=sim,
    auction_engine=engine,
    max_bid=MAX_BID,
    click_value=CLICK_VALUE
)

agent = PPOAgent(input_dim=INPUT_DIM, max_bid=MAX_BID)

# ------------------------ RL Training Loop ------------------------
for episode in range(EPISODES):
    state, _ = env.reset()
    done = False

    states, old_ratios, actions, rewards = [], [], [], []

    while not done:
        bid_price, ratio = agent.select_action(state)
        action = [ratio]  # env expects [bid_ratio]

        next_state, reward, done, _, _ = env.step(action)

        # log transition
        states.append(state)
        old_ratios.append(ratio)
        actions.append(bid_price)
        rewards.append(reward)

        state = next_state

    print(f"Episode {episode+1}: Reward Sum = {sum(rewards):.2f}")
    agent.update(states, old_ratios, actions, rewards)

# ------------------------ Save Model ------------------------
agent.save("checkpoints/rl_agent.pt")
print("RL agent saved to checkpoints/rl_agent.pt")

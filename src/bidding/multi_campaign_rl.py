from typing import Dict
import numpy as np
from collections import defaultdict


class MultiCampaignRLAgent:
    """
    多 campaign 协同强化学习控制器：
    - 每个 campaign 独立使用一个 RL agent
    - 中央调度策略分配预算/资源（可选）
    """
    def __init__(self, agent_class, campaign_ids, agent_kwargs=None):
        """
        参数：
        - agent_class: 传入 PPOAgent/DDPGAgent 等 class
        - campaign_ids: list of campaign IDs
        - agent_kwargs: 传入 agent 初始化参数
        """
        self.campaigns = campaign_ids
        self.agents: Dict[str, object] = {}
        agent_kwargs = agent_kwargs or {}

        for cid in campaign_ids:
            self.agents[cid] = agent_class(**agent_kwargs)

        self.stats = defaultdict(lambda: {"imps": 0, "clicks": 0, "spend": 0})

    def select_action(self, campaign_id: str, state: np.ndarray) -> float:
        agent = self.agents[campaign_id]
        bid_price, _ = agent.select_action(state)
        return bid_price

    def update(self, campaign_id: str, states, old_ratios, actions, returns):
        agent = self.agents[campaign_id]
        agent.update(states, old_ratios, actions, returns)

    def log(self, campaign_id: str, cost: float, clicked: bool = False):
        self.stats[campaign_id]["imps"] += 1
        self.stats[campaign_id]["spend"] += cost
        if clicked:
            self.stats[campaign_id]["clicks"] += 1

    def report(self):
        print("\n Multi-Campaign Report")
        for cid, stat in self.stats.items():
            ctr = stat["clicks"] / stat["imps"] if stat["imps"] > 0 else 0
            cpm = stat["spend"] / stat["imps"] * 1000 if stat["imps"] > 0 else 0
            print(f"- {cid}: Imps={stat['imps']}, Clicks={stat['clicks']}, CTR={ctr:.4f}, Spend={stat['spend']:.2f}, CPM={cpm:.2f}")


if __name__ == "__main__":
    from src.models.rl_agent import PPOAgent

    agent = MultiCampaignRLAgent(
        agent_class=PPOAgent,
        campaign_ids=["camp_A", "camp_B"],
        agent_kwargs={"input_dim": 20, "max_bid": 5.0}
    )

    dummy_state = np.random.rand(20)
    for _ in range(5):
        for cid in ["camp_A", "camp_B"]:
            bid = agent.select_action(cid, dummy_state)
            agent.log(cid, cost=bid, clicked=np.random.rand() < 0.2)

    agent.report()

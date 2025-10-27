import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np


class ConstrainedActor(nn.Module):
    def __init__(self, input_dim, hidden_dim=128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.net(x)


class LagrangianPPOAgent:
    """
    约束强化学习智能体（Lagrangian-based PPO）
    目标：最大化 reward，同时满足 cost_constraint（如预算约束）
    """
    def __init__(self, input_dim, max_bid=10.0, gamma=0.99, clip_eps=0.2, cost_limit=0.1, lr=3e-4):
        self.actor = ConstrainedActor(input_dim)
        self.optimizer = optim.Adam(self.actor.parameters(), lr=lr)
        self.gamma = gamma
        self.clip_eps = clip_eps
        self.max_bid = max_bid

        # Lagrangian multiplier λ
        self.lambda_param = torch.tensor(1.0, requires_grad=True)
        self.lambda_optimizer = optim.Adam([self.lambda_param], lr=1e-2)

        self.cost_limit = cost_limit  # 每步成本约束

    def select_action(self, state):
        state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():
            bid_ratio = self.actor(state_tensor).item()
        bid_price = bid_ratio * self.max_bid
        return bid_price, bid_ratio

    def compute_returns(self, rewards, costs, dones):
        R, C = 0, 0
        returns, cost_returns = [], []
        for r, c, done in zip(reversed(rewards), reversed(costs), reversed(dones)):
            if done:
                R, C = 0, 0
            R = r + self.gamma * R
            C = c + self.gamma * C
            returns.insert(0, R)
            cost_returns.insert(0, C)
        return torch.tensor(returns, dtype=torch.float32), torch.tensor(cost_returns, dtype=torch.float32)

    def update(self, states, old_ratios, actions, rewards, costs, dones):
        states = torch.tensor(states, dtype=torch.float32)
        old_ratios = torch.tensor(old_ratios, dtype=torch.float32)
        actions = torch.tensor(actions, dtype=torch.float32)

        returns, cost_returns = self.compute_returns(rewards, costs, dones)
        returns = (returns - returns.mean()) / (returns.std() + 1e-6)

        for _ in range(5):
            new_ratios = self.actor(states).squeeze(1)
            ratio = new_ratios / (old_ratios + 1e-6)
            surr_reward = ratio * returns
            surr_cost = ratio * cost_returns

            lagrangian_loss = -(surr_reward - self.lambda_param * surr_cost)
            clipped = torch.clamp(ratio, 1 - self.clip_eps, 1 + self.clip_eps)
            clipped_loss = -(clipped * returns - self.lambda_param * clipped * cost_returns)
            loss = torch.min(lagrangian_loss, clipped_loss).mean()

            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

        # 更新 Lagrangian multiplier
        mean_cost = cost_returns.mean()
        lambda_loss = -self.lambda_param * (mean_cost - self.cost_limit)
        self.lambda_optimizer.zero_grad()
        lambda_loss.backward()
        self.lambda_optimizer.step()

    def save(self, path):
        torch.save({
            "actor_state": self.actor.state_dict(),
            "lambda": self.lambda_param.detach().item()
        }, path)

    def load(self, path):
        data = torch.load(path)
        self.actor.load_state_dict(data["actor_state"])
        self.lambda_param = torch.tensor(data["lambda"], requires_grad=True)
        self.lambda_optimizer = optim.Adam([self.lambda_param], lr=1e-2)


if __name__ == '__main__':
    agent = LagrangianPPOAgent(input_dim=20, cost_limit=0.05)
    dummy_state = np.random.rand(20)
    bid, ratio = agent.select_action(dummy_state)
    print(f"Bid: {bid:.2f} (ratio: {ratio:.3f}), λ = {agent.lambda_param.item():.3f}")

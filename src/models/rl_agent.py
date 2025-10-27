import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import os
from collections import deque
import random


class Actor(nn.Module):
    def __init__(self, input_dim, hidden_dim=128):
        super(Actor, self).__init__()
        self.fc = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()  # 输出 bid 比例（0~1），乘以 max_bid 即为最终 bid
        )

    def forward(self, x):
        return self.fc(x)


class PPOAgent:
    def __init__(self, input_dim, max_bid=10.0, gamma=0.99, clip_epsilon=0.2, lr=3e-4):
        self.actor = Actor(input_dim)
        self.optimizer = optim.Adam(self.actor.parameters(), lr=lr)
        self.gamma = gamma
        self.clip_epsilon = clip_epsilon
        self.max_bid = max_bid

    def select_action(self, state):
        state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)  # shape: (1, input_dim)
        with torch.no_grad():
            bid_ratio = self.actor(state_tensor).item()  # 输出 bid 比例
        bid_price = bid_ratio * self.max_bid
        return bid_price, bid_ratio

    def compute_returns(self, rewards, dones):
        R = 0
        returns = []
        for r, done in zip(reversed(rewards), reversed(dones)):
            if done:
                R = 0
            R = r + self.gamma * R
            returns.insert(0, R)
        return torch.tensor(returns, dtype=torch.float32)

    def update(self, states, old_ratios, actions, returns):
        states_array = np.array(states)
        ratios_array = np.array(old_ratios)
        actions_array = np.array(actions)
        returns_array = np.array(returns)

        states = torch.FloatTensor(states_array)
        old_ratios = torch.FloatTensor(ratios_array)
        actions = torch.FloatTensor(actions_array)
        returns = torch.FloatTensor(returns_array)

        # Normalize returns
        returns = (returns - returns.mean()) / (returns.std() + 1e-6)

        for _ in range(5):  # K epochs
            new_ratios = self.actor(states).squeeze(1)
            ratio = new_ratios / (old_ratios + 1e-6)
            surr1 = ratio * returns
            surr2 = torch.clamp(ratio, 1 - self.clip_epsilon, 1 + self.clip_epsilon) * returns
            loss = -torch.min(surr1, surr2).mean()

            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

    def save(self, path):
        torch.save(self.actor.state_dict(), path)

    def load(self, path):
        self.actor.load_state_dict(torch.load(path))
        self.actor.eval()


if __name__ == '__main__':
    # 简单测试（仅结构验证）
    agent = PPOAgent(input_dim=20)
    dummy_state = np.random.rand(20)
    bid_price, bid_ratio = agent.select_action(dummy_state)
    print(f"Sampled bid: {bid_price:.2f} (ratio: {bid_ratio:.4f})")

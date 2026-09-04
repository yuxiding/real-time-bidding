"""Value-based baselines, disjoint LinUCB and Stable-Baselines3 PPO."""
from pathlib import Path
import numpy as np
from .environment import MULTIPLIERS


class ValuePolicy:
    def __init__(self, multiplier=1.):
        self.multiplier = multiplier

    def bid(self, observation, conversion_value):
        return float(self.multiplier * observation[0] * observation[1] * conversion_value)


class ConstantPolicy:
    def __init__(self, amount=1.):
        self.amount = amount

    def bid(self, observation, conversion_value):
        return self.amount


class LinUCBAgent:
    """Separate linear reward model per action; evaluate with updates disabled."""
    def __init__(self, alpha=.2, seed=42):
        self.alpha = alpha
        self.rng = np.random.default_rng(seed)
        self.inverse = np.repeat(np.eye(7)[None, :, :], len(MULTIPLIERS), axis=0)
        self.b = np.zeros((len(MULTIPLIERS), 7))

    def select_action(self, observation, explore=False):
        x = np.r_[1., observation]
        theta = np.einsum("aij,aj->ai", self.inverse, self.b)
        means = theta @ x
        if explore:
            uncertainty = np.sqrt(np.maximum(0., np.einsum("i,aij,j->a", x, self.inverse, x)))
            means = means + self.alpha * uncertainty
        candidates = np.flatnonzero(np.isclose(means, means.max(), rtol=0, atol=1e-12))
        return int(self.rng.choice(candidates)) if explore else int(candidates[0])

    def update(self, observation, action, reward):
        x = np.r_[1., observation]
        projected = self.inverse[action] @ x
        self.inverse[action] -= np.outer(projected, projected) / (1 + x @ projected)
        self.b[action] += reward * x

    def bid(self, observation, conversion_value):
        action = self.select_action(observation)
        return float(MULTIPLIERS[action] * observation[0] * observation[1] * conversion_value)


def train_bandit(env, seed=42, episodes=20):
    agent = LinUCBAgent(seed=seed)
    for episode in range(episodes):
        obs, _ = env.reset(seed=seed + episode)
        done = False
        while not done:
            action = agent.select_action(obs, explore=True)
            next_obs, reward, done, _, _ = env.step(action)
            agent.update(obs, action, reward)
            obs = next_obs
    return agent


class PPOAgent:
    """Delegate PPO probability ratios, advantages and optimization to SB3."""
    def __init__(self, model):
        self.model = model

    @classmethod
    def train(cls, env, seed=42, timesteps=30000):
        import torch
        from stable_baselines3 import PPO
        torch.set_num_threads(1)
        model = PPO("MlpPolicy", env, seed=seed, device="cpu", n_steps=512,
                    batch_size=64, n_epochs=5, learning_rate=3e-4, ent_coef=.01,
                    policy_kwargs={"net_arch": [32, 32]}, verbose=0)
        model.learn(total_timesteps=timesteps)
        return cls(model)

    def bid(self, observation, conversion_value):
        action, _ = self.model.predict(observation, deterministic=True)
        return float(MULTIPLIERS[int(action)] * observation[0] * observation[1] * conversion_value)

    def save(self, path):
        self.model.save(path)

    @classmethod
    def load(cls, path):
        from stable_baselines3 import PPO
        if not Path(path).is_file():
            raise FileNotFoundError(f"Missing PPO checkpoint: {path}. Run aurorabid reproduce.")
        return cls(PPO.load(path, device="cpu"))

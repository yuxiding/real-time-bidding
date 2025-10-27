import numpy as np

class LinUCBAgent:
    """
    基于 LinUCB 的 Contextual Bandit 策略。
    """
    def __init__(self, input_dim: int, alpha: float = 0.5, max_bid: float = 10.0):
        self.d = input_dim
        self.alpha = alpha
        self.max_bid = max_bid

        self.A = np.identity(self.d)
        self.b = np.zeros((self.d, 1))

    def select_action(self, context: np.ndarray) -> float:
        context = context.reshape(-1, 1)
        A_inv = np.linalg.inv(self.A)
        theta = A_inv @ self.b
        p = (theta.T @ context + self.alpha * np.sqrt(context.T @ A_inv @ context)).item()
        bid = np.clip(p, 0, 1) * self.max_bid
        return bid

    def update(self, context: np.ndarray, reward: float):
        context = context.reshape(-1, 1)
        self.A += context @ context.T
        self.b += reward * context


if __name__ == '__main__':
    input_dim = 26
    agent = LinUCBAgent(input_dim=input_dim, alpha=0.5, max_bid=5.0)

    for step in range(10):
        ctx = np.random.rand(input_dim)
        bid = agent.select_action(ctx)
        reward = np.random.rand() if bid > 2 else 0  # mock reward
        agent.update(ctx, reward)
        print(f"Step {step+1}: Bid = {bid:.2f}, Reward = {reward:.2f}")

import numpy as np
import pickle


class BidSimulator:
    """
    基于 Bid Landscape 进行市场出价模拟（采样竞争者报价）。
    """
    def __init__(self, landscape_path: str, n_competitors: int = 5):
        self.model = self._load_model(landscape_path)
        self.n_competitors = n_competitors

    def _load_model(self, path):
        with open(path, 'rb') as f:
            return pickle.load(f)

    def sample_market_price(self) -> float:
        samples = self.model.sample(self.n_competitors)
        return float(np.max(samples))  # 模拟 winner 的出价


if __name__ == '__main__':
    sim = BidSimulator("artifacts/bid_landscape.pkl")
    print([sim.sample_market_price() for _ in range(10)])

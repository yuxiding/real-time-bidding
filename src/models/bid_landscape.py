import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import pickle
from sklearn.neighbors import KernelDensity


class BidLandscapeModel:
    """
    基于历史 win_price 拟合市场价格分布的 Bid Landscape 模型
    支持 KDE 拟合与随机采样，用于仿真环境中生成对手出价。
    """
    def __init__(self, bandwidth: float = 0.5):
        self.bandwidth = bandwidth
        self.model = KernelDensity(kernel='gaussian', bandwidth=bandwidth)
        self.fitted = False

    def fit(self, win_prices: np.ndarray):
        filtered = win_prices[win_prices > 0].reshape(-1, 1)
        self.model.fit(filtered)
        self.fitted = True

    def sample(self, n_samples: int = 10) -> np.ndarray:
        assert self.fitted, "Model not fitted. Please call `fit()` first."
        samples = self.model.sample(n_samples)
        return np.maximum(0, samples.flatten())

    def save(self, path: str):
        with open(path, 'wb') as f:
            pickle.dump(self.model, f)

    def load(self, path: str):
        with open(path, 'rb') as f:
            self.model = pickle.load(f)
        self.fitted = True

    def plot_distribution(self, win_prices: np.ndarray, output_path: str = None):
        filtered = win_prices[win_prices > 0].reshape(-1, 1)
        x = np.linspace(0, np.percentile(filtered, 98), 1000).reshape(-1, 1)
        log_dens = self.model.score_samples(x)
        dens = np.exp(log_dens)

        plt.figure(figsize=(8, 4))
        plt.plot(x[:, 0], dens, label='KDE')
        plt.hist(filtered, bins=50, density=True, alpha=0.4, label='Histogram')
        plt.title("Bid Landscape Distribution")
        plt.xlabel("Win Price")
        plt.ylabel("Density")
        plt.legend()
        if output_path:
            plt.savefig(output_path)
        else:
            plt.show()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to impressions.csv")
    parser.add_argument("--output", default="bid_landscape.pkl", help="Model output path")
    parser.add_argument("--plot", default=None, help="Optional path to save plot")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    assert "win_price" in df.columns, "Missing win_price column"

    model = BidLandscapeModel(bandwidth=0.5)
    model.fit(df["win_price"].values)
    model.save(args.output)
    print(f"Bid landscape model saved to {args.output}")

    if args.plot:
        model.plot_distribution(df["win_price"].values, output_path=args.plot)
        print(f"Plot saved to {args.plot}")

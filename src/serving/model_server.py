import os
import torch
from src.models.ctr_model import CTRModel
from src.models.cvr_model import CVREstimator
from src.models.bandit_agent import LinUCBAgent
from src.models.rl_agent import PPOAgent


class ModelServer:
    def __init__(self, checkpoint_dir="checkpoints"):
        self.checkpoint_dir = checkpoint_dir
        self.models = {}
        self.load_all()

    def load_all(self):
        self.models["ctr"] = CTRModel(input_dim=26)
        self.models["cvr"] = CVREstimator(input_dim=26)
        self.models["bandit"] = LinUCBAgent(input_dim=26, alpha=0.3, max_bid=5.0)
        self.models["rl"] = PPOAgent(input_dim=26, max_bid=5.0)

        for name, model in self.models.items():
            ckpt_path = os.path.join(self.checkpoint_dir, f"{name}_model.pt") if name in ["ctr", "cvr"] else os.path.join(self.checkpoint_dir, f"{name}.pt")
            if os.path.exists(ckpt_path):
                model.load(ckpt_path)

    def get(self, name):
        return self.models.get(name, None)

    def get_all(self):
        return self.models


if __name__ == '__main__':
    ms = ModelServer()
    print("Loaded models:", list(ms.get_all().keys()))

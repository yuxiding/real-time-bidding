import os
import json
import random
import numpy as np
import torch
import yaml

def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def load_json(path: str):
    with open(path, 'r') as f:
        return json.load(f)

def save_json(obj: dict, path: str):
    with open(path, 'w') as f:
        json.dump(obj, f, indent=2)

def load_yaml(path: str):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def save_yaml(obj: dict, path: str):
    with open(path, 'w') as f:
        yaml.safe_dump(obj, f)

def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

def load_checkpoint(checkpoint_path: str):
    """
    加载训练好的模型
    
    参数:
        checkpoint_path: 模型文件路径
    
    返回:
        PPOAgent: 加载了权重的agent对象
    """
    from src.models.rl_agent import PPOAgent
    
    # 创建agent实例（需要指定正确的输入维度）
    agent = PPOAgent(input_dim=26, max_bid=10.0)  # 根据您的特征维度调整
    
    # 加载权重
    agent.load(checkpoint_path)
    
    return agent

if __name__ == '__main__':
    set_seed(2024)
    ensure_dir("outputs")
    save_json({"a": 1}, "outputs/sample.json")
    print(load_json("outputs/sample.json"))

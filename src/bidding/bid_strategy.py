from typing import Dict
import numpy as np


def compute_ecpm(pctr: float, pcvr: float, value: float) -> float:
    """
    eCPM = pCTR * pCVR * ConversionValue
    """
    return pctr * pcvr * value


def rule_based_bid(pctr: float, pcvr: float, value: float, max_bid: float = 10.0) -> float:
    ecpm = compute_ecpm(pctr, pcvr, value)
    bid = min(ecpm, max_bid)
    return bid


class BidStrategyWrapper:
    """
    出价策略封装器，统一接口支持三种策略：
    - Rule-based
    - Contextual Bandit（如 LinUCB）
    - Reinforcement Learning（如 PPO/DDPG）

    输入：特征字典（feature_dict）
    输出：实际出价金额（float）
    """
    def __init__(self, strategy_type: str, model_dict: Dict):
        """
        参数：
        - strategy_type: 'rule' | 'bandit' | 'rl'
        - model_dict:
            - 'ctr': 训练好的 CTR 模型对象，需实现 predict(X)
            - 'cvr': 训练好的 CVR 模型对象，需实现 predict(X)
            - 'bandit': 上下文 Bandit agent，需实现 select_action(context)
            - 'rl': 强化学习 agent，需实现 select_action(state) 返回 (bid, ratio)
            - 'max_bid': 出价上限（float）
        """
        self.strategy_type = strategy_type
        self.model_dict = model_dict

    def bid(self, feature_dict: Dict) -> float:
        ctr_model = self.model_dict.get("ctr")
        cvr_model = self.model_dict.get("cvr")
        bandit_agent = self.model_dict.get("bandit")
        rl_agent = self.model_dict.get("rl")
        max_bid = self.model_dict.get("max_bid", 10.0)

        # 特征向量（batch_size=1）
        features = list(feature_dict.values())
        X = [features]  # shape: (1, dim)

        # 模型预测 CTR / CVR
        pctr = float(ctr_model.predict(X)[0]) if ctr_model else 0.01
        pcvr = float(cvr_model.predict(X)[0]) if cvr_model else 0.01

        # 价值（默认转化为 50 元）
        value = feature_dict.get("conv_value", 50.0)

        # 策略分发
        if self.strategy_type == 'rule':
            bid = rule_based_bid(pctr, pcvr, value, max_bid)
            return bid

        elif self.strategy_type == 'bandit':
            if not bandit_agent:
                raise ValueError("No bandit agent provided.")
            context_vec = np.array(features)
            return bandit_agent.select_action(context_vec)

        elif self.strategy_type == 'rl':
            if not rl_agent:
                raise ValueError("No RL agent provided.")
            state_vec = np.array(features)
            bid, _ = rl_agent.select_action(state_vec)
            return bid

        else:
            raise ValueError(f"Unsupported strategy type: {self.strategy_type}")

import pandas as pd
import os
import json
from typing import Dict, Optional

# Optional: you can add redis or kafka imports here
# import redis
# from kafka import KafkaProducer, KafkaConsumer

class LocalFeatureStore:
    """
    本地模拟的特征存储系统。
    用于仿真环境下快速加载用户特征、上下文特征、行为特征。
    """

    def __init__(self, base_path: str):
        """
        参数：
            base_path: 特征文件所在目录
        """
        self.base_path = base_path
        self.user_feature_path = os.path.join(base_path, "user_embeddings.csv")
        self.context_feature_path = os.path.join(base_path, "context_features.csv")
        self.history_feature_path = os.path.join(base_path, "history_features.csv")

        self.user_df = None
        self.context_df = None
        self.history_df = None

    def load(self):
        self.user_df = pd.read_csv(self.user_feature_path)
        self.context_df = pd.read_csv(self.context_feature_path)
        self.history_df = pd.read_csv(self.history_feature_path)

    def get_user_features(self, user_id: str) -> Optional[Dict]:
        row = self.user_df[self.user_df.user_id == user_id]
        if row.empty:
            return None
        return row.drop(columns=["user_id"]).iloc[0].to_dict()

    def get_context_features(self, adslot_id: str) -> Optional[Dict]:
        row = self.context_df[self.context_df.adslot_id == adslot_id]
        if row.empty:
            return None
        return row.drop(columns=["adslot_id"]).iloc[0].to_dict()

    def get_history_features(self, request_id: str) -> Optional[Dict]:
        row = self.history_df[self.history_df.request_id == request_id]
        if row.empty:
            return None
        return row.drop(columns=["request_id", "user_id"]).iloc[0].to_dict()

    def get_combined_feature(self, user_id: str, adslot_id: str, request_id: str) -> Optional[Dict]:
        u = self.get_user_features(user_id)
        c = self.get_context_features(adslot_id)
        h = self.get_history_features(request_id)
        if u is None or c is None or h is None:
            return None
        return {**u, **c, **h}


if __name__ == "__main__":
    fs = LocalFeatureStore(base_path="data/processed")
    fs.load()
    features = fs.get_combined_feature(user_id="u1234", adslot_id="s01", request_id="req000001")
    print(json.dumps(features, indent=2))

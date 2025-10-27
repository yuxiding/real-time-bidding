import pandas as pd
import numpy as np
import hashlib
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline


class UserFeatureEngineer:
    """
    用于生成用户画像 embedding 和编码的特征工程模块。
    支持分类特征 label encoding + 连续特征标准化 + PCA 降维（可选）。
    """

    def __init__(self, n_components: int = 3):
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=n_components)
        self.pipeline = None

    def load_user_data(self, filepath: str) -> pd.DataFrame:
        df = pd.read_csv(filepath)
        expected_cols = {"user_id", "age", "gender", "segment"}
        assert expected_cols.issubset(set(df.columns)), f"Missing columns in user file: {expected_cols - set(df.columns)}"
        return df

    def _hash_uid(self, uid: str) -> int:
        # 哈希用户 ID 到整数
        return int(hashlib.sha256(uid.encode('utf-8')).hexdigest(), 16) % (10 ** 8)

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # Step 1: 用户 ID 哈希编码
        df["uid_hash"] = df["user_id"].apply(self._hash_uid)

        # Step 2: 类别特征编码（性别、用户类型）
        # onehot encoding
        cat_cols = ["gender", "segment"]
        for col in cat_cols:
            le = LabelEncoder()
            df[f"{col}_enc"] = le.fit_transform(df[col])
            self.label_encoders[col] = le

        # Step 3: 连续特征 + 类别编码拼接
        # x = [34, 0, 1, 0, 0, 0 , 0, 0,  1]
        # x_norm = x / np.linalg.norm(x) -> [0.23, 0, 0.003, 0,0,0,0,0, 0.01] -> pca -> [0.5, 0.1, 0.2]
        feature_cols = ["age"] + [f"{col}_enc" for col in cat_cols]
        X = df[feature_cols].values

        # Step 4: 构造 pipeline（标准化 + PCA 降维）
        self.pipeline = Pipeline([
            ("scaler", self.scaler),
            ("pca", self.pca)
        ])
        embedding = self.pipeline.fit_transform(X)

        # Step 5: 拼接输出
        for i in range(embedding.shape[1]):
            df[f"user_emb_{i+1}"] = embedding[:, i]

        return df[["user_id"] + [f"user_emb_{i+1}" for i in range(embedding.shape[1])]]

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["uid_hash"] = df["user_id"].apply(self._hash_uid)

        # 类别特征编码
        for col in ["gender", "segment"]:
            le = self.label_encoders[col]
            df[f"{col}_enc"] = le.transform(df[col])

        # 数值特征 + 编码拼接
        feature_cols = ["age"] + [f"{col}_enc" for col in ["gender", "segment"]]
        X = df[feature_cols].values
        embedding = self.pipeline.transform(X)

        for i in range(embedding.shape[1]):
            df[f"user_emb_{i+1}"] = embedding[:, i]

        return df[["user_id"] + [f"user_emb_{i+1}" for i in range(embedding.shape[1])]]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True, help="Path to users.csv")
    parser.add_argument("--output", type=str, required=True, help="Path to save user embeddings")
    parser.add_argument("--n_components", type=int, default=3, help="Number of PCA dimensions")
    args = parser.parse_args()

    engine = UserFeatureEngineer(n_components=args.n_components)
    df_users = engine.load_user_data(args.input)
    df_embed = engine.fit_transform(df_users)
    df_embed.to_csv(args.output, index=False)
    print(f"Saved user embedding to {args.output}")

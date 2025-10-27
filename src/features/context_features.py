import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
import numpy as np
import os

class ContextFeatureEngineer:
    """
    将广告上下文（时间、地理位置、设备、媒体、广告位）编码为特征，支持 OneHot + label 编码组合。
    """
    def __init__(self):
        self.label_encoders = {}
        self.onehot_encoder = None

    def load_context_data(self, filepath: str) -> pd.DataFrame:
        df = pd.read_csv(filepath)
        expected_cols = {"adslot_id", "media", "device", "os", "geo", "hour"}
        assert expected_cols.issubset(set(df.columns)), f"Missing columns: {expected_cols - set(df.columns)}"
        return df

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # Label encode adslot_id（用于广告位ID）
        le_adslot = LabelEncoder()
        df["adslot_enc"] = le_adslot.fit_transform(df["adslot_id"])
        self.label_encoders["adslot_id"] = le_adslot

        # One-hot encode 其他类别字段（媒体/设备/系统/地域/小时）
        onehot_cols = ["media", "device", "os", "geo", "hour"]
        self.onehot_encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
        onehot_matrix = self.onehot_encoder.fit_transform(df[onehot_cols])
        onehot_feature_names = self.onehot_encoder.get_feature_names_out(onehot_cols)

        onehot_df = pd.DataFrame(onehot_matrix, columns=onehot_feature_names)
        onehot_df.index = df.index

        # 拼接最终结果
        final_df = pd.concat([df[["adslot_id", "adslot_enc"]], onehot_df], axis=1)
        return final_df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["adslot_enc"] = self.label_encoders["adslot_id"].transform(df["adslot_id"])

        onehot_cols = ["media", "device", "os", "geo", "hour"]
        onehot_matrix = self.onehot_encoder.transform(df[onehot_cols])
        onehot_feature_names = self.onehot_encoder.get_feature_names_out(onehot_cols)

        onehot_df = pd.DataFrame(onehot_matrix, columns=onehot_feature_names)
        onehot_df.index = df.index

        final_df = pd.concat([df[["adslot_id", "adslot_enc"]], onehot_df], axis=1)
        return final_df


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True, help="Path to context.csv")
    parser.add_argument("--output", type=str, required=True, help="Path to save encoded context features")
    args = parser.parse_args()

    engine = ContextFeatureEngineer()
    df_ctx = engine.load_context_data(args.input)
    df_encoded = engine.fit_transform(df_ctx)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    df_encoded.to_csv(args.output, index=False)
    print(f"Saved context features to {args.output}")

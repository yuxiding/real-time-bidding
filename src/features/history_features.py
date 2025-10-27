import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

class HistoryFeatureEngineer:
    """
    根据曝光/点击日志，为每个用户构造行为序列特征：
    - 最近N次点击时间间隔
    - 点击频率统计（单位时间内）
    - 行为计数（曝光次数、点击次数、转化次数）
    """
    def __init__(self, max_history=5, time_window_minutes=60):
        self.max_history = max_history
        self.time_window = timedelta(minutes=time_window_minutes)

    def load_logs(self, impression_fp, click_fp, conversion_fp):
        imp = pd.read_csv(impression_fp, parse_dates=['timestamp'])
        clk = pd.read_csv(click_fp, parse_dates=['click_timestamp'])
        conv = pd.read_csv(conversion_fp, parse_dates=['conv_timestamp'])
        return imp, clk, conv

    def generate(self, impressions, clicks, conversions) -> pd.DataFrame:
        impressions = impressions.copy()

        # 加入点击标记
        impressions["clicked"] = impressions["request_id"].isin(clicks["request_id"])
        impressions["converted"] = impressions["request_id"].isin(conversions["request_id"])

        # 排序准备构造行为序列
        impressions.sort_values(by=["user_id", "timestamp"], inplace=True)

        features = []

        for uid, user_df in impressions.groupby("user_id"):
            user_df = user_df.reset_index(drop=True)
            history_clicks = []
            for i, row in user_df.iterrows():
                current_time = row["timestamp"]

                # 过滤过去点击行为（时间在当前之前）
                recent_clicks = [t for t in history_clicks if t < current_time]
                recent_clicks = sorted(recent_clicks)[-self.max_history:]

                # 构造特征
                if recent_clicks:
                    intervals = [(current_time - t).total_seconds() for t in recent_clicks]
                    avg_interval = np.mean(intervals)
                    last_click_gap = intervals[-1]
                else:
                    avg_interval = -1
                    last_click_gap = -1

                time_window_start = current_time - self.time_window
                n_clicks_in_window = sum(1 for t in recent_clicks if t >= time_window_start)

                features.append({
                    "request_id": row["request_id"],
                    "user_id": uid,
                    "exp_count": i + 1,
                    "click_count": sum(user_df.loc[:i, "clicked"]),
                    "conv_count": sum(user_df.loc[:i, "converted"]),
                    "recent_clicks": len(recent_clicks),
                    "avg_click_interval": avg_interval,
                    "last_click_gap": last_click_gap,
                    "click_freq_last_hour": n_clicks_in_window
                })

                # 如果本次点击，加入点击历史中
                if row["clicked"]:
                    history_clicks.append(current_time)

        feature_df = pd.DataFrame(features)
        return feature_df


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--impression", required=True, help="Path to impressions.csv")
    parser.add_argument("--click", required=True, help="Path to clicks.csv")
    parser.add_argument("--conversion", required=True, help="Path to conversions.csv")
    parser.add_argument("--output", required=True, help="Path to save history features")
    parser.add_argument("--max_history", type=int, default=5, help="Max recent clicks to consider")
    parser.add_argument("--window", type=int, default=60, help="Time window in minutes")
    args = parser.parse_args()

    engine = HistoryFeatureEngineer(max_history=args.max_history, time_window_minutes=args.window)
    imp, clk, conv = engine.load_logs(args.impression, args.click, args.conversion)
    df_hist = engine.generate(imp, clk, conv)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    df_hist.to_csv(args.output, index=False)
    print(f"Saved history features to {args.output}")

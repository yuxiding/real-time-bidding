#!/usr/bin/env python3
"""
创建CTR训练数据
将特征文件和点击数据合并，生成用于训练CTR模型的数据
"""

import pandas as pd
import numpy as np
import os

def create_ctr_training_data():
    """创建CTR训练数据"""
    
    # 1. 加载特征文件
    user_features = pd.read_csv("data/processed/user_embeddings.csv")
    context_features = pd.read_csv("data/processed/context_features.csv")
    history_features = pd.read_csv("data/processed/history_features.csv")
    
    # 2. 加载原始数据
    clicks = pd.read_csv("data/raw/clicks.csv")
    impressions = pd.read_csv("data/raw/impressions.csv")
    
    # 3. 为历史特征添加adslot_id
    # 从impressions.csv获取request_id对应的adslot_id
    imp_mapping = impressions[['request_id', 'adslot_id']].set_index('request_id')['adslot_id']
    history_features['adslot_id'] = history_features['request_id'].map(imp_mapping)
    
    # 4. 合并特征
    
    # 首先合并历史特征和上下文特征（基于adslot_id）
    merged_features = history_features.merge(
        context_features, 
        on='adslot_id', 
        how='left'
    )
    
    # 然后合并用户特征（基于user_id）
    merged_features = merged_features.merge(
        user_features, 
        on='user_id', 
        how='left'
    )
    
    # 5. 添加点击标签
    merged_features['clicked'] = merged_features['request_id'].isin(clicks['request_id']).astype(int)
    
    # 6. 处理缺失值
    # 填充数值型特征的缺失值
    numeric_columns = merged_features.select_dtypes(include=[np.number]).columns
    merged_features[numeric_columns] = merged_features[numeric_columns].fillna(0)
    
    # 7. 选择特征列
    # 排除非特征列
    exclude_cols = ['request_id', 'user_id', 'adslot_id', 'clicked']
    feature_cols = [col for col in merged_features.columns if col not in exclude_cols]
    
    
    # 8. 保存训练数据
    output_file = "data/processed/ctr_training_data.csv"
    merged_features[feature_cols + ['clicked']].to_csv(output_file, index=False)
    
    print(f"CTR训练数据创建完成！")
    
    return output_file, len(feature_cols)

if __name__ == "__main__":
    output_file, feature_dim = create_ctr_training_data()
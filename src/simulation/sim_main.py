#!/usr/bin/env python3
"""
仿真主程序 - 完整的广告系统仿真
支持规则出价、Bandit、强化学习等多种策略

使用方法:
    python sim_main.py --strategy rule --max_bid 5.0 --budget 5000
    python sim_main.py --strategy bandit --max_bid 3.0 --budget 3000
    python sim_main.py --strategy rl --max_bid 10.0 --budget 10000
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os
import argparse

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.features.feature_store import LocalFeatureStore
from src.bidding.bid_strategy import BidStrategyWrapper
from src.bidding.budget_controller import BudgetController
from src.models.ctr_model import CTRModel
from src.models.cvr_model import CVREstimator
from src.models.bandit_agent import LinUCBAgent
from src.models.rl_agent import PPOAgent
from src.simulation.bid_simulator import BidSimulator
from src.simulation.auction_engine import SecondPriceAuction


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="AuroraBid 广告系统仿真程序",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
策略类型说明:
  rule     - 规则出价策略 (基于eCPM)
  bandit   - Contextual Bandit策略 (LinUCB算法)
  rl       - 强化学习策略 (PPO算法)

示例:
  python sim_main.py --strategy rule --max_bid 5.0 --budget 5000
  python sim_main.py --strategy bandit --max_bid 3.0 --budget 3000
  python sim_main.py --strategy rl --max_bid 10.0 --budget 8000
        """
    )
    
    parser.add_argument(
        '--strategy', '-s',
        type=str,
        choices=['rule', 'bandit', 'rl'],
        default='rule',
        help='选择出价策略 (默认: rule)'
    )
    
    parser.add_argument(
        '--max_bid', '-m',
        type=float,
        default=5.0,
        help='最大出价限制 (默认: 5.0)'
    )
    
    parser.add_argument(
        '--budget', '-b',
        type=float,
        default=5000.0,
        help='每日预算 (默认: 5000.0)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细输出'
    )
    
    parser.add_argument(
        '--evaluate', '-e',
        action='store_true',
        help='评估模式：运行多次仿真并计算统计指标'
    )
    
    parser.add_argument(
        '--runs', '-r',
        type=int,
        default=5,
        help='评估模式下的运行次数 (默认: 5)'
    )
    
    return parser.parse_args()


# ------------------------ Config ------------------------

def calculate_bandit_reward(bid_price, cost, clicked, value=50.0):
    """计算LinUCB训练的奖励函数"""
    if clicked:
        # 点击奖励：转化价值 - 成本
        reward = value - cost
    else:
        # 未点击惩罚：轻微负奖励
        reward = -cost * 0.1
    
    return reward


def run_simulation(args):
    """运行单次仿真"""
    try:
        # 初始化特征存储
        feature_store = LocalFeatureStore(base_path="data/processed")
        feature_store.load()
        
        # 加载预训练CTR和CVR模型
        ctr_model = CTRModel(input_dim=26)
        ctr_model.load("checkpoints/ctr_model.pt")
        cvr_model = CVREstimator(input_dim=26)
        cvr_model.load("checkpoints/cvr_model.pt")
        
        # 初始化智能体
        bandit_agent = LinUCBAgent(input_dim=26, alpha=0.3, max_bid=args.max_bid)
        
        # 尝试加载已训练的LinUCB模型
        if args.strategy == 'bandit':
            try:
                import pickle
                with open("checkpoints/bandit_agent.pkl", "rb") as f:
                    trained_bandit = pickle.load(f)
                    bandit_agent = trained_bandit
                    print("已加载训练好的LinUCB模型")
            except FileNotFoundError:
                print("LinUCB模型文件不存在，使用新初始化的模型")
            except Exception as e:
                print(f"LinUCB模型加载失败: {e}，使用新初始化的模型")
        
        # 加载预训练的RL智能体
        rl_agent = PPOAgent(input_dim=26, max_bid=args.max_bid)
        try:
            rl_agent.load("checkpoints/rl_agent.pt")
            print("已加载储存的RL智能体！")
        except FileNotFoundError:
            print("RL智能体模型文件不存在，使用随机初始化的模型")
        except Exception as e:
            print(f"RL智能体模型加载失败: {e}，使用随机初始化的模型")
        
        # 预算控制
        budget_control = BudgetController(
            daily_budget=args.budget,
            hourly_schedule={10: 0.1, 12: 0.3, 14: 0.5, 16: 0.7, 18: 0.9, 21: 1.0}
        )
        
        # 出价策略
        strategy = BidStrategyWrapper(
            strategy_type=args.strategy,
            model_dict={
                'ctr': ctr_model,
                'cvr': cvr_model,
                'bandit': bandit_agent,
                'rl': rl_agent,
                'max_bid': args.max_bid
            }
        )
        
        # 初始化市场模拟器和拍卖引擎
        try:
            bid_simulator = BidSimulator("artifacts/bid_landscape.pkl")
            print("已加载储存的市场模拟器")
        except FileNotFoundError:
            print("Bid Landscape文件不存在，使用默认市场模拟")
            bid_simulator = None
        
        auction_engine = SecondPriceAuction()
        
        # 加载数据
        imp_df = pd.read_csv("data/raw/impressions.csv", parse_dates=['timestamp'])
        clk_df = pd.read_csv("data/raw/clicks.csv")
        converted = set(clk_df.request_id.values)
        print(f"{len(imp_df)} 条曝光记录")
        
        print("开始仿真...")
        metrics = {
            "imps": 0, "clicks": 0, "cost": 0.0
        }
        
        # LinUCB训练统计
        bandit_training_stats = {
            "total_updates": 0,
            "avg_reward": 0.0,
            "rewards": [],
            "bids": []
        }
        
        for idx, row in imp_df.iterrows():
            if args.verbose and idx % 1000 == 0:
                print(f"   处理进度: {idx}/{len(imp_df)}")
                
            uid, slot, ts, req_id, floor = row["user_id"], row["adslot_id"], row["timestamp"], row["request_id"], row["floor_price"]
            
            if not budget_control.allow_bid(ts):
                continue
                
            feats = feature_store.get_combined_feature(user_id=uid, adslot_id=slot, request_id=req_id)
            if feats is None:
                continue
                
            bid_price = strategy.bid(feats)
            bid_price = budget_control.scale_bid(bid_price, ts)
            
            # 使用真实的市场模拟器
            if bid_simulator:
                # 模拟市场最高出价
                market_max_bid = bid_simulator.sample_market_price()
                
                # 执行第二价格拍卖
                if bid_price >= market_max_bid:
                    # 我们的出价获胜，支付第二高价
                    win_price = market_max_bid
                    clicked = req_id in converted
                    budget_control.update(cost=win_price, timestamp=ts)
                    
                    metrics["imps"] += 1
                    metrics["cost"] += win_price
                    if clicked:
                        metrics["clicks"] += 1
            else:
                market_price = floor + np.random.rand() * 2
                if bid_price >= market_price:
                    clicked = req_id in converted
                    budget_control.update(cost=market_price, timestamp=ts)
                    
                    metrics["imps"] += 1
                    metrics["cost"] += market_price
                    if clicked:
                        metrics["clicks"] += 1
        
        # 结果输出
        print("\n" + "=" * 50)
        ctr = metrics["clicks"] / metrics["imps"] if metrics["imps"] else 0
        cpm = metrics["cost"] / metrics["imps"] * 1000 if metrics["imps"] else 0
        
        print("仿真结束！")
        print(f"策略类型: {args.strategy}")
        print(f"预算: {args.budget}")
        print(f"最大出价: {args.max_bid}")
        print(f"曝光次数: {metrics['imps']}")
        print(f"点击次数: {metrics['clicks']}")
        print(f"点击率(CTR): {ctr:.4f}")
        print(f"总花费: {metrics['cost']:.2f}")
        print(f"千次曝光成本(CPM): {cpm:.2f}")
        
        # 如果启用详细输出，显示更多信息
        if args.verbose:
            print(f"\n详细统计:")
            print(f"预算使用率: {metrics['cost']/args.budget*100:.2f}%")
            print(f"平均点击成本: {metrics['cost']/metrics['clicks']:.2f}" if metrics['clicks'] > 0 else "平均点击成本: N/A")
            print(f"ROI: {(metrics['clicks']*50 - metrics['cost'])/metrics['cost']*100:.2f}%" if metrics['cost'] > 0 else "ROI: N/A")
        
        return metrics
        
    except Exception as e:
        print(f"仿真过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def evaluate_strategy(args):
    """评估模式：运行多次仿真并计算统计指标"""
    print(f"策略评估...")
    print(f"策略类型: {args.strategy}")
    print(f"最大出价: {args.max_bid}")
    print(f"预算: {args.budget}")
    print(f"评估次数: {args.runs}")
    print("=" * 50)
    
    all_metrics = []
    
    for run in range(args.runs):
        print(f"\n第 {run + 1}/{args.runs} 次仿真...")
        
        # 运行仿真
        metrics = run_simulation(args)
        if metrics:
            all_metrics.append(metrics)
            print(f"第 {run + 1} 次仿真完成")
        else:
            print(f"第 {run + 1} 次仿真失败")
    
    if not all_metrics:
        print("所有仿真都失败了")
        return
    
    # 计算统计指标
    print(f"\n评估结果统计 ({len(all_metrics)} 次运行):")
    print("=" * 50)
    
    # CTR统计
    ctrs = [m['clicks']/m['imps'] if m['imps'] > 0 else 0 for m in all_metrics]
    print(f"CTR 平均值: {np.mean(ctrs):.4f} ± {np.std(ctrs):.4f}")
    print(f"CTR 范围: [{min(ctrs):.4f}, {max(ctrs):.4f}]")
    
    # CPM统计
    cpms = [m['cost']/m['imps']*1000 if m['imps'] > 0 else 0 for m in all_metrics]
    print(f"CPM 平均值: {np.mean(cpms):.2f} ± {np.std(cpms):.2f}")
    print(f"CPM 范围: [{min(cpms):.2f}, {max(cpms):.2f}]")
    
    # 成本统计
    costs = [m['cost'] for m in all_metrics]
    print(f"总成本 平均值: {np.mean(costs):.2f} ± {np.std(costs):.2f}")
    
    # 点击统计
    clicks = [m['clicks'] for m in all_metrics]
    print(f"总点击 平均值: {np.mean(clicks):.1f} ± {np.std(clicks):.1f}")
    
    # ROI统计
    rois = []
    for m in all_metrics:
        if m['cost'] > 0:
            roi = (m['clicks'] * 50 - m['cost']) / m['cost'] * 100
            rois.append(roi)
    
    if rois:
        print(f"ROI 平均值: {np.mean(rois):.2f}% ± {np.std(rois):.2f}%")
        print(f"ROI 范围: [{min(rois):.2f}%, {max(rois):.2f}%]")
    
    print("=" * 50)
    print("策略评估完成！")


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    if args.evaluate:
        # 评估模式
        evaluate_strategy(args)
    else:
        # 单次仿真模式
        print("启动广告系统仿真...")
        print(f"策略类型: {args.strategy}")
        print(f"最大出价: {args.max_bid}")
        print(f"预算: {args.budget}")
        print("=" * 50)
        
        metrics = run_simulation(args)
        if metrics:
            print("仿真完成！")


if __name__ == "__main__":
    main()

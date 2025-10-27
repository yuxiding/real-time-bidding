import numpy as np

def compute_ctr(clicks: int, impressions: int) -> float:
    return clicks / impressions if impressions > 0 else 0.0

def compute_cvr(conversions: int, clicks: int) -> float:
    return conversions / clicks if clicks > 0 else 0.0

def compute_cpm(spend: float, impressions: int) -> float:
    return (spend / impressions) * 1000 if impressions > 0 else 0.0

def compute_gmv(conversions: int, unit_value: float = 50.0) -> float:
    return conversions * unit_value

def compute_roi(gmv: float, spend: float) -> float:
    return gmv / spend if spend > 0 else 0.0


def evaluate_policy(policy, env,episodes: int = 50):
    """
    评估策略的性能
    
    参数:
        policy: 策略对象（可以是RL agent或规则策略）
        episodes: 评估的episode数量
    
    返回:
        dict: 包含各种性能指标的字典
    """
    total_rewards = []
    total_costs = []
    total_clicks = []
    total_conversions = []
    win_rates = []
    
    for episode in range(episodes):
        # 重置环境
        obs, _ = env.reset()
        done = False
        episode_reward = 0
        episode_cost = 0
        episode_clicks = 0
        episode_conversions = 0
        episode_wins = 0
        episode_bids = 0
        
        while not done:
            # 策略选择动作
            if hasattr(policy, 'select_action'):
                # RL agent
                bid_price, ratio = policy.select_action(obs)
                action = [ratio]
            else:
                # 规则策略
                action = policy(obs)
            
            # 执行动作
            next_obs, reward, done, truncated, info = env.step(action)
            
            # 记录结果
            episode_reward += reward
            episode_cost += info.get('cost', 0)
            episode_clicks += int(info.get('clicked', False))
            episode_conversions += int(info.get('converted', False))
            episode_wins += int(info.get('cost', 0) > 0)
            episode_bids += 1
            
            obs = next_obs
        
        # 记录episode结果
        total_rewards.append(episode_reward)
        total_costs.append(episode_cost)
        total_clicks.append(episode_clicks)
        total_conversions.append(episode_conversions)
        win_rates.append(episode_wins / episode_bids if episode_bids > 0 else 0)
    
    # 计算统计指标
    metrics = {
        'avg_reward': np.mean(total_rewards),
        'std_reward': np.std(total_rewards),
        'avg_cost': np.mean(total_costs),
        'total_cost': np.sum(total_costs),
        'avg_clicks': np.mean(total_clicks),
        'total_clicks': np.sum(total_clicks),
        'avg_conversions': np.mean(total_conversions),
        'total_conversions': np.sum(total_conversions),
        'avg_win_rate': np.mean(win_rates),
        'avg_ctr': np.mean(total_clicks) / episodes,  # 假设每个episode有1个曝光
        'avg_cvr': np.sum(total_conversions) / np.sum(total_clicks) if np.sum(total_clicks) > 0 else 0,
        'roi': np.sum(total_conversions) * 50 / np.sum(total_costs) if np.sum(total_costs) > 0 else 0,  # 假设每次转化价值50元
    }
    
    return metrics




if __name__ == '__main__':
    clicks, imps, spend, conversions = 130, 10000, 340.0, 18
    print("CTR:", compute_ctr(clicks, imps))
    print("CVR:", compute_cvr(conversions, clicks))
    print("CPM:", compute_cpm(spend, imps))
    print("GMV:", compute_gmv(conversions))
    print("ROI:", compute_roi(compute_gmv(conversions), spend))

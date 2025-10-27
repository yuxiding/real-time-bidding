import datetime

class BudgetController:
    """
    根据预算分配策略动态控制投放节奏和预算消耗。
    - 支持：日预算、小时节奏控制、提前 burn out 预警。
    """
    def __init__(self, daily_budget: float, hourly_schedule: dict):
        """
        参数：
            daily_budget: 每日预算上限（单位：元）
            hourly_schedule: dict，如 {10: 0.1, 11: 0.2, ..., 20: 1.0}，表示每小时期望消耗比例累计
        """
        self.daily_budget = daily_budget
        self.hourly_schedule = hourly_schedule  # 必须是递增的累计占比（如 burn 20%, 40%, ..., 100%）
        self.reset()

    def reset(self):
        self.spend_so_far = 0.0
        self.impressions = 0
        self.current_hour = None

    def update(self, cost: float, timestamp: datetime.datetime):
        self.spend_so_far += cost
        self.impressions += 1
        self.current_hour = timestamp.hour

    def allow_bid(self, timestamp: datetime.datetime) -> bool:
        hour = timestamp.hour
        expected_ratio = self._expected_ratio(hour)
        expected_spend = expected_ratio * self.daily_budget
        return self.spend_so_far <= expected_spend

    def scale_bid(self, bid: float, timestamp: datetime.datetime) -> float:
        """
        如果当前花费超出节奏，自动降低出价比例；
        如果预算过多，提升；否则原价。
        """
        hour = timestamp.hour
        ratio = self._expected_ratio(hour)
        expected_spend = ratio * self.daily_budget
        if expected_spend == 0:
            return bid
        overshoot = self.spend_so_far / expected_spend
        if overshoot > 1.1:
            return bid * 0.5
        elif overshoot < 0.7:
            return min(bid * 1.2, 2 * bid)
        else:
            return bid

    def _expected_ratio(self, hour: int) -> float:
        keys = sorted(self.hourly_schedule.keys())
        for h in keys:
            if hour <= h:
                return self.hourly_schedule[h]
        return 1.0


if __name__ == '__main__':
    import datetime

    controller = BudgetController(
        daily_budget=1000,
        hourly_schedule={10: 0.1, 12: 0.3, 15: 0.6, 18: 0.85, 21: 1.0}
    )

    for t in range(100):
        ts = datetime.datetime(2025, 8, 20, 12)
        if controller.allow_bid(ts):
            bid = 3.5
            scaled = controller.scale_bid(bid, ts)
            controller.update(cost=scaled, timestamp=ts)
            print(f"Hour: {ts.hour}, Bid: {bid:.2f} → Scaled: {scaled:.2f}, Spend: {controller.spend_so_far:.2f}")

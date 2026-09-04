"""Second-price auction and hard spending limits, in currency per impression."""
from dataclasses import dataclass
import math


def clear_auction(bid, market_price, floor_price=0.):
    if any(not math.isfinite(v) or v < 0 for v in [bid, market_price, floor_price]):
        raise ValueError("Auction amounts must be finite and nonnegative.")
    threshold = max(market_price, floor_price)
    won = bid > 0 and bid >= threshold  # Ties favor our bidder in this simulator.
    return won, threshold if won else 0.


@dataclass
class BudgetController:
    budget: float
    max_bid: float
    spent: float = 0.

    def __post_init__(self):
        if any(not math.isfinite(x) or x < 0 for x in [self.budget, self.max_bid, self.spent]):
            raise ValueError("Budget and bid limits must be finite and nonnegative.")
        if self.spent > self.budget:
            raise ValueError("Spent amount exceeds budget.")

    @property
    def remaining(self):
        return max(0., self.budget - self.spent)

    def cap(self, bid):
        if not math.isfinite(bid):
            raise ValueError("Bid must be finite.")
        return max(0., min(float(bid), self.max_bid, self.remaining))

    def charge(self, cost):
        if not math.isfinite(cost) or cost < 0 or cost > self.remaining + 1e-9:
            raise ValueError("Settlement would violate the budget.")
        self.spent = min(self.budget, self.spent + cost)

from typing import List, Tuple


class SecondPriceAuction:
    """
    二价拍卖引擎（Second-Price Auction）
    接收：我方出价 + 若干市场竞争者报价
    返回：是否中标 + 清算价
    """
    def __init__(self):
        pass

    def execute(self, our_bid: float, competitor_bids: List[float]) -> Tuple[bool, float]:
        """
        参数：
            our_bid: 我方出价（float）
            competitor_bids: 竞争者出价列表（List[float]）
        返回：
            - 是否中标（bool）
            - 清算价（float）：如果中标则为第二高价，否则为0
        """
        all_bids = competitor_bids + [our_bid]
        all_bids_sorted = sorted(all_bids, reverse=True)
        winner = all_bids_sorted[0] == our_bid

        if winner:
            clear_price = all_bids_sorted[1]  # 第二高价
            return True, clear_price
        else:
            return False, 0.0


if __name__ == '__main__':
    engine = SecondPriceAuction()
    win, price = engine.execute(our_bid=3.8, competitor_bids=[2.5, 3.2, 3.6])
    print(f"✅ Win: {win}, Clear Price: {price:.2f}")

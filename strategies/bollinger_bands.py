"""
布林带策略

策略逻辑：
1. 计算中轨(SMA)和上下轨(中轨 ± N倍标准差)
2. 买入信号：价格触及下轨，认为超卖
3. 卖出信号：价格触及上轨，认为超买
"""
from collections import deque
from decimal import Decimal, ROUND_DOWN
from math import sqrt
from typing import Optional

from domain import KLine, Order, Side
from engine import StrategyBase, ITradingContext


class BollingerBandsStrategy(StrategyBase):
    """布林带策略"""

    def __init__(
        self,
        context: ITradingContext,
        period: int,
        num_std: Decimal,
        drawdown_rate: Optional[Decimal] = None,
        take_profit_rate: Optional[Decimal] = None
    ):
        super().__init__(context)

        if period <= 0:
            raise ValueError("Period must be positive")
        if num_std <= Decimal("0"):
            raise ValueError("num_std must be positive")

        self._period = period
        self._num_std = num_std
        self._drawdown_rate = drawdown_rate
        self._take_profit_rate = take_profit_rate

        self._price_wnd: deque[Decimal] = deque(maxlen=period)
        self._last_buy_order: Optional[Order] = None
        self._pending_signal: Optional[str] = None

        self._buy_count = 0
        self._sell_count = 0
        self._stop_loss_count = 0
        self._take_profit_count = 0

    @property
    def buy_count(self) -> int:
        return self._buy_count

    @property
    def sell_count(self) -> int:
        return self._sell_count

    @property
    def stop_loss_count(self) -> int:
        return self._stop_loss_count

    @property
    def take_profit_count(self) -> int:
        return self._take_profit_count

    def _on_order_executed(self, order: Order) -> None:
        if order.side == Side.Buy:
            self._last_buy_order = order
            self._buy_count += 1
        else:
            if self._pending_signal == "stop_loss":
                self._stop_loss_count += 1
            elif self._pending_signal == "take_profit":
                self._take_profit_count += 1
            self._sell_count += 1
            self._last_buy_order = None
            self._pending_signal = None

    def _calc_bands(self) -> tuple[Decimal, Decimal, Decimal]:
        prices = list(self._price_wnd)
        n = len(prices)
        mid = sum(prices, Decimal("0")) / Decimal(n)

        variance = sum(((p - mid) ** 2 for p in prices), Decimal("0")) / Decimal(n)
        std = Decimal(str(sqrt(float(variance))))

        upper = mid + self._num_std * std
        lower = mid - self._num_std * std
        return mid, upper, lower

    def _process_kline(self, kline: KLine) -> None:
        self._price_wnd.append(kline.close_price)

        if len(self._price_wnd) < self._period:
            return

        mid, upper, lower = self._calc_bands()
        current_price = kline.close_price

        base_balance, quote_balance = self.context.get_balance()

        if base_balance > Decimal("0"):
            self._handle_position(kline, base_balance, current_price, upper)
        else:
            self._handle_no_position(kline, quote_balance, current_price, lower)

    def _handle_position(self, kline: KLine, base_balance: Decimal, current_price: Decimal, upper: Decimal) -> None:
        if self._last_buy_order is not None and self._drawdown_rate is not None:
            price_change = (current_price - self._last_buy_order.price) / self._last_buy_order.price
            if price_change < -self._drawdown_rate:
                self._pending_signal = "stop_loss"
                self.context.sell(kline.open_time, current_price, base_balance)
                return

        if self._last_buy_order is not None and self._take_profit_rate is not None:
            price_change = (current_price - self._last_buy_order.price) / self._last_buy_order.price
            if price_change > self._take_profit_rate:
                self._pending_signal = "take_profit"
                self.context.sell(kline.open_time, current_price, base_balance)
                return

        if current_price >= upper:
            self._pending_signal = "signal"
            self.context.sell(kline.open_time, current_price, base_balance)

    def _handle_no_position(self, kline: KLine, quote_balance: Decimal, current_price: Decimal, lower: Decimal) -> None:
        if current_price <= lower:
            quantity = quote_balance / current_price
            quantity = quantity.quantize(Decimal("0.0000"), rounding=ROUND_DOWN)

            if quantity > Decimal("0"):
                self.context.buy(kline.open_time, current_price, quantity)

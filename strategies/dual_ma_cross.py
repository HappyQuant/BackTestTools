"""
双均线交叉策略

策略逻辑：
1. 计算短期均线(SMA_fast)和长期均线(SMA_slow)
2. 买入信号：短期均线上穿长期均线（金叉）
3. 卖出信号：短期均线下穿长期均线（死叉）
"""
from collections import deque
from decimal import Decimal, ROUND_DOWN
from typing import Optional

from domain import KLine, Order
from engine import StrategyBase, ITradingContext


class DualMACrossStrategy(StrategyBase):
    """双均线交叉策略"""

    def __init__(
        self,
        context: ITradingContext,
        fast_period: int,
        slow_period: int,
        drawdown_rate: Optional[Decimal] = None,
        take_profit_rate: Optional[Decimal] = None
    ):
        super().__init__(context)

        if fast_period <= 0 or slow_period <= 0:
            raise ValueError("Periods must be positive")
        if fast_period >= slow_period:
            raise ValueError("fast_period must be less than slow_period")

        self._fast_period = fast_period
        self._slow_period = slow_period
        self._drawdown_rate = drawdown_rate
        self._take_profit_rate = take_profit_rate

        self._fast_wnd: deque[Decimal] = deque(maxlen=fast_period)
        self._slow_wnd: deque[Decimal] = deque(maxlen=slow_period)
        self._last_buy_order: Optional[Order] = None
        self._prev_fast_above_slow: Optional[bool] = None

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

    def _process_kline(self, kline: KLine) -> None:
        self._fast_wnd.append(kline.close_price)
        self._slow_wnd.append(kline.close_price)

        if len(self._slow_wnd) < self._slow_period:
            return

        fast_avg = sum(self._fast_wnd) / Decimal(len(self._fast_wnd))
        slow_avg = sum(self._slow_wnd) / Decimal(len(self._slow_wnd))

        fast_above_slow = fast_avg > slow_avg

        if self._prev_fast_above_slow is None:
            self._prev_fast_above_slow = fast_above_slow
            return

        base_balance, quote_balance = self.context.get_balance()

        if base_balance > Decimal("0"):
            self._handle_position(kline, base_balance, fast_above_slow)
        else:
            self._handle_no_position(kline, quote_balance, fast_above_slow)

        self._prev_fast_above_slow = fast_above_slow

    def _handle_position(self, kline: KLine, base_balance: Decimal, fast_above_slow: bool) -> None:
        current_price = kline.close_price

        # 止损
        if self._last_buy_order is not None and self._drawdown_rate is not None:
            price_change = (current_price - self._last_buy_order.price) / self._last_buy_order.price
            if price_change < -self._drawdown_rate:
                self.context.sell(kline.open_time, current_price, base_balance)
                self._sell_count += 1
                self._stop_loss_count += 1
                self._last_buy_order = None
                return

        # 止盈
        if self._last_buy_order is not None and self._take_profit_rate is not None:
            price_change = (current_price - self._last_buy_order.price) / self._last_buy_order.price
            if price_change > self._take_profit_rate:
                self.context.sell(kline.open_time, current_price, base_balance)
                self._sell_count += 1
                self._take_profit_count += 1
                self._last_buy_order = None
                return

        # 死叉卖出
        if self._prev_fast_above_slow and not fast_above_slow:
            self.context.sell(kline.open_time, current_price, base_balance)
            self._sell_count += 1
            self._last_buy_order = None

    def _handle_no_position(self, kline: KLine, quote_balance: Decimal, fast_above_slow: bool) -> None:
        # 金叉买入
        if not self._prev_fast_above_slow and fast_above_slow:
            current_price = kline.close_price
            quantity = quote_balance / current_price
            quantity = quantity.quantize(Decimal("0.0000"), rounding=ROUND_DOWN)

            if quantity > Decimal("0"):
                order = self.context.buy(kline.open_time, current_price, quantity)
                self._last_buy_order = order
                self._buy_count += 1

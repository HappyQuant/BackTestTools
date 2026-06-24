"""
双均线趋势策略

策略逻辑：
1. 计算快均线(fast MA)和慢均线(slow MA)
2. 买入信号：快均线上穿慢均线(金叉) + 快均线斜率 ≥ 趋势强度阈值
3. 卖出信号：快均线下穿慢均线(死叉) / 止损 / 止盈
"""
from collections import deque
from decimal import Decimal, ROUND_DOWN
from typing import Optional

from domain import KLine, Order, Side
from engine import StrategyBase, ITradingContext


class MovingAverageTrendStrategy(StrategyBase):
    """双均线趋势策略"""

    def __init__(
        self,
        context: ITradingContext,
        fast_ma_period: int,
        slow_ma_period: int,
        trend_strength: Decimal,
        drawdown_rate: Decimal,
        take_profit_rate: Optional[Decimal] = None
    ):
        super().__init__(context)

        if fast_ma_period <= 0 or slow_ma_period <= 0:
            raise ValueError("MA periods must be positive")
        if fast_ma_period >= slow_ma_period:
            raise ValueError("Fast MA period must be less than slow MA period")

        self._fast_ma_period = fast_ma_period
        self._slow_ma_period = slow_ma_period
        self._trend_strength = trend_strength
        self._drawdown_rate = drawdown_rate
        self._take_profit_rate = take_profit_rate

        self._price_window: deque[Decimal] = deque(maxlen=slow_ma_period)
        self._last_buy_order: Optional[Order] = None
        self._prev_fast_ma: Optional[Decimal] = None
        self._prev_slow_ma: Optional[Decimal] = None

        self._buy_count = 0
        self._sell_count = 0
        self._stop_loss_count = 0
        self._take_profit_count = 0

    @property
    def fast_ma_period(self) -> int:
        return self._fast_ma_period

    @property
    def slow_ma_period(self) -> int:
        return self._slow_ma_period

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

    def _on_order_executed(self, order: Order, signal: Optional[str] = None) -> None:
        if order.side == Side.Buy:
            self._last_buy_order = order
            self._buy_count += 1
        else:
            if signal == "stop_loss":
                self._stop_loss_count += 1
            elif signal == "take_profit":
                self._take_profit_count += 1
            self._sell_count += 1
            self._last_buy_order = None

    def _calculate_ma(self, period: int) -> Optional[Decimal]:
        if len(self._price_window) < period:
            return None
        prices = list(self._price_window)[-period:]
        return sum(prices, Decimal("0")) / Decimal(period)

    def _process_kline(self, kline: KLine) -> None:
        self._price_window.append(kline.close_price)

        if len(self._price_window) < self._slow_ma_period:
            return

        fast_ma = self._calculate_ma(self._fast_ma_period)
        slow_ma = self._calculate_ma(self._slow_ma_period)

        if fast_ma is None or slow_ma is None:
            return

        self._execute_strategy(kline, fast_ma, slow_ma)

        self._prev_fast_ma = fast_ma
        self._prev_slow_ma = slow_ma

    def _execute_strategy(self, kline: KLine, fast_ma: Decimal, slow_ma: Decimal) -> None:
        base_balance, quote_balance = self.context.get_balance()

        if base_balance > Decimal("0"):
            self._handle_position(kline, base_balance, fast_ma, slow_ma)
        else:
            self._handle_no_position(kline, quote_balance, fast_ma, slow_ma)

    def _handle_position(self, kline: KLine, base_balance: Decimal, fast_ma: Decimal, slow_ma: Decimal) -> None:
        current_price = kline.close_price

        if self._last_buy_order is not None:
            price_change = (current_price - self._last_buy_order.price) / self._last_buy_order.price

            if price_change < -self._drawdown_rate:
                self.context.sell(kline.open_time, current_price, base_balance, signal="stop_loss")
                return

            if self._take_profit_rate is not None and price_change > self._take_profit_rate:
                self.context.sell(kline.open_time, current_price, base_balance, signal="take_profit")
                return

        if self._prev_fast_ma is not None and self._prev_slow_ma is not None:
            if self._prev_fast_ma > self._prev_slow_ma and fast_ma < slow_ma:
                self.context.sell(kline.open_time, current_price, base_balance, signal="signal")

    def _handle_no_position(self, kline: KLine, quote_balance: Decimal, fast_ma: Decimal, slow_ma: Decimal) -> None:
        current_price = kline.close_price

        if self._prev_fast_ma is None or self._prev_slow_ma is None:
            return

        if self._prev_fast_ma < self._prev_slow_ma and fast_ma > slow_ma:
            # 趋势强度确认：快均线斜率（上涨动量）
            if self._prev_fast_ma > Decimal("0"):
                fast_ma_slope = (fast_ma - self._prev_fast_ma) / self._prev_fast_ma
            else:
                fast_ma_slope = Decimal("0")

            if fast_ma_slope >= self._trend_strength:
                quantity = quote_balance / current_price
                quantity = quantity.quantize(Decimal("0.00001"), rounding=ROUND_DOWN)

                if quantity > Decimal("0"):
                    self.context.buy(kline.open_time, current_price, quantity)

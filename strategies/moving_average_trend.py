"""
移动平均线趋势策略

策略逻辑：
1. 计算K线收盘价的简单移动平均(SMA)
2. 买入信号：当前价格上穿均线，且均线处于上升趋势
3. 卖险信号检测：当前价格下穿均线，或触发止损/止盈
"""
from collections import deque
from decimal import Decimal, ROUND_DOWN
from typing import Optional

from domain import KLine, Order
from engine import StrategyBase, ITradingContext


class MovingAverageTrendStrategy(StrategyBase):
    """均线趋势策略"""

    def __init__(
        self,
        context: ITradingContext,
        kline_wnd_size: int,
        avg_wnd_size: int,
        buy_volatility_rate: Decimal,
        sell_volatility_rate: Decimal,
        drawdown_rate: Decimal,
        take_profit_rate: Optional[Decimal] = None
    ):
        super().__init__(context)

        if kline_wnd_size <= 0 or avg_wnd_size <= 0:
            raise ValueError("Window sizes must be positive")

        self._kline_wnd_size = kline_wnd_size
        self._avg_wnd_size = avg_wnd_size
        self._buy_volatility = buy_volatility_rate
        self._sell_volatility = sell_volatility_rate
        self._drawdown_rate = drawdown_rate
        self._take_profit_rate = take_profit_rate

        self._kline_wnd: deque[KLine] = deque(maxlen=kline_wnd_size)
        self._avg_wnd: deque[Decimal] = deque(maxlen=avg_wnd_size)
        self._last_buy_order: Optional[Order] = None
        self._last_avg: Optional[Decimal] = None

        # 统计信息
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
        self._kline_wnd.append(kline)

        if len(self._kline_wnd) < self._kline_wnd_size:
            return

        avg_price = sum(k.close_price for k in self._kline_wnd) / Decimal(self._kline_wnd_size)
        self._avg_wnd.append(avg_price)

        if len(self._avg_wnd) < self._avg_wnd_size:
            return

        self._execute_strategy(kline, avg_price)
        self._last_avg = avg_price

    def _execute_strategy(self, kline: KLine, avg_price: Decimal) -> None:
        base_balance, quote_balance = self.context.get_balance()

        if base_balance > Decimal("0"):
            self._handle_position(kline, base_balance, avg_price)
        else:
            self._handle_no_position(kline, quote_balance, avg_price)

    def _handle_position(self, kline: KLine, base_balance: Decimal, avg_price: Decimal) -> None:
        """持有仓位时的策略"""
        current_price = kline.close_price

        # 1. 止损检查
        if self._last_buy_order is not None:
            price_change = (current_price - self._last_buy_order.price) / self._last_buy_order.price

            # 止损
            if price_change < -self._drawdown_rate:
                self.context.sell(kline.open_time, current_price, base_balance)
                self._sell_count += 1
                self._stop_loss_count += 1
                self._last_buy_order = None
                return

            # 止盈
            if self._take_profit_rate is not None and price_change > self._take_profit_rate:
                self.context.sell(kline.open_time, current_price, base_balance)
                self._sell_count += 1
                self._take_profit_count += 1
                self._last_buy_order = None
                return

        # 2. 均线下穿信号 - 趋势转弱
        if len(self._avg_wnd) >= 2:
            avg_prev = self._avg_wnd[-2]
            avg_curr = self._avg_wnd[-1]

            # 均线下降且价格低于均线
            if avg_curr < avg_prev and current_price < avg_price:
                decline_rate = (avg_prev - avg_curr) / avg_prev if avg_prev > 0 else Decimal("0")
                if decline_rate >= self._sell_volatility:
                    self.context.sell(kline.open_time, current_price, base_balance)
                    self._sell_count += 1
                    self._last_buy_order = None

    def _handle_no_position(self, kline: KLine, quote_balance: Decimal, avg_price: Decimal) -> None:
        """空仓时的策略"""
        current_price = kline.close_price

        if len(self._avg_wnd) < 2:
            return

        avg_prev = self._avg_wnd[-2]
        avg_curr = self._avg_wnd[-1]

        # 均线上升且价格上穿均线 - 趋势确认
        if avg_curr > avg_prev and current_price > avg_price:
            rise_rate = (avg_curr - avg_prev) / avg_prev if avg_prev > 0 else Decimal("0")
            if rise_rate >= self._buy_volatility:
                quantity = quote_balance / current_price
                quantity = quantity.quantize(Decimal("0.0000"), rounding=ROUND_DOWN)

                if quantity > Decimal("0"):
                    order = self.context.buy(kline.open_time, current_price, quantity)
                    self._last_buy_order = order
                    self._buy_count += 1

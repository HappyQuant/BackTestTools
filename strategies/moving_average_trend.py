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
        drawdown_rate: Decimal
    ):
        super().__init__(context)

        if kline_wnd_size <= 0 or avg_wnd_size <= 0:
            raise ValueError("Window sizes must be positive")

        self._kline_wnd_size = kline_wnd_size
        self._avg_wnd_size = avg_wnd_size
        self._buy_volatility = buy_volatility_rate
        self._sell_volatility = sell_volatility_rate
        self._drawdown_rate = drawdown_rate

        self._kline_wnd: deque[KLine] = deque(maxlen=kline_wnd_size)
        self._avg_wnd: deque[Decimal] = deque(maxlen=avg_wnd_size)
        self._last_buy_order: Optional[Order] = None

    def _process_kline(self, kline: KLine) -> None:
        self._kline_wnd.append(kline)

        if len(self._kline_wnd) < self._kline_wnd_size:
            return

        avg_price = sum(k.close_price for k in self._kline_wnd) / Decimal(self._kline_wnd_size)
        self._avg_wnd.append(avg_price)

        if len(self._avg_wnd) < self._avg_wnd_size:
            return

        self._execute_strategy(kline)

    def _execute_strategy(self, kline: KLine) -> None:
        base_balance, quote_balance = self.context.get_balance()

        if base_balance > Decimal("0"):
            self._handle_position(kline, base_balance)
        else:
            self._handle_no_position(kline, quote_balance)

    def _handle_position(self, kline: KLine, base_balance: Decimal) -> None:
        """持有仓位时的策略"""
        avg_max = max(self._avg_wnd)
        if avg_max == Decimal("0"):
            return

        volatility = (avg_max - self._avg_wnd[-1]) / avg_max

        if volatility >= self._sell_volatility:
            self.context.sell(kline.open_time, kline.close_price, base_balance)
            return

        if self._last_buy_order is not None:
            price_change = (kline.close_price - self._last_buy_order.price) / self._last_buy_order.price
            if price_change < -self._drawdown_rate:
                self.context.sell(kline.open_time, kline.close_price, base_balance)

    def _handle_no_position(self, kline: KLine, quote_balance: Decimal) -> None:
        """空仓时的策略"""
        avg_min = min(self._avg_wnd)
        if avg_min == Decimal("0"):
            return

        volatility = (self._avg_wnd[-1] - avg_min) / avg_min

        if volatility >= self._buy_volatility:
            quantity = quote_balance / kline.close_price
            quantity = quantity.quantize(Decimal("0.0000"), rounding=ROUND_DOWN)
            order = self.context.buy(kline.open_time, kline.close_price, quantity)
            self._last_buy_order = order

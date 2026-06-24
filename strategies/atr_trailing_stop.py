"""
ATR追踪止损策略

策略逻辑：
1. 计算ATR(Average True Range)衡量市场波动
2. 买入信号：价格突破近期高点（N日最高价）
3. 卖出信号：价格跌破 买入后最高价 - N倍ATR（追踪止损线）
4. 止损线随价格上涨而上移，不会随价格下跌而下移
"""
from collections import deque
from decimal import Decimal, ROUND_DOWN
from typing import Optional

from domain import KLine, Order, Side
from engine import StrategyBase, ITradingContext


class ATRTrailingStopStrategy(StrategyBase):
    """ATR追踪止损策略"""

    def __init__(
        self,
        context: ITradingContext,
        atr_period: int,
        atr_multiplier: Decimal,
        breakout_period: int,
        take_profit_rate: Optional[Decimal] = None
    ):
        super().__init__(context)

        if atr_period <= 0 or breakout_period <= 0:
            raise ValueError("Periods must be positive")
        if atr_multiplier <= Decimal("0"):
            raise ValueError("atr_multiplier must be positive")

        self._atr_period = atr_period
        self._atr_multiplier = atr_multiplier
        self._breakout_period = breakout_period
        self._take_profit_rate = take_profit_rate

        self._tr_wnd: deque[Decimal] = deque(maxlen=atr_period)
        self._high_wnd: deque[Decimal] = deque(maxlen=breakout_period)
        self._prev_close: Optional[Decimal] = None
        self._last_buy_order: Optional[Order] = None
        self._highest_since_buy: Optional[Decimal] = None

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

    def _on_order_executed(self, order: Order, signal: Optional[str] = None) -> None:
        if order.side == Side.Buy:
            self._last_buy_order = order
            self._highest_since_buy = order.price
            self._buy_count += 1
        else:
            if signal == "stop_loss":
                self._stop_loss_count += 1
            elif signal == "take_profit":
                self._take_profit_count += 1
            self._sell_count += 1
            self._last_buy_order = None
            self._highest_since_buy = None

    def _calc_tr(self, kline: KLine) -> Decimal:
        high_low = kline.high_price - kline.low_price
        if self._prev_close is not None:
            high_close = abs(kline.high_price - self._prev_close)
            low_close = abs(kline.low_price - self._prev_close)
            return max(high_low, high_close, low_close)
        return high_low

    def _calc_atr(self) -> Optional[Decimal]:
        if len(self._tr_wnd) < self._atr_period:
            return None
        return sum(self._tr_wnd, Decimal("0")) / Decimal(self._atr_period)

    def _process_kline(self, kline: KLine) -> None:
        tr = self._calc_tr(kline)
        self._tr_wnd.append(tr)
        self._high_wnd.append(kline.high_price)
        self._prev_close = kline.close_price

        atr = self._calc_atr()
        if atr is None:
            return

        base_balance, quote_balance = self.context.get_balance()

        if base_balance > Decimal("0"):
            self._handle_position(kline, base_balance, atr)
        else:
            self._handle_no_position(kline, quote_balance, atr)

    def _handle_position(self, kline: KLine, base_balance: Decimal, atr: Decimal) -> None:
        current_price = kline.close_price

        if self._highest_since_buy is None or current_price > self._highest_since_buy:
            self._highest_since_buy = current_price

        if self._last_buy_order is not None and self._take_profit_rate is not None:
            price_change = (current_price - self._last_buy_order.price) / self._last_buy_order.price
            if price_change > self._take_profit_rate:
                self.context.sell(kline.open_time, current_price, base_balance, signal="take_profit")
                return

        stop_line = max(self._highest_since_buy - self._atr_multiplier * atr, Decimal("0"))
        if current_price <= stop_line:
            self.context.sell(kline.open_time, current_price, base_balance, signal="stop_loss")

    def _handle_no_position(self, kline: KLine, quote_balance: Decimal, atr: Decimal) -> None:
        if len(self._high_wnd) < self._breakout_period:
            return

        current_price = kline.close_price
        highest = max(self._high_wnd)

        if current_price >= highest:
            quantity = quote_balance / current_price
            quantity = quantity.quantize(Decimal("0.0000"), rounding=ROUND_DOWN)

            if quantity > Decimal("0"):
                self.context.buy(kline.open_time, current_price, quantity)

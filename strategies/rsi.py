"""
RSI超买超卖策略

策略逻辑：
1. 计算RSI(Relative Strength Index)指标
2. 买入信号：RSI低于超卖阈值，认为超卖反弹
3. 卖出信号：RSI高于超买阈值，认为超买回落
"""
from collections import deque
from decimal import Decimal, ROUND_DOWN
from typing import Optional

from domain import KLine, Order
from engine import StrategyBase, ITradingContext


class RSIStrategy(StrategyBase):
    """RSI超买超卖策略"""

    def __init__(
        self,
        context: ITradingContext,
        period: int,
        oversold_threshold: Decimal,
        overbought_threshold: Decimal,
        drawdown_rate: Optional[Decimal] = None,
        take_profit_rate: Optional[Decimal] = None
    ):
        super().__init__(context)

        if period <= 1:
            raise ValueError("Period must be greater than 1")
        if not (Decimal("0") < oversold_threshold < overbought_threshold < Decimal("100")):
            raise ValueError("Thresholds must satisfy: 0 < oversold < overbought < 100")

        self._period = period
        self._oversold_threshold = oversold_threshold
        self._overbought_threshold = overbought_threshold
        self._drawdown_rate = drawdown_rate
        self._take_profit_rate = take_profit_rate

        self._gains: deque[Decimal] = deque(maxlen=period)
        self._losses: deque[Decimal] = deque(maxlen=period)
        self._prev_price: Optional[Decimal] = None
        self._last_buy_order: Optional[Order] = None

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

    def _calc_rsi(self) -> Optional[Decimal]:
        """计算RSI值"""
        if len(self._gains) < self._period:
            return None

        avg_gain = sum(self._gains) / Decimal(self._period)
        avg_loss = sum(self._losses) / Decimal(self._period)

        if avg_loss == Decimal("0"):
            return Decimal("100")

        rs = avg_gain / avg_loss
        rsi = Decimal("100") - (Decimal("100") / (Decimal("1") + rs))
        return rsi

    def _process_kline(self, kline: KLine) -> None:
        current_price = kline.close_price

        if self._prev_price is not None:
            change = current_price - self._prev_price
            self._gains.append(max(change, Decimal("0")))
            self._losses.append(max(-change, Decimal("0")))

        self._prev_price = current_price

        rsi = self._calc_rsi()
        if rsi is None:
            return

        base_balance, quote_balance = self.context.get_balance()

        if base_balance > Decimal("0"):
            self._handle_position(kline, base_balance, current_price, rsi)
        else:
            self._handle_no_position(kline, quote_balance, current_price, rsi)

    def _handle_position(self, kline: KLine, base_balance: Decimal, current_price: Decimal, rsi: Decimal) -> None:
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

        # RSI超买卖出
        if rsi >= self._overbought_threshold:
            self.context.sell(kline.open_time, current_price, base_balance)
            self._sell_count += 1
            self._last_buy_order = None

    def _handle_no_position(self, kline: KLine, quote_balance: Decimal, current_price: Decimal, rsi: Decimal) -> None:
        # RSI超卖买入
        if rsi <= self._oversold_threshold:
            quantity = quote_balance / current_price
            quantity = quantity.quantize(Decimal("0.0000"), rounding=ROUND_DOWN)

            if quantity > Decimal("0"):
                order = self.context.buy(kline.open_time, current_price, quantity)
                self._last_buy_order = order
                self._buy_count += 1

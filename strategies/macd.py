"""
MACD策略

策略逻辑：
1. 计算MACD指标：DIF(快线EMA - 慢线EMA)、DEA(DIF的EMA)、MACD柱(DIF - DEA)
2. 买入信号：DIF上穿DEA（金叉）
3. 卖出信号：DIF下穿DEA（死叉）
"""
from decimal import Decimal, ROUND_DOWN
from typing import Optional

from domain import KLine, Order
from engine import StrategyBase, ITradingContext


class MACDStrategy(StrategyBase):
    """MACD策略"""

    def __init__(
        self,
        context: ITradingContext,
        fast_period: int,
        slow_period: int,
        signal_period: int,
        drawdown_rate: Optional[Decimal] = None,
        take_profit_rate: Optional[Decimal] = None
    ):
        super().__init__(context)

        if fast_period <= 0 or slow_period <= 0 or signal_period <= 0:
            raise ValueError("Periods must be positive")
        if fast_period >= slow_period:
            raise ValueError("fast_period must be less than slow_period")

        self._fast_period = fast_period
        self._slow_period = slow_period
        self._signal_period = signal_period
        self._drawdown_rate = drawdown_rate
        self._take_profit_rate = take_profit_rate

        self._fast_ema: Optional[Decimal] = None
        self._slow_ema: Optional[Decimal] = None
        self._dea: Optional[Decimal] = None
        self._kline_count = 0
        self._last_buy_order: Optional[Order] = None
        self._prev_dif_above_dea: Optional[bool] = None

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

    @staticmethod
    def _calc_ema(prev_ema: Optional[Decimal], price: Decimal, period: int) -> Decimal:
        """计算EMA"""
        multiplier = Decimal("2") / Decimal(period + 1)
        if prev_ema is None:
            return price
        return price * multiplier + prev_ema * (Decimal("1") - multiplier)

    def _process_kline(self, kline: KLine) -> None:
        self._kline_count += 1
        current_price = kline.close_price

        self._fast_ema = self._calc_ema(self._fast_ema, current_price, self._fast_period)
        self._slow_ema = self._calc_ema(self._slow_ema, current_price, self._slow_period)

        # 需要足够数据让EMA稳定
        if self._kline_count < self._slow_period:
            return

        dif = self._fast_ema - self._slow_ema
        self._dea = self._calc_ema(self._dea, dif, self._signal_period)

        dif_above_dea = dif > self._dea

        if self._prev_dif_above_dea is None:
            self._prev_dif_above_dea = dif_above_dea
            return

        base_balance, quote_balance = self.context.get_balance()

        if base_balance > Decimal("0"):
            self._handle_position(kline, base_balance, dif_above_dea)
        else:
            self._handle_no_position(kline, quote_balance, dif_above_dea)

        self._prev_dif_above_dea = dif_above_dea

    def _handle_position(self, kline: KLine, base_balance: Decimal, dif_above_dea: bool) -> None:
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
        if self._prev_dif_above_dea and not dif_above_dea:
            self.context.sell(kline.open_time, current_price, base_balance)
            self._sell_count += 1
            self._last_buy_order = None

    def _handle_no_position(self, kline: KLine, quote_balance: Decimal, dif_above_dea: bool) -> None:
        # 金叉买入
        if not self._prev_dif_above_dea and dif_above_dea:
            current_price = kline.close_price
            quantity = quote_balance / current_price
            quantity = quantity.quantize(Decimal("0.0000"), rounding=ROUND_DOWN)

            if quantity > Decimal("0"):
                order = self.context.buy(kline.open_time, current_price, quantity)
                self._last_buy_order = order
                self._buy_count += 1

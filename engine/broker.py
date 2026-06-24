"""
延迟执行代理，解决回测中的未来函数(look-ahead bias)问题

策略在当前K线收盘后做出决策，但实际交易应在下一根K线开盘价执行。
PendingOrderBroker 缓存策略的交易意图，在下一根K线到来时以开盘价成交。
"""
from decimal import Decimal
from typing import Optional

from domain import KLine, Order, Side
from domain.account import Account, InsufficientBalanceError
from engine.strategy_base import ITradingContext


class PendingOrder:
    __slots__ = ('side', 'quantity', 'signal')

    def __init__(self, side: Side, quantity: Decimal, signal: Optional[str] = None):
        self.side = side
        self.quantity = quantity
        self.signal = signal


class PendingOrderBroker(ITradingContext):
    """延迟执行代理：策略下单后，订单在下一根K线开盘价成交"""

    def __init__(self, account: Account):
        self._account = account
        self._pending: Optional[PendingOrder] = None

    def get_balance(self) -> tuple[Decimal, Decimal]:
        return self._account.get_balance()

    def buy(self, ts: int, price: Decimal, quantity: Decimal, signal: Optional[str] = None) -> None:
        if self._pending is not None:
            raise ValueError("已有待执行订单，不能重复下单")
        self._pending = PendingOrder(Side.Buy, quantity, signal)

    def sell(self, ts: int, price: Decimal, quantity: Decimal, signal: Optional[str] = None) -> None:
        if self._pending is not None:
            raise ValueError("已有待执行订单，不能重复下单")
        self._pending = PendingOrder(Side.Sell, quantity, signal)

    def execute_pending(self, kline: KLine) -> Optional[tuple[Order, Optional[str]]]:
        """在下一根K线到来时，以开盘价执行待处理订单

        Returns:
            (executed_order, signal) 如果成功执行，或 None 如果没有待处理订单或执行失败
        """
        if self._pending is None:
            return None

        order = self._pending
        self._pending = None

        try:
            if order.side == Side.Buy:
                result = self._account.buy(kline.open_time, kline.open_price, order.quantity)
            else:
                result = self._account.sell(kline.open_time, kline.open_price, order.quantity)
            return result, order.signal
        except InsufficientBalanceError:
            return None

    @property
    def account(self) -> Account:
        return self._account

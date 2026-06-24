"""
延迟执行代理，解决回测中的未来函数(look-ahead bias)问题

策略在当前K线收盘后做出决策，但实际交易应在下一根K线开盘价执行。
PendingOrderBroker 缓存策略的交易意图，在下一根K线到来时以开盘价成交。
"""
from decimal import Decimal
from typing import Optional

from domain import KLine, Order, Side
from domain.account import Account
from engine.strategy_base import ITradingContext


class PendingOrderBroker(ITradingContext):
    """延迟执行代理：策略下单后，订单在下一根K线开盘价成交"""

    def __init__(self, account: Account):
        self._account = account
        self._pending_buy_quantity: Optional[Decimal] = None
        self._pending_sell_quantity: Optional[Decimal] = None
        self._last_executed_order: Optional[Order] = None

    def get_balance(self) -> tuple[Decimal, Decimal]:
        return self._account.get_balance()

    def buy(self, ts: int, price: Decimal, quantity: Decimal) -> Order:
        """策略调用buy时，仅记录意图"""
        if self._pending_buy_quantity is not None or self._pending_sell_quantity is not None:
            raise ValueError("已有待执行订单，不能重复下单")
        self._pending_buy_quantity = quantity
        # 返回占位Order（price为信号价格，实际成交价在execute_pending时确定）
        return Order(ts, Side.Buy, price, quantity, Decimal("0"))

    def sell(self, ts: int, price: Decimal, quantity: Decimal) -> Order:
        """策略调用sell时，仅记录意图"""
        if self._pending_buy_quantity is not None or self._pending_sell_quantity is not None:
            raise ValueError("已有待执行订单，不能重复下单")
        self._pending_sell_quantity = quantity
        return Order(ts, Side.Sell, price, quantity, Decimal("0"))

    def execute_pending(self, kline: KLine) -> Optional[Order]:
        """在下一根K线到来时，以开盘价执行待处理订单"""
        self._last_executed_order = None

        if self._pending_buy_quantity is not None:
            quantity = self._pending_buy_quantity
            self._pending_buy_quantity = None
            # 检查是否有足够余额（开盘价可能不同于信号价）
            cost = kline.open_price * quantity
            fee = cost * self._account.fee_rate
            if cost + fee > self._account.quote_balance:
                return None
            result = self._account.buy(kline.open_time, kline.open_price, quantity)
            self._last_executed_order = result
            return result

        if self._pending_sell_quantity is not None:
            quantity = self._pending_sell_quantity
            self._pending_sell_quantity = None
            if quantity > self._account.base_balance:
                return None
            result = self._account.sell(kline.open_time, kline.open_price, quantity)
            self._last_executed_order = result
            return result

        return None

    @property
    def last_executed_order(self) -> Optional[Order]:
        return self._last_executed_order

    @property
    def account(self) -> Account:
        return self._account

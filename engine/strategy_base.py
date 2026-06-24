from decimal import Decimal
from typing import List, Protocol, runtime_checkable

from domain import KLine, Order


@runtime_checkable
class ITradingContext(Protocol):
    """策略交易上下文接口，策略通过此接口与回测引擎交互"""

    def buy(self, ts: int, price: Decimal, quantity: Decimal) -> Order:
        """买入"""
        ...

    def sell(self, ts: int, price: Decimal, quantity: Decimal) -> Order:
        """卖出"""
        ...

    def get_balance(self) -> tuple[Decimal, Decimal]:
        """获取余额"""
        ...


class IStrategy(Protocol):
    """策略接口"""

    def on_kline(self, kline: KLine) -> None:
        """处理K线数据"""
        ...

    def on_start(self) -> None:
        """回测开始前调用"""
        ...

    def on_end(self) -> None:
        """回测结束后调用"""
        ...


class StrategyBase:
    """策略基类，提供常用功能"""

    def __init__(self, context: ITradingContext):
        self.context = context
        self._first_kline: KLine | None = None
        self._last_kline: KLine | None = None

    @property
    def first_kline(self) -> KLine | None:
        return self._first_kline

    @property
    def last_kline(self) -> KLine | None:
        return self._last_kline

    def on_start(self) -> None:
        pass

    def on_end(self) -> None:
        pass

    def on_kline(self, kline: KLine) -> None:
        if self._first_kline is None:
            self._first_kline = kline
        self._last_kline = kline
        self._process_kline(kline)

    def _on_order_executed(self, order: Order) -> None:
        """当延迟执行的订单实际成交时调用，子类可重写"""
        pass

    def _process_kline(self, kline: KLine) -> None:
        """子类实现具体策略逻辑"""
        raise NotImplementedError

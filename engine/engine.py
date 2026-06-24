from typing import List, Optional

from data import IKLineProvider
from domain import Account, Order
from engine.broker import PendingOrderBroker
from engine.config import BackTestConfig
from engine.feeder import KLineFeeder
from engine.strategy_base import IStrategy


class BackTestEngine:
    """回测引擎"""

    def __init__(
        self,
        provider: IKLineProvider,
        config: BackTestConfig,
        account: Account
    ):
        self._provider = provider
        self._config = config
        self._account = account
        self._broker = PendingOrderBroker(account)
        self._strategies: List[IStrategy] = []

    def add_strategy(self, strategy: IStrategy) -> "BackTestEngine":
        """添加策略，支持链式调用"""
        self._strategies.append(strategy)
        return self

    def run(self) -> None:
        """运行回测"""
        if not self._strategies:
            raise ValueError("No strategy added")

        feeder = KLineFeeder(self._provider, self._config)

        for strategy in self._strategies:
            strategy.on_start()

        for kline in feeder:
            # 先执行上一根K线产生的待处理订单（以当前K线开盘价成交）
            result = self._broker.execute_pending(kline)

            # 通知策略有新订单成交
            if result is not None:
                executed_order, signal = result
                for strategy in self._strategies:
                    strategy._on_order_executed(executed_order, signal)

            # 然后让策略处理当前K线
            for strategy in self._strategies:
                strategy.on_kline(kline)

        for strategy in self._strategies:
            strategy.on_end()

    @property
    def account(self) -> Account:
        return self._account

    @property
    def broker(self) -> PendingOrderBroker:
        return self._broker

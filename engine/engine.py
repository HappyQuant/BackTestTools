from typing import List

from data import IKLineProvider
from domain import Account
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
            for strategy in self._strategies:
                strategy.on_kline(kline)

        for strategy in self._strategies:
            strategy.on_end()

    @property
    def account(self) -> Account:
        return self._account

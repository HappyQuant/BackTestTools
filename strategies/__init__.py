from abc import ABC, abstractmethod

from context import BackTestContext, KLine


class IStrategy(ABC):
    def __init__(self, context: BackTestContext):
        self.context = context

    @abstractmethod
    def run(self, kline: KLine):
        """执行策略逻辑"""
        pass

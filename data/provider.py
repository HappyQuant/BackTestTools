from abc import ABC, abstractmethod
from typing import List

from domain import KLine, KLineSymbol, KLineInterval


class IKLineProvider(ABC):
    """K线数据源接口"""

    @abstractmethod
    def fetch_next_klines(
        self,
        symbol: KLineSymbol,
        interval: KLineInterval,
        from_time: int,
        limit: int
    ) -> List[KLine]:
        """获取指定时间之后的K线数据"""
        pass

    @abstractmethod
    def fetch_previous_klines(
        self,
        symbol: KLineSymbol,
        interval: KLineInterval,
        end_time: int,
        limit: int
    ) -> List[KLine]:
        """获取指定时间之前的K线数据"""
        pass

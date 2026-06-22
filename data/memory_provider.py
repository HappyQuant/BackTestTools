from typing import List
from decimal import Decimal

from data.provider import IKLineProvider
from domain import KLine, KLineSymbol, KLineInterval


class InMemoryKLineProvider(IKLineProvider):
    """内存数据源，用于测试"""

    def __init__(self, klines: List[KLine]):
        self._klines = sorted(klines, key=lambda k: k.open_time)

    def fetch_next_klines(
        self,
        symbol: KLineSymbol,
        interval: KLineInterval,
        from_time: int,
        limit: int
    ) -> List[KLine]:
        result = [
            k for k in self._klines
            if k.open_time >= from_time * 1000
        ][:limit]
        return result

    def fetch_previous_klines(
        self,
        symbol: KLineSymbol,
        interval: KLineInterval,
        end_time: int,
        limit: int
    ) -> List[KLine]:
        result = [
            k for k in self._klines
            if k.open_time <= end_time * 1000
        ][-limit:]
        return result


def generate_mock_klines(
    start_time: int,
    count: int,
    base_price: Decimal = Decimal("100"),
    interval_seconds: int = 60
) -> List[KLine]:
    """生成模拟K线数据，用于测试"""
    klines = []
    for i in range(count):
        open_time = (start_time + i * interval_seconds) * 1000
        price = base_price + Decimal(str(i * 0.1))
        klines.append(KLine(
            open_time=open_time,
            open_price=price,
            close_price=price + Decimal("0.05"),
            high_price=price + Decimal("0.1"),
            low_price=price - Decimal("0.05")
        ))
    return klines

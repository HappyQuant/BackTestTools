from collections import deque
from typing import Iterator, Optional

from data import IKLineProvider
from domain import KLine
from engine.config import BackTestConfig


class KLineFeeder(Iterator[KLine]):
    """K线数据迭代器，支持预加载和按需获取"""

    BUFFER_THRESHOLD = 20
    FETCH_LIMIT = 1000

    def __init__(
        self,
        provider: IKLineProvider,
        config: BackTestConfig
    ):
        self._provider = provider
        self._config = config
        self._buffer: deque[KLine] = deque()
        self._next_fetch_time: int = config.start_ts
        self._exhausted: bool = False
        self._current: Optional[KLine] = None

    def _refill_buffer(self) -> None:
        """从数据源获取更多K线数据"""
        if len(self._buffer) >= self.BUFFER_THRESHOLD or self._exhausted:
            return

        klines = self._provider.fetch_next_klines(
            self._config.symbol,
            self._config.interval,
            self._next_fetch_time,
            self.FETCH_LIMIT
        )

        if not klines:
            self._exhausted = True
            return

        interval_seconds = BackTestConfig.get_interval_seconds(self._config.interval)
        self._next_fetch_time = klines[-1].open_time // 1000 + interval_seconds
        self._buffer.extend(klines)

    def __iter__(self) -> "KLineFeeder":
        return self

    def __next__(self) -> KLine:
        self._refill_buffer()

        if not self._buffer:
            raise StopIteration

        kline = self._buffer.popleft()
        if kline.open_time // 1000 > self._config.end_ts:
            raise StopIteration

        self._current = kline
        return kline

    @property
    def current(self) -> Optional[KLine]:
        return self._current

from collections import deque
from typing import Optional, List

from decimal import Decimal

from context import BackTestContext
from kline import KLine
from kline_cli import get_next_klines


class BackTestKLineCache:
    BUFFER_THRESHOLD = 20
    FETCH_LIMIT = 1000

    def __init__(self, context: BackTestContext):
        self.cursor_kline: Optional[KLine] = None
        self.next_klines_start_ts: int = context.from_ts
        self.no_left_klines: bool = False
        self.cached_klines: deque[KLine] = deque()
        self.context: BackTestContext = context

    @staticmethod
    def get_interval(unit: str, digital: int) -> int:
        multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        return digital * multipliers.get(unit, 1)

    def get_next_kline(self) -> Optional[KLine]:
        if len(self.cached_klines) < self.BUFFER_THRESHOLD and not self.no_left_klines:
            klines = get_next_klines(
                self.context.kline_provider,
                self.context.symbol,
                self.context.interval,
                self.next_klines_start_ts,
                self.FETCH_LIMIT
            )

            if klines is None or len(klines) == 0:
                self.no_left_klines = True
            else:
                unit = self.context.interval.value[-1]
                digital = int(self.context.interval.value[:-1])
                interval = BackTestKLineCache.get_interval(unit, digital)

                self.next_klines_start_ts = klines[-1]["open_time"] // 1000 + interval
                self.cached_klines.extend(
                    KLine(
                        k["open_time"],
                        Decimal(k["open_price"]),
                        Decimal(k["close_price"]),
                        Decimal(k["high_price"]),
                        Decimal(k["low_price"])
                    )
                    for k in klines
                )

        if len(self.cached_klines) == 0:
            return None

        self.cursor_kline = self.cached_klines.popleft()
        if self.cursor_kline.open_time / 1000 > self.context.end_ts:
            return None

        return self.cursor_kline

    def __iter__(self):
        return self

    def __next__(self) -> KLine:
        kline = self.get_next_kline()
        if kline is not None:
            return kline
        raise StopIteration

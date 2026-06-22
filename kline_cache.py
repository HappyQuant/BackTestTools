from typing import Optional, List

from decimal import Decimal

from context import BackTestContext
from kline import KLine
from kline_cli import get_next_klines


class BackTestKLineCache:
    def __init__(self, context: BackTestContext):
        # 游标K线
        self.cursor_kline: Optional[KLine] = None
        # 下一条批量从数据源获取到K线的开始时间
        self.next_klines_start_ts: int = context.from_ts
        # 数据源已没有剩余K线
        self.no_left_klines: bool = False
        # 本地K线缓冲区
        self.cached_klines: List[KLine] = list()
        self.context: BackTestContext = context

    @staticmethod
    def get_interval(unit: str, digital: int):
        if unit == "m":
            digital *= 60
        elif unit == "h":
            digital *= 3600
        elif unit == "d":
            digital *= 86400
        return digital

    def get_next_kline(self) -> Optional[KLine]:
        # 本地缓冲区K线数据不足20条 且远程数据源仍有K线数据
        if len(self.cached_klines) < 20 and not self.no_left_klines:
            klines = get_next_klines(self.context.kline_provider, self.context.symbol, self.context.interval,
                                     self.next_klines_start_ts,
                                     1000)
            if klines is None or len(klines) == 0:
                self.no_left_klines = True
            else:
                unit = self.context.interval.value[-1]
                assert unit in ("s", "m", "h", "d")
                digital = int(self.context.interval.value[:-1])
                interval = BackTestKLineCache.get_interval(unit, digital)

                # 推算 next_klines_start_ts
                # 扩充本地K线缓冲区
                self.next_klines_start_ts = klines[-1]["open_time"] // 1000 + interval
                self.cached_klines.extend(
                    [
                        KLine(k["open_time"], Decimal(k["open_price"]), Decimal(k["close_price"]),
                              Decimal(k["high_price"]), Decimal(k["low_price"]))
                        for k in klines
                    ])

        if len(self.cached_klines) == 0:
            return None

        self.cursor_kline = self.cached_klines.pop(0)
        if self.cursor_kline.open_time / 1000 > self.context.end_ts:
            return None

        return self.cursor_kline

    def __iter__(self):
        return self

    def __next__(self) -> Optional[KLine]:
        kline = self.get_next_kline()
        if kline is not None:
            return kline
        else:
            raise StopIteration

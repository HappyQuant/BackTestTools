from dataclasses import dataclass, field
import time

from domain import KLineSymbol, KLineInterval


@dataclass
class BackTestConfig:
    """回测配置"""
    symbol: KLineSymbol
    interval: KLineInterval
    start_ts: int
    end_ts: int = field(default_factory=lambda: int(time.time()))

    def __post_init__(self):
        if self.start_ts < 0:
            raise ValueError("start_ts must be non-negative")
        if self.end_ts < self.start_ts:
            raise ValueError("end_ts must be greater than or equal to start_ts")

    @staticmethod
    def get_interval_seconds(interval: KLineInterval) -> int:
        """获取K线间隔秒数"""
        unit = interval.value[-1]
        digital = int(interval.value[:-1])
        multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        return digital * multipliers.get(unit, 1)

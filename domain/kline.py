from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class KLine:
    """K线数据，不可变对象"""
    open_time: int
    open_price: Decimal
    close_price: Decimal
    high_price: Decimal
    low_price: Decimal

    def __str__(self) -> str:
        return (f"| KLine | O: {self.open_price} | C: {self.close_price} | "
                f"H: {self.high_price} | L: {self.low_price} | OpenTs: {self.open_time} |")

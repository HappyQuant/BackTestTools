from dataclasses import dataclass
from decimal import Decimal

from domain.enumeration import Side


@dataclass
class Order:
    """订单记录"""
    order_ts: int
    side: Side
    price: Decimal
    quantity: Decimal
    fee: Decimal

    def __str__(self) -> str:
        return (f"| Order | Side: {self.side.value} | Price: {self.price} | "
                f"Quantity: {self.quantity} | Fee: {self.fee} | Ts: {self.order_ts} |")

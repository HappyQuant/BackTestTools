from dataclasses import dataclass, field
from decimal import Decimal
from typing import List

from domain.enumeration import Side
from domain.order import Order


class InsufficientBalanceError(Exception):
    """余额不足错误"""
    pass


@dataclass
class Account:
    """账户管理"""
    base_balance: Decimal = Decimal("0")
    quote_balance: Decimal = Decimal("0")
    fee_rate: Decimal = Decimal("0")
    total_fee: Decimal = Decimal("0")
    orders: List[Order] = field(default_factory=list)

    def set_balance(self, base: Decimal, quote: Decimal) -> None:
        if base < Decimal("0") or quote < Decimal("0"):
            raise ValueError("Balances must be non-negative")
        self.base_balance = base
        self.quote_balance = quote

    def set_fee_rate(self, fee_rate: Decimal) -> None:
        if fee_rate < Decimal("0") or fee_rate > Decimal("1"):
            raise ValueError("fee_rate must be between 0 and 1")
        self.fee_rate = fee_rate

    def get_balance(self) -> tuple[Decimal, Decimal]:
        return self.base_balance, self.quote_balance

    def get_total_fee(self) -> Decimal:
        return self.total_fee

    def buy(self, ts: int, price: Decimal, quantity: Decimal) -> Order:
        if price <= Decimal("0"):
            raise ValueError("price must be positive")
        if quantity <= Decimal("0"):
            raise ValueError("quantity must be positive")

        cost = price * quantity
        fee = cost * self.fee_rate
        if cost + fee > self.quote_balance:
            raise InsufficientBalanceError(
                f"Insufficient quote balance: need {cost + fee}, have {self.quote_balance}"
            )

        self.base_balance += quantity
        self.quote_balance -= cost + fee
        self.total_fee += fee

        order = Order(ts, Side.Buy, price, quantity, fee)
        self.orders.append(order)
        return order

    def sell(self, ts: int, price: Decimal, quantity: Decimal) -> Order:
        if price <= Decimal("0"):
            raise ValueError("price must be positive")
        if quantity <= Decimal("0"):
            raise ValueError("quantity must be positive")

        if quantity > self.base_balance:
            raise InsufficientBalanceError(
                f"Insufficient base balance: need {quantity}, have {self.base_balance}"
            )

        self.base_balance -= quantity
        fee = price * quantity * self.fee_rate
        self.quote_balance += price * quantity - fee
        self.total_fee += fee

        order = Order(ts, Side.Sell, price, quantity, fee)
        self.orders.append(order)
        return order

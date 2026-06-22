from enumeration import Side
from typing import Optional, List, Tuple

from decimal import Decimal

from kline import KLine
from kline_cli import KLineSymbol, KLineInterval, get_next_klines
from order import Order


class InsufficientBalanceError(Exception):
    """余额不足错误"""
    pass


class BackTestContext:
    def __init__(self, kline_provider: str, symbol: KLineSymbol, interval: KLineInterval,
                 from_ts: int, end_ts: int = 4294967295):
        if from_ts < 0:
            raise ValueError("from_ts must be non-negative")
        if end_ts < from_ts:
            raise ValueError("end_ts must be greater than or equal to from_ts")

        self.kline_provider: str = kline_provider
        self.symbol: KLineSymbol = symbol
        self.interval: KLineInterval = interval

        self.from_ts: int = from_ts
        self.end_ts: int = end_ts

        self.base_balance: Decimal = Decimal("0")
        self.quote_balance: Decimal = Decimal("0")

        self.base_fee: Decimal = Decimal("0")
        self.quote_fee: Decimal = Decimal("0")

        self.fee_rate: Decimal = Decimal("0")
        self.orders: List[Order] = list()

    def init_currency_balances(self, base_balance: Decimal, quote_balance: Decimal):
        if base_balance < Decimal("0") or quote_balance < Decimal("0"):
            raise ValueError("Balances must be non-negative")
        self.base_balance = base_balance
        self.quote_balance = quote_balance

    def init_exchange_fee_rate(self, fee_rate: Decimal):
        if fee_rate < Decimal("0") or fee_rate > Decimal("1"):
            raise ValueError("fee_rate must be between 0 and 1")
        self.fee_rate = fee_rate

    def get_currency_balances(self) -> Tuple[Decimal, Decimal]:
        return self.base_balance, self.quote_balance

    def get_exchange_fee_rate(self) -> Decimal:
        return self.fee_rate

    def get_exchange_fee(self) -> Tuple[Decimal, Decimal]:
        return self.base_fee, self.quote_fee

    def buy(self, buy_ts: int, price: Decimal, quantity: Decimal):
        if price <= Decimal("0"):
            raise ValueError("price must be positive")
        if quantity <= Decimal("0"):
            raise ValueError("quantity must be positive")

        fee = quantity * self.fee_rate
        cost = price * quantity

        if cost > self.quote_balance:
            raise InsufficientBalanceError(
                f"Insufficient quote balance: need {cost}, have {self.quote_balance}"
            )

        self.base_balance += quantity - fee
        self.quote_balance -= cost
        self.base_fee += fee

        order = Order(buy_ts, Side.Buy, price, quantity, fee)
        self.orders.append(order)

    def sell(self, sell_ts: int, price: Decimal, quantity: Decimal):
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
        self.quote_fee += fee

        order = Order(sell_ts, Side.Sell, price, quantity, fee)
        self.orders.append(order)

from enumeration import Side
from typing import Optional, List, Tuple

from decimal import Decimal

from kline import KLine
from kline_cli import KLineSymbol, KLineInterval, get_next_klines
from order import Order


class BackTestContext(object):
    def __init__(self, kline_provider: str, symbol: KLineSymbol, interval: KLineInterval,
                 from_ts: int, end_ts: int = 4294967295):
        # K线数据源
        self.kline_provider: str = kline_provider
        # 交易对
        self.symbol: KLineSymbol = symbol
        # K线级别
        self.interval: KLineInterval = interval

        # 回测起止
        self.from_ts: int = from_ts
        self.end_ts: int = end_ts

        # 余额 [base资产]
        self.base_balance: Decimal = Decimal("0")
        # 余额 [quote资产]
        self.quote_balance: Decimal = Decimal("0")

        # 手续费消耗 [base资产]
        self.base_fee: Decimal = Decimal("0")
        # 手续费消耗 [quote资产]
        self.quote_fee: Decimal = Decimal("0")

        # 设定费率 [不区分maker还是taker]
        # 默认我们的交易行为都是taker
        self.fee_rate: Decimal = Decimal("0")
        # 订单记录
        self.orders: List[Order] = list()

    def init_currency_balances(self, base_balance: Decimal, quote_balance: Decimal):
        self.base_balance = base_balance
        self.quote_balance = quote_balance

    def init_exchange_fee_rate(self, fee_rate: Decimal):
        self.fee_rate = fee_rate

    def get_currency_balances(self) -> Tuple[Decimal, Decimal]:
        return self.base_balance, self.quote_balance

    def get_exchange_fee_rate(self) -> Decimal:
        return self.fee_rate

    def get_exchange_fee(self) -> Tuple[Decimal, Decimal]:
        return self.base_fee, self.quote_fee

    # 下单 [买]
    # 手续费为 base资产
    # base balance增加
    # quote balance减少
    def buy(self, buy_ts: int, price: Decimal, quantity: Decimal):
        fee = quantity * self.fee_rate
        self.base_balance += quantity - fee
        self.quote_balance -= price * quantity
        self.base_fee += fee
        assert self.quote_balance >= Decimal("0")
        order = Order(buy_ts, Side.Buy, price, quantity, fee)
        self.orders.append(order)

    # 下单 [卖]
    # 手续费为 quote资产
    # base balance减少
    # quote balance增加
    def sell(self, sell_ts: int, price: Decimal, quantity: Decimal):
        self.base_balance -= quantity
        assert self.base_balance >= Decimal("0")
        fee = price * quantity * self.fee_rate
        self.quote_balance += price * quantity - fee
        self.quote_fee += fee
        order = Order(sell_ts, Side.Sell, price, quantity, fee)
        self.orders.append(order)



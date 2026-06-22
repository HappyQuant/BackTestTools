from collections import deque
from typing import Optional

from decimal import Decimal, ROUND_DOWN

from context import BackTestContext, KLine, Order
from strategies import IStrategy


class MovingAverageTrendStrategy(IStrategy):
    def __init__(self, context: BackTestContext,
                 kline_wnd_size: int, avg_line_wnd_size: int,
                 buy_volatility_rate: Decimal, sell_volatility_rate: Decimal, drawdown_rate: Decimal):
        IStrategy.__init__(self, context)
        self.kline_wnd_size: int = kline_wnd_size
        self.avg_line_wnd_size: int = avg_line_wnd_size
        self.buy_volatility_rate: Decimal = buy_volatility_rate
        self.sell_volatility_rate: Decimal = sell_volatility_rate
        self.drawdown_rate: Decimal = drawdown_rate
        self.kline_wnd: deque[KLine] = deque(maxlen=kline_wnd_size)
        self.avg_line_wnd: deque[Decimal] = deque(maxlen=avg_line_wnd_size)
        self.first_kline: Optional[KLine] = None
        self.last_kline: Optional[KLine] = None
        self.last_buy_order: Optional[Order] = None

    def run(self, kline: KLine):
        if self.first_kline is None:
            self.first_kline = kline
        self.last_kline = kline

        self.kline_wnd.append(kline)

        if len(self.kline_wnd) < self.kline_wnd_size:
            return

        avg_price: Decimal = sum(kl.close_price for kl in self.kline_wnd) / Decimal(self.kline_wnd_size)
        self.avg_line_wnd.append(avg_price)

        if len(self.avg_line_wnd) < self.avg_line_wnd_size:
            return

        base_balance, quote_balance = self.context.get_currency_balances()
        if base_balance > Decimal("0"):
            avg_max = max(self.avg_line_wnd)
            volatility = (avg_max - self.avg_line_wnd[-1]) / avg_max

            if volatility >= self.sell_volatility_rate:
                sell_price = kline.close_price
                print("Sell:", sell_price, base_balance)
                self.context.sell(kline.open_time, sell_price, base_balance)

            if (kline.close_price - self.last_buy_order.price) / self.last_buy_order.price < -self.drawdown_rate:
                sell_price = kline.close_price
                print("Sell:", sell_price, base_balance)
                self.context.sell(kline.open_time, sell_price, base_balance)
        else:
            avg_min = min(self.avg_line_wnd)
            volatility = (self.avg_line_wnd[-1] - avg_min) / avg_min

            if volatility >= self.buy_volatility_rate:
                buy_price = kline.close_price
                quantity = quote_balance / buy_price
                quantity = quantity.quantize(Decimal("0.0000"), rounding=ROUND_DOWN)
                print("Buy:", buy_price, quantity)
                self.context.buy(kline.open_time, buy_price, quantity)
                self.last_buy_order = self.context.orders[-1]

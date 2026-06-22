from decimal import Decimal


class KLine(object):
    def __init__(self, open_time: int, open_price: Decimal, close_price: Decimal, high_price: Decimal,
                 low_price: Decimal):
        self.open_time: int = open_time
        self.open_price: Decimal = open_price
        self.close_price: Decimal = close_price
        self.high_price: Decimal = high_price
        self.low_price: Decimal = low_price

    def __str__(self):
        return ("| KLine | O: {} | C: {} | H: {} | L: {} | OpenTs: {} |".
                format(self.open_price, self.close_price, self.high_price,
                       self.low_price, self.open_time))

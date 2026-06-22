from decimal import Decimal

from enumeration import Side


class Order(object):
    def __init__(self, order_ts: int, side: Side, price: Decimal, quantity: Decimal, fee: Decimal):
        self.order_ts = order_ts
        self.side = side
        self.price = price
        self.quantity = quantity
        self.fee = fee

    def __str__(self):
        return ("| Order | Side: {} | Price: {} | Quantity: {} | Fee: {} | Ts: {} |".
                format(self.side.value, self.price, self.quantity,
                       self.fee, self.order_ts))

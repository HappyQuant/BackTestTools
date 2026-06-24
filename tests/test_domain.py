import unittest
from decimal import Decimal

from domain import KLine, KLineSymbol, KLineInterval, Account, InsufficientBalanceError


class TestAccount(unittest.TestCase):
    def setUp(self):
        self.account = Account()

    def test_set_balance(self):
        self.account.set_balance(Decimal("1.5"), Decimal("10000"))
        base, quote = self.account.get_balance()
        self.assertEqual(base, Decimal("1.5"))
        self.assertEqual(quote, Decimal("10000"))

    def test_set_balance_negative(self):
        with self.assertRaises(ValueError):
            self.account.set_balance(Decimal("-1"), Decimal("10000"))

    def test_set_fee_rate(self):
        self.account.set_fee_rate(Decimal("0.002"))
        self.assertEqual(self.account.fee_rate, Decimal("0.002"))

    def test_set_fee_rate_invalid(self):
        with self.assertRaises(ValueError):
            self.account.set_fee_rate(Decimal("1.5"))

    def test_buy_success(self):
        self.account.set_balance(Decimal("0"), Decimal("10000"))
        self.account.set_fee_rate(Decimal("0.001"))

        order = self.account.buy(1000, Decimal("100"), Decimal("10"))

        self.assertEqual(order.quantity, Decimal("10"))
        base, quote = self.account.get_balance()
        self.assertEqual(base, Decimal("10"))
        self.assertEqual(quote, Decimal("8999"))

    def test_buy_insufficient_balance(self):
        self.account.set_balance(Decimal("0"), Decimal("100"))
        with self.assertRaises(InsufficientBalanceError):
            self.account.buy(1000, Decimal("100"), Decimal("10"))

    def test_sell_success(self):
        self.account.set_balance(Decimal("10"), Decimal("0"))
        self.account.set_fee_rate(Decimal("0.001"))

        order = self.account.sell(1000, Decimal("100"), Decimal("5"))

        self.assertEqual(order.quantity, Decimal("5"))
        base, quote = self.account.get_balance()
        self.assertEqual(base, Decimal("5"))
        self.assertAlmostEqual(float(quote), float(Decimal("499.5")))

    def test_sell_insufficient_balance(self):
        self.account.set_balance(Decimal("1"), Decimal("0"))
        with self.assertRaises(InsufficientBalanceError):
            self.account.sell(1000, Decimal("100"), Decimal("10"))


class TestKLine(unittest.TestCase):
    def test_kline_creation(self):
        kline = KLine(
            open_time=1000000,
            open_price=Decimal("100"),
            close_price=Decimal("101"),
            high_price=Decimal("102"),
            low_price=Decimal("99")
        )
        self.assertEqual(kline.open_time, 1000000)
        self.assertEqual(kline.open_price, Decimal("100"))

    def test_kline_immutable(self):
        kline = KLine(
            open_time=1000000,
            open_price=Decimal("100"),
            close_price=Decimal("101"),
            high_price=Decimal("102"),
            low_price=Decimal("99")
        )
        with self.assertRaises(AttributeError):
            kline.open_price = Decimal("200")


if __name__ == "__main__":
    unittest.main()

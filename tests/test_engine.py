import unittest
from decimal import Decimal

from data import InMemoryKLineProvider, generate_mock_klines
from domain import Account, KLineSymbol, KLineInterval, Side
from engine import BackTestConfig, BackTestEngine, StrategyBase


class SimpleTestStrategy(StrategyBase):
    """用于测试的简单策略"""

    def __init__(self, context):
        super().__init__(context)
        self.kline_count = 0
        self.buy_called = False
        self.sell_called = False

    def _on_order_executed(self, order, signal=None):
        if order.side == Side.Buy:
            self.buy_called = True
        else:
            self.sell_called = True

    def _process_kline(self, kline):
        self.kline_count += 1

        base, quote = self.context.get_balance()

        if base == Decimal("0") and not self.buy_called:
            quantity = quote / kline.close_price / 2
            self.context.buy(kline.open_time, kline.close_price, quantity)
        elif base > Decimal("0") and not self.sell_called:
            self.context.sell(kline.open_time, kline.close_price, base)


class TestBackTestEngine(unittest.TestCase):
    def setUp(self):
        self.klines = generate_mock_klines(
            start_time=1000,
            count=200,
            base_price=Decimal("100"),
            interval_seconds=60
        )
        self.provider = InMemoryKLineProvider(self.klines)

    def test_engine_run(self):
        config = BackTestConfig(
            symbol=KLineSymbol.BtcUsdt,
            interval=KLineInterval.OneMinute,
            start_ts=1000,
            end_ts=2000
        )

        account = Account()
        account.set_balance(Decimal("0"), Decimal("10000"))
        account.set_fee_rate(Decimal("0.001"))

        engine = BackTestEngine(self.provider, config, account)
        strategy = SimpleTestStrategy(engine.broker)
        engine.add_strategy(strategy)
        engine.run()

        self.assertGreater(strategy.kline_count, 0)
        self.assertTrue(strategy.buy_called)
        self.assertTrue(strategy.sell_called)

    def test_engine_no_strategy(self):
        config = BackTestConfig(
            symbol=KLineSymbol.BtcUsdt,
            interval=KLineInterval.OneMinute,
            start_ts=1000,
            end_ts=2000
        )

        account = Account()
        engine = BackTestEngine(self.provider, config, account)

        with self.assertRaises(ValueError):
            engine.run()


class TestBackTestConfig(unittest.TestCase):
    def test_valid_config(self):
        config = BackTestConfig(
            symbol=KLineSymbol.BtcUsdt,
            interval=KLineInterval.OneMinute,
            start_ts=1000,
            end_ts=2000
        )
        self.assertEqual(config.start_ts, 1000)

    def test_invalid_time_range(self):
        with self.assertRaises(ValueError):
            BackTestConfig(
                symbol=KLineSymbol.BtcUsdt,
                interval=KLineInterval.OneMinute,
                start_ts=2000,
                end_ts=1000
            )

    def test_interval_seconds(self):
        self.assertEqual(BackTestConfig.get_interval_seconds(KLineInterval.OneMinute), 60)
        self.assertEqual(BackTestConfig.get_interval_seconds(KLineInterval.OneHour), 3600)
        self.assertEqual(BackTestConfig.get_interval_seconds(KLineInterval.OneDay), 86400)


if __name__ == "__main__":
    unittest.main()

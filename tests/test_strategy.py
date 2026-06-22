import unittest
from decimal import Decimal

from data import InMemoryKLineProvider, generate_mock_klines
from domain import Account, KLineSymbol, KLineInterval
from engine import BackTestConfig, BackTestEngine
from strategies import MovingAverageTrendStrategy


class TestMovingAverageTrendStrategy(unittest.TestCase):
    def setUp(self):
        self.klines = generate_mock_klines(
            start_time=1000,
            count=200,
            base_price=Decimal("100"),
            interval_seconds=60
        )
        self.provider = InMemoryKLineProvider(self.klines)

    def test_strategy_creation(self):
        account = Account()
        strategy = MovingAverageTrendStrategy(
            context=account,
            kline_wnd_size=10,
            avg_wnd_size=5,
            buy_volatility_rate=Decimal("0.01"),
            sell_volatility_rate=Decimal("0.01"),
            drawdown_rate=Decimal("0.02")
        )
        self.assertIsNotNone(strategy)

    def test_strategy_invalid_window(self):
        account = Account()
        with self.assertRaises(ValueError):
            MovingAverageTrendStrategy(
                context=account,
                kline_wnd_size=0,
                avg_wnd_size=5,
                buy_volatility_rate=Decimal("0.01"),
                sell_volatility_rate=Decimal("0.01"),
                drawdown_rate=Decimal("0.02")
            )

    def test_strategy_with_multiple_strategies(self):
        """测试多策略并行"""
        config = BackTestConfig(
            symbol=KLineSymbol.BtcUsdt,
            interval=KLineInterval.OneMinute,
            start_ts=1000,
            end_ts=3000
        )

        account1 = Account()
        account1.set_balance(Decimal("0"), Decimal("10000"))
        account1.set_fee_rate(Decimal("0.001"))

        account2 = Account()
        account2.set_balance(Decimal("0"), Decimal("5000"))
        account2.set_fee_rate(Decimal("0.001"))

        strategy1 = MovingAverageTrendStrategy(
            context=account1,
            kline_wnd_size=20,
            avg_wnd_size=10,
            buy_volatility_rate=Decimal("0.001"),
            sell_volatility_rate=Decimal("0.001"),
            drawdown_rate=Decimal("0.01")
        )

        strategy2 = MovingAverageTrendStrategy(
            context=account2,
            kline_wnd_size=30,
            avg_wnd_size=15,
            buy_volatility_rate=Decimal("0.002"),
            sell_volatility_rate=Decimal("0.002"),
            drawdown_rate=Decimal("0.02")
        )

        engine1 = BackTestEngine(self.provider, config, account1)
        engine1.add_strategy(strategy1)

        engine2 = BackTestEngine(self.provider, config, account2)
        engine2.add_strategy(strategy2)

        engine1.run()
        engine2.run()

        base1, quote1 = account1.get_balance()
        base2, quote2 = account2.get_balance()

        total1 = base1 * Decimal("100") + quote1
        total2 = base2 * Decimal("100") + quote2

        self.assertGreater(total1, Decimal("0"))
        self.assertGreater(total2, Decimal("0"))


if __name__ == "__main__":
    unittest.main()

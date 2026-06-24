import unittest
from decimal import Decimal

from data import InMemoryKLineProvider, generate_mock_klines
from domain import Account, KLineSymbol, KLineInterval
from engine import BackTestConfig, BackTestEngine
from strategies import MovingAverageTrendStrategy
from comparison import StrategyConfig, run_single_backtest, STRATEGY_PRESETS


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
        engine = BackTestEngine(self.provider, BackTestConfig(
            symbol=KLineSymbol.BtcUsdt,
            interval=KLineInterval.OneMinute,
            start_ts=1000,
            end_ts=3000
        ), account)
        strategy = MovingAverageTrendStrategy(
            context=engine.broker,
            fast_ma_period=10,
            slow_ma_period=30,
            trend_strength=Decimal("0.002"),
            drawdown_rate=Decimal("0.02")
        )
        self.assertIsNotNone(strategy)

    def test_strategy_invalid_window(self):
        account = Account()
        engine = BackTestEngine(self.provider, BackTestConfig(
            symbol=KLineSymbol.BtcUsdt,
            interval=KLineInterval.OneMinute,
            start_ts=1000,
            end_ts=3000
        ), account)
        with self.assertRaises(ValueError):
            MovingAverageTrendStrategy(
                context=engine.broker,
                fast_ma_period=0,
                slow_ma_period=30,
                trend_strength=Decimal("0.002"),
                drawdown_rate=Decimal("0.02")
            )

    def test_strategy_fast_greater_than_slow(self):
        account = Account()
        engine = BackTestEngine(self.provider, BackTestConfig(
            symbol=KLineSymbol.BtcUsdt,
            interval=KLineInterval.OneMinute,
            start_ts=1000,
            end_ts=3000
        ), account)
        with self.assertRaises(ValueError):
            MovingAverageTrendStrategy(
                context=engine.broker,
                fast_ma_period=30,
                slow_ma_period=30,
                trend_strength=Decimal("0.002"),
                drawdown_rate=Decimal("0.02")
            )

    def test_strategy_with_multiple_strategies(self):
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

        engine1 = BackTestEngine(self.provider, config, account1)
        strategy1 = MovingAverageTrendStrategy(
            context=engine1.broker,
            fast_ma_period=10,
            slow_ma_period=30,
            trend_strength=Decimal("0.002"),
            drawdown_rate=Decimal("0.01")
        )
        engine1.add_strategy(strategy1)

        engine2 = BackTestEngine(self.provider, config, account2)
        strategy2 = MovingAverageTrendStrategy(
            context=engine2.broker,
            fast_ma_period=5,
            slow_ma_period=20,
            trend_strength=Decimal("0.003"),
            drawdown_rate=Decimal("0.02")
        )
        engine2.add_strategy(strategy2)

        engine1.run()
        engine2.run()

        base1, quote1 = account1.get_balance()
        base2, quote2 = account2.get_balance()

        total1 = base1 * Decimal("100") + quote1
        total2 = base2 * Decimal("100") + quote2

        self.assertGreater(total1, Decimal("0"))
        self.assertGreater(total2, Decimal("0"))


class TestComparison(unittest.TestCase):
    """对比测试用例"""

    def setUp(self):
        self.klines = generate_mock_klines(
            start_time=1000,
            count=500,
            base_price=Decimal("100"),
            interval_seconds=60
        )
        self.provider = InMemoryKLineProvider(self.klines)

    def test_strategy_config_creation(self):
        config = StrategyConfig(
            fast_ma_period=10,
            slow_ma_period=30,
            trend_strength=Decimal("0.002"),
            drawdown_rate=Decimal("0.05")
        )
        self.assertEqual(config.fast_ma_period, 10)
        self.assertEqual(config.slow_ma_period, 30)

    def test_strategy_presets(self):
        self.assertIn("conservative", STRATEGY_PRESETS)
        self.assertIn("balanced", STRATEGY_PRESETS)
        self.assertIn("aggressive", STRATEGY_PRESETS)

        conservative = STRATEGY_PRESETS["conservative"]
        self.assertEqual(conservative.fast_ma_period, 20)
        self.assertEqual(conservative.slow_ma_period, 50)

    def test_single_backtest(self):
        config = StrategyConfig(
            fast_ma_period=10,
            slow_ma_period=30,
            trend_strength=Decimal("0.002"),
            drawdown_rate=Decimal("0.05"),
            take_profit_rate=Decimal("0.10")
        )

        result = run_single_backtest(
            provider=self.provider,
            symbol=KLineSymbol.BtcUsdt,
            interval=KLineInterval.OneMinute,
            start_ts=1000,
            end_ts=35000,
            strategy_config=config,
            initial_quote=Decimal("10000")
        )

        self.assertEqual(result.interval, KLineInterval.OneMinute)
        self.assertGreaterEqual(result.total_value, Decimal("0"))

    def test_different_presets_comparison(self):
        results = []

        for preset_name in ["conservative", "balanced", "aggressive"]:
            config = STRATEGY_PRESETS[preset_name]

            result = run_single_backtest(
                provider=self.provider,
                symbol=KLineSymbol.BtcUsdt,
                interval=KLineInterval.OneMinute,
                start_ts=1000,
                end_ts=35000,
                strategy_config=config,
                initial_quote=Decimal("10000")
            )
            results.append(result)

        self.assertEqual(len(results), 3)
        buy_counts = [r.buy_count for r in results]
        self.assertTrue(all(c >= 0 for c in buy_counts))


if __name__ == "__main__":
    unittest.main()

import unittest
from decimal import Decimal

from data import InMemoryKLineProvider, generate_mock_klines
from domain import KLineSymbol, KLineInterval


class TestInMemoryKLineProvider(unittest.TestCase):
    def setUp(self):
        self.klines = generate_mock_klines(
            start_time=1000,
            count=100,
            base_price=Decimal("100"),
            interval_seconds=60
        )
        self.provider = InMemoryKLineProvider(self.klines)

    def test_fetch_next_klines(self):
        result = self.provider.fetch_next_klines(
            KLineSymbol.BtcUsdt,
            KLineInterval.OneMinute,
            1000,
            10
        )
        self.assertEqual(len(result), 10)
        self.assertEqual(result[0].open_time, 1000000)

    def test_fetch_next_klines_limited(self):
        result = self.provider.fetch_next_klines(
            KLineSymbol.BtcUsdt,
            KLineInterval.OneMinute,
            2000,
            10
        )
        self.assertGreater(len(result), 0)
        self.assertTrue(all(k.open_time >= 2000000 for k in result))

    def test_fetch_previous_klines(self):
        result = self.provider.fetch_previous_klines(
            KLineSymbol.BtcUsdt,
            KLineInterval.OneMinute,
            2000,
            10
        )
        self.assertEqual(len(result), 10)
        self.assertTrue(all(k.open_time <= 2000000 for k in result))


class TestGenerateMockKlines(unittest.TestCase):
    def test_generate_count(self):
        klines = generate_mock_klines(1000, 50)
        self.assertEqual(len(klines), 50)

    def test_generate_order(self):
        klines = generate_mock_klines(1000, 10)
        for i in range(1, len(klines)):
            self.assertGreater(klines[i].open_time, klines[i - 1].open_time)


if __name__ == "__main__":
    unittest.main()

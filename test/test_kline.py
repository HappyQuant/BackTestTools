import time
import unittest

from kline_cli import get_previous_klines, get_next_klines, KLineSymbol, KLineInterval


class TestKline(unittest.TestCase):
    kline_provider = "http://192.168.1.35:30080"

    def test_get_previous_klines(self):
        ks = get_previous_klines(TestKline.kline_provider, KLineSymbol.LtcUsdt, KLineInterval.OneMinute,
                                 int(time.time()), 20)
        print(ks)
        self.assertEqual(len(ks), 20)

        ks = get_next_klines(TestKline.kline_provider, KLineSymbol.LtcUsdt, KLineInterval.OneMinute,
                             int(time.time()) - 86400 * 265, 20)
        print(ks)
        self.assertEqual(len(ks), 20)

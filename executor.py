import os
import time
from decimal import Decimal

from dotenv import load_dotenv

from context import BackTestContext
from kline_cache import BackTestKLineCache
from enumeration import KLineSymbol, KLineInterval
from strategies import IStrategy
from strategies.moving_average_trend import MovingAverageTrendStrategy

if __name__ == "__main__":
    load_dotenv()
    kline_provider = os.environ.get("KLINE_PROVIDER")

    kline_symbol = KLineSymbol.BtcUsdt
    kline_interval = KLineInterval.OneMinute

    start_ts = int(time.time()) - 86400 * 300

    context = BackTestContext(kline_provider, kline_symbol, kline_interval, start_ts)
    context.init_currency_balances(Decimal("0"), Decimal("10000"))
    context.init_exchange_fee_rate(Decimal("0.002"))

    # strategy = IStrategy(context)
    strategy = MovingAverageTrendStrategy(context, 50, 50,
                                          Decimal("0.04"), Decimal("0.04"), Decimal("0.05"))

    kline_cache = BackTestKLineCache(context)

    for kline in kline_cache:
        strategy.run(kline)

    print(strategy.first_kline.close_price)
    print(strategy.last_kline.close_price)

    base_balance, quote_balance = context.get_currency_balances()
    print(base_balance * strategy.last_kline.close_price + quote_balance)

    base_fee, quote_fee = context.get_exchange_fee()
    print(base_fee * strategy.last_kline.close_price + quote_fee)

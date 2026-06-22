import os
import time
from decimal import Decimal

from dotenv import load_dotenv

from context import BackTestContext
from kline_cache import BackTestKLineCache
from enumeration import KLineSymbol, KLineInterval
from strategies.moving_average_trend import MovingAverageTrendStrategy


def main():
    load_dotenv()

    kline_provider = os.environ.get("KLINE_PROVIDER")
    if not kline_provider:
        raise ValueError("KLINE_PROVIDER environment variable is required")

    kline_symbol = KLineSymbol.BtcUsdt
    kline_interval = KLineInterval.OneMinute

    start_ts = int(time.time()) - 86400 * 300

    context = BackTestContext(kline_provider, kline_symbol, kline_interval, start_ts)
    context.init_currency_balances(Decimal("0"), Decimal("10000"))
    context.init_exchange_fee_rate(Decimal("0.002"))

    strategy = MovingAverageTrendStrategy(
        context, 50, 50,
        Decimal("0.04"), Decimal("0.04"), Decimal("0.05")
    )

    kline_cache = BackTestKLineCache(context)

    for kline in kline_cache:
        strategy.run(kline)

    if strategy.first_kline:
        print(strategy.first_kline.close_price)
    if strategy.last_kline:
        print(strategy.last_kline.close_price)

    base_balance, quote_balance = context.get_currency_balances()
    if strategy.last_kline:
        total_value = base_balance * strategy.last_kline.close_price + quote_balance
        print(f"Total value: {total_value}")

    base_fee, quote_fee = context.get_exchange_fee()
    if strategy.last_kline:
        total_fee = base_fee * strategy.last_kline.close_price + quote_fee
        print(f"Total fee: {total_fee}")


if __name__ == "__main__":
    main()

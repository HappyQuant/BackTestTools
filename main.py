"""
BackTestTools - 回测工具入口
"""
import os
import time
from decimal import Decimal

from dotenv import load_dotenv

from data import APIKLineProvider
from domain import Account, KLineSymbol, KLineInterval
from engine import BackTestConfig, BackTestEngine
from strategies import MovingAverageTrendStrategy


def main():
    load_dotenv()

    kline_provider_url = os.environ.get("KLINE_PROVIDER")
    if not kline_provider_url:
        raise ValueError("KLINE_PROVIDER environment variable is required")

    # 创建数据源
    provider = APIKLineProvider(kline_provider_url)

    # 回测配置
    config = BackTestConfig(
        symbol=KLineSymbol.BtcUsdt,
        interval=KLineInterval.OneMinute,
        start_ts=int(time.time()) - 86400 * 300
    )

    # 创建账户
    account = Account()
    account.set_balance(Decimal("0"), Decimal("10000"))
    account.set_fee_rate(Decimal("0.002"))

    # 创建策略
    strategy = MovingAverageTrendStrategy(
        context=account,
        kline_wnd_size=50,
        avg_wnd_size=50,
        buy_volatility_rate=Decimal("0.04"),
        sell_volatility_rate=Decimal("0.04"),
        drawdown_rate=Decimal("0.05")
    )

    # 运行回测
    engine = BackTestEngine(provider, config, account)
    engine.add_strategy(strategy)
    engine.run()

    # 输出结果
    if strategy.last_kline:
        print(f"First price: {strategy.first_kline.close_price}")
        print(f"Last price: {strategy.last_kline.close_price}")

        base, quote = account.get_balance()
        total_value = base * strategy.last_kline.close_price + quote
        print(f"Total value: {total_value}")

        base_fee, quote_fee = account.get_total_fee()
        total_fee = base_fee * strategy.last_kline.close_price + quote_fee
        print(f"Total fee: {total_fee}")


if __name__ == "__main__":
    main()

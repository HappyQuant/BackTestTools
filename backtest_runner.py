"""
回测通用工具模块

提供所有策略共用的环境初始化、账户创建、报告输出等功能
"""
import os
import time
from datetime import datetime
from decimal import Decimal

from dotenv import load_dotenv

from data import APIKLineProvider
from domain import Account, KLineSymbol, KLineInterval, Side
from engine import BackTestConfig, BackTestEngine
from engine.strategy_base import StrategyBase


def format_timestamp(ts: int) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def print_separator():
    print("=" * 60)


def create_provider() -> APIKLineProvider:
    load_dotenv()
    kline_provider_url = os.environ.get("KLINE_PROVIDER")
    if not kline_provider_url:
        raise ValueError("KLINE_PROVIDER environment variable is required")
    return APIKLineProvider(kline_provider_url)


def create_config(
    symbol: KLineSymbol = KLineSymbol.BtcUsdt,
    interval: KLineInterval = KLineInterval.OneMinute,
    days: int = 300
) -> BackTestConfig:
    start_ts = int(time.time()) - 86400 * days
    return BackTestConfig(symbol=symbol, interval=interval, start_ts=start_ts)


def create_account(initial_quote: Decimal = Decimal("10000"), fee_rate: Decimal = Decimal("0.002")) -> Account:
    account = Account()
    account.set_balance(Decimal("0"), initial_quote)
    account.set_fee_rate(fee_rate)
    return account


def print_backtest_report(
    account: Account,
    strategy: StrategyBase,
    config: BackTestConfig,
    initial_quote: Decimal,
    strategy_params: dict
):
    """通用回测报告"""
    print_separator()
    print("回测报告")
    print_separator()

    # 1. 回测配置
    print("\n【回测配置】")
    print(f"  交易对: {config.symbol.value}")
    print(f"  K线周期: {config.interval.value}")
    print(f"  回测区间: {format_timestamp(config.start_ts)} ~ {format_timestamp(config.end_ts)}")
    print(f"  回测时长: {(config.end_ts - config.start_ts) / 86400:.1f} 天")

    # 2. 策略参数
    print("\n【策略参数】")
    for name, value in strategy_params.items():
        if isinstance(value, Decimal):
            print(f"  {name}: {float(value) * 100 if float(value) < 1 and name.endswith('rate') else float(value)}")
        else:
            print(f"  {name}: {value}")

    # 3. 初始资金
    print("\n【初始资金】")
    print(f"  Quote资产: {initial_quote:.2f}")
    print(f"  Base资产: 0")

    # 4. 价格信息
    if strategy.first_kline and strategy.last_kline:
        first_price = strategy.first_kline.close_price
        last_price = strategy.last_kline.close_price
        price_change = (last_price - first_price) / first_price * 100

        print("\n【价格变化】")
        print(f"  起始价格: {first_price:.4f}")
        print(f"  结束价格: {last_price:.4f}")
        print(f"  价格涨幅: {float(price_change):.2f}%")

    # 5. 交易统计
    print("\n【交易统计】")
    if hasattr(strategy, "buy_count"):
        print(f"  买入次数: {strategy.buy_count}")
        print(f"  卖出次数: {strategy.sell_count}")
        print(f"  止损次数: {strategy.stop_loss_count}")
        print(f"  止盈次数: {strategy.take_profit_count}")

    # 6. 最终资产
    base, quote = account.get_balance()
    last_price = strategy.last_kline.close_price if strategy.last_kline else Decimal("0")
    total_value = base * last_price + quote

    print("\n【最终资产】")
    print(f"  Base资产: {base:.8f}")
    print(f"  Quote资产: {quote:.2f}")
    print(f"  总价值(Quote计价): {total_value:.2f}")

    # 7. 收益分析
    profit = total_value - initial_quote
    profit_rate = profit / initial_quote * 100

    print("\n【收益分析】")
    print(f"  绝对收益: {profit:.2f}")
    print(f"  收益率: {float(profit_rate):.2f}%")

    if strategy.first_kline and strategy.last_kline:
        hold_profit_rate = float(
            (strategy.last_kline.close_price - strategy.first_kline.close_price)
            / strategy.first_kline.close_price * 100
        )
        print(f"  持有不动收益率: {hold_profit_rate:.2f}%")
        print(f"  策略超额收益: {float(profit_rate) - hold_profit_rate:.2f}%")

    # 8. 手续费统计
    base_fee, quote_fee = account.get_total_fee()
    total_fee = base_fee * last_price + quote_fee

    print("\n【手续费统计】")
    print(f"  Base手续费: {base_fee:.8f}")
    print(f"  Quote手续费: {quote_fee:.2f}")
    print(f"  总手续费(Quote计价): {total_fee:.2f}")
    print(f"  手续费占收益比例: {float(total_fee / profit * 100) if profit > 0 else 0:.2f}%")

    # 9. 订单详情
    print("\n【订单详情】")
    if account.orders:
        for i, order in enumerate(account.orders):
            ts_str = format_timestamp(order.order_ts // 1000)
            side_str = "买入" if order.side == Side.Buy else "卖出"
            print(f"  #{i + 1} [{ts_str}] {side_str}")
            print(f"      价格: {order.price:.4f}")
            print(f"      数量: {order.quantity:.8f}")
            print(f"      手续费: {order.fee:.8f}")
    else:
        print("  无交易记录")

    print_separator()
    print("回测完成")
    print_separator()

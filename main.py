"""
BackTestTools - 回测工具入口

支持策略：
  1. ma_trend       - 均线趋势策略
  2. dual_ma        - 双均线交叉策略
  3. bollinger      - 布林带策略
  4. rsi            - RSI超买超卖策略
  5. macd           - MACD策略
  6. atr            - ATR追踪止损策略

用法：python main.py <策略名>
示例：python main.py dual_ma
"""

import sys
from decimal import Decimal

from dotenv import load_dotenv

from data import APIKLineProvider
from domain import Account, KLineSymbol, KLineInterval, Side
from engine import BackTestConfig, BackTestEngine
from strategies import MovingAverageTrendStrategy


def format_timestamp(ts: int) -> str:
    """格式化时间戳"""
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def print_separator():
    """打印分隔线"""
    print("=" * 60)


def print_backtest_summary(
    account: Account,
    strategy: MovingAverageTrendStrategy,
    config: BackTestConfig,
    initial_quote: Decimal,
):
    """打印回测摘要"""
    print_separator()
    print("回测报告")
    print_separator()

    # 1. 回测配置信息
    print("\n【回测配置】")
    print(f"  交易对: {config.symbol.value}")
    print(f"  K线周期: {config.interval.value}")
    print(
        f"  回测区间: {format_timestamp(config.start_ts)} ~ {format_timestamp(config.end_ts)}"
    )
    print(f"  回测时长: {(config.end_ts - config.start_ts) / 86400:.1f} 天")

    # 2. 策略参数
    print("\n【策略参数】")
    print(f"  K线窗口: {strategy._kline_wnd_size}")
    print(f"  均线窗口: {strategy._avg_wnd_size}")
    print(f"  买入阈值: {float(strategy._buy_volatility) * 100:.2f}%")
    print(f"  卖险信号阈值: {float(strategy._sell_volatility) * 100:.2f}%")
    print(f"  止损率: {float(strategy._drawdown_rate) * 100:.2f}%")
    if strategy._take_profit_rate:
        print(f"  止盈率: {float(strategy._take_profit_rate) * 100:.2f}%")

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
    print(f"  买入次数: {strategy.buy_count}")
    print(f"  卖险信号次数: {strategy.sell_count}")
    print(f"  止损次数: {strategy.stop_loss_count}")
    if strategy._take_profit_rate:
        print(f"  止盈次数: {strategy.take_profit_count}")

    # 6. 最终资产
    base, quote = account.get_balance()
    last_price = (
        strategy.last_kline.close_price if strategy.last_kline else Decimal("0")
    )
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

    # 计算如果持有不动收益
    if strategy.first_kline and strategy.last_kline:
        hold_profit_rate = float(
            (strategy.last_kline.close_price - strategy.first_kline.close_price)
            / strategy.first_kline.close_price
            * 100
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
    print(
        f"  手续费占收益比例: {float(total_fee / profit * 100) if profit > 0 else 0:.2f}%"
    )

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


def main():
    load_dotenv()

    kline_provider_url = os.environ.get("KLINE_PROVIDER")
    if not kline_provider_url:
        raise ValueError("KLINE_PROVIDER environment variable is required")

    # 创建数据源
    provider = APIKLineProvider(kline_provider_url)

    # 回测配置
    start_ts = int(time.time()) - 86400 * 300
    config = BackTestConfig(
        symbol=KLineSymbol.BtcUsdt, interval=KLineInterval.OneMinute, start_ts=start_ts
    )

    # 初始资金
    initial_quote = Decimal("10000")
    account = create_account(initial_quote)

    strategy = MovingAverageTrendStrategy(
        context=account,
        fast_ma_period=10,
        slow_ma_period=30,
        trend_strength=Decimal("0.002"),
        drawdown_rate=Decimal("0.05"),
        take_profit_rate=Decimal("0.10"),
    )

    engine = BackTestEngine(provider, config, account)
    engine.add_strategy(strategy)
    engine.run()

    print_backtest_report(
        account,
        strategy,
        config,
        initial_quote,
        {
            "K线窗口": strategy._kline_wnd_size,
            "均线窗口": strategy._avg_wnd_size,
            "买入阈值": f"{float(strategy._buy_volatility) * 100:.2f}%",
            "卖出阈值": f"{float(strategy._sell_volatility) * 100:.2f}%",
            "止损率": f"{float(strategy._drawdown_rate) * 100:.2f}%",
            "止盈率": f"{float(strategy._take_profit_rate) * 100:.2f}%",
        },
    )


def run_dual_ma():
    """双均线交叉策略"""
    provider = create_provider()
    config = create_config()
    initial_quote = Decimal("10000")
    account = create_account(initial_quote)

    strategy = DualMACrossStrategy(
        context=account,
        fast_period=10,
        slow_period=30,
        drawdown_rate=Decimal("0.05"),
        take_profit_rate=Decimal("0.10"),
    )

    engine = BackTestEngine(provider, config, account)
    engine.add_strategy(strategy)
    engine.run()

    print_backtest_report(
        account,
        strategy,
        config,
        initial_quote,
        {
            "快线周期": strategy._fast_period,
            "慢线周期": strategy._slow_period,
            "止损率": f"{float(strategy._drawdown_rate) * 100:.2f}%",
            "止盈率": f"{float(strategy._take_profit_rate) * 100:.2f}%",
        },
    )


def run_bollinger():
    """布林带策略"""
    provider = create_provider()
    config = create_config()
    initial_quote = Decimal("10000")
    account = create_account(initial_quote)

    strategy = BollingerBandsStrategy(
        context=account,
        period=20,
        num_std=Decimal("2"),
        drawdown_rate=Decimal("0.05"),
        take_profit_rate=Decimal("0.10"),
    )

    engine = BackTestEngine(provider, config, account)
    engine.add_strategy(strategy)
    engine.run()

    print_backtest_report(
        account,
        strategy,
        config,
        initial_quote,
        {
            "周期": strategy._period,
            "标准差倍数": float(strategy._num_std),
            "止损率": f"{float(strategy._drawdown_rate) * 100:.2f}%",
            "止盈率": f"{float(strategy._take_profit_rate) * 100:.2f}%",
        },
    )


def run_rsi():
    """RSI超买超卖策略"""
    provider = create_provider()
    config = create_config()
    initial_quote = Decimal("10000")
    account = create_account(initial_quote)

    strategy = RSIStrategy(
        context=account,
        period=14,
        oversold_threshold=Decimal("30"),
        overbought_threshold=Decimal("70"),
        drawdown_rate=Decimal("0.05"),
        take_profit_rate=Decimal("0.10"),
    )

    engine = BackTestEngine(provider, config, account)
    engine.add_strategy(strategy)
    engine.run()

    print_backtest_report(
        account,
        strategy,
        config,
        initial_quote,
        {
            "RSI周期": strategy._period,
            "超卖阈值": float(strategy._oversold_threshold),
            "超买阈值": float(strategy._overbought_threshold),
            "止损率": f"{float(strategy._drawdown_rate) * 100:.2f}%",
            "止盈率": f"{float(strategy._take_profit_rate) * 100:.2f}%",
        },
    )


def run_macd():
    """MACD策略"""
    provider = create_provider()
    config = create_config()
    initial_quote = Decimal("10000")
    account = create_account(initial_quote)

    strategy = MACDStrategy(
        context=account,
        fast_period=12,
        slow_period=26,
        signal_period=9,
        drawdown_rate=Decimal("0.05"),
        take_profit_rate=Decimal("0.10"),
    )

    engine = BackTestEngine(provider, config, account)
    engine.add_strategy(strategy)
    engine.run()

    print_backtest_report(
        account,
        strategy,
        config,
        initial_quote,
        {
            "快线周期": strategy._fast_period,
            "慢线周期": strategy._slow_period,
            "信号线周期": strategy._signal_period,
            "止损率": f"{float(strategy._drawdown_rate) * 100:.2f}%",
            "止盈率": f"{float(strategy._take_profit_rate) * 100:.2f}%",
        },
    )


def run_atr():
    """ATR追踪止损策略"""
    provider = create_provider()
    config = create_config()
    initial_quote = Decimal("10000")
    account = create_account(initial_quote)

    strategy = ATRTrailingStopStrategy(
        context=account,
        atr_period=14,
        atr_multiplier=Decimal("2"),
        breakout_period=20,
        take_profit_rate=Decimal("0.10"),
    )

    engine = BackTestEngine(provider, config, account)
    engine.add_strategy(strategy)
    engine.run()

    print_backtest_report(
        account,
        strategy,
        config,
        initial_quote,
        {
            "ATR周期": strategy._atr_period,
            "ATR倍数": float(strategy._atr_multiplier),
            "突破周期": strategy._breakout_period,
            "止盈率": f"{float(strategy._take_profit_rate) * 100:.2f}%",
        },
    )


STRATEGY_MAP = {
    "ma_trend": run_ma_trend,
    "dual_ma": run_dual_ma,
    "bollinger": run_bollinger,
    "rsi": run_rsi,
    "macd": run_macd,
    "atr": run_atr,
}


def main():
    if len(sys.argv) < 2:
        print(f"用法: python main.py <策略名>")
        print(f"可选策略: {', '.join(STRATEGIES)}")
        sys.exit(1)

    name = sys.argv[1]
    if name not in STRATEGY_MAP:
        print(f"未知策略: {name}")
        print(f"可选策略: {', '.join(STRATEGIES)}")
        sys.exit(1)

    STRATEGY_MAP[name]()


def run_comparison():
    """运行多级别对比测试"""
    load_dotenv()

    kline_provider_url = os.environ.get("KLINE_PROVIDER")
    if not kline_provider_url:
        raise ValueError("KLINE_PROVIDER environment variable is required")

    results = run_comparison_backtest(
        provider_url=kline_provider_url,
        symbol=KLineSymbol.BtcUsdt,
        days=300,
        initial_quote=Decimal("10000"),
    )

    print_comparison_report(results)


if __name__ == "__main__":
    main()

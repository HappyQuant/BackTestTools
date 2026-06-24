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

from backtest_runner import create_provider, create_config, create_account, print_backtest_report
from engine import BackTestEngine
from strategies import (
    MovingAverageTrendStrategy,
    DualMACrossStrategy,
    BollingerBandsStrategy,
    RSIStrategy,
    MACDStrategy,
    ATRTrailingStopStrategy,
)

STRATEGIES = [
    "ma_trend", "dual_ma", "bollinger", "rsi", "macd", "atr"
]


def run_ma_trend():
    """均线趋势策略"""
    provider = create_provider()
    config = create_config()
    initial_quote = Decimal("10000")
    account = create_account(initial_quote)

    engine = BackTestEngine(provider, config, account)
    strategy = MovingAverageTrendStrategy(
        context=engine.broker,
        fast_ma_period=10,
        slow_ma_period=50,
        trend_strength=Decimal("0.001"),
        drawdown_rate=Decimal("0.05"),
        take_profit_rate=Decimal("0.10")
    )
    engine.add_strategy(strategy)
    engine.run()

    print_backtest_report(account, strategy, config, initial_quote, {
        "快均线周期": strategy._fast_ma_period,
        "慢均线周期": strategy._slow_ma_period,
        "趋势强度": f"{float(strategy._trend_strength) * 100:.2f}%",
        "止损率": f"{float(strategy._drawdown_rate) * 100:.2f}%",
        "止盈率": f"{float(strategy._take_profit_rate) * 100:.2f}%",
    })


def run_dual_ma():
    """双均线交叉策略"""
    provider = create_provider()
    config = create_config()
    initial_quote = Decimal("10000")
    account = create_account(initial_quote)

    engine = BackTestEngine(provider, config, account)
    strategy = DualMACrossStrategy(
        context=engine.broker,
        fast_period=10,
        slow_period=30,
        drawdown_rate=Decimal("0.05"),
        take_profit_rate=Decimal("0.10")
    )
    engine.add_strategy(strategy)
    engine.run()

    print_backtest_report(account, strategy, config, initial_quote, {
        "快线周期": strategy._fast_period,
        "慢线周期": strategy._slow_period,
        "止损率": f"{float(strategy._drawdown_rate) * 100:.2f}%",
        "止盈率": f"{float(strategy._take_profit_rate) * 100:.2f}%",
    })


def run_bollinger():
    """布林带策略"""
    provider = create_provider()
    config = create_config()
    initial_quote = Decimal("10000")
    account = create_account(initial_quote)

    engine = BackTestEngine(provider, config, account)
    strategy = BollingerBandsStrategy(
        context=engine.broker,
        period=20,
        num_std=Decimal("2"),
        drawdown_rate=Decimal("0.05"),
        take_profit_rate=Decimal("0.10")
    )
    engine.add_strategy(strategy)
    engine.run()

    print_backtest_report(account, strategy, config, initial_quote, {
        "周期": strategy._period,
        "标准差倍数": float(strategy._num_std),
        "止损率": f"{float(strategy._drawdown_rate) * 100:.2f}%",
        "止盈率": f"{float(strategy._take_profit_rate) * 100:.2f}%",
    })


def run_rsi():
    """RSI超买超卖策略"""
    provider = create_provider()
    config = create_config()
    initial_quote = Decimal("10000")
    account = create_account(initial_quote)

    engine = BackTestEngine(provider, config, account)
    strategy = RSIStrategy(
        context=engine.broker,
        period=14,
        oversold_threshold=Decimal("30"),
        overbought_threshold=Decimal("70"),
        drawdown_rate=Decimal("0.05"),
        take_profit_rate=Decimal("0.10")
    )
    engine.add_strategy(strategy)
    engine.run()

    print_backtest_report(account, strategy, config, initial_quote, {
        "RSI周期": strategy._period,
        "超卖阈值": float(strategy._oversold_threshold),
        "超买阈值": float(strategy._overbought_threshold),
        "止损率": f"{float(strategy._drawdown_rate) * 100:.2f}%",
        "止盈率": f"{float(strategy._take_profit_rate) * 100:.2f}%",
    })


def run_macd():
    """MACD策略"""
    provider = create_provider()
    config = create_config()
    initial_quote = Decimal("10000")
    account = create_account(initial_quote)

    engine = BackTestEngine(provider, config, account)
    strategy = MACDStrategy(
        context=engine.broker,
        fast_period=12,
        slow_period=26,
        signal_period=9,
        drawdown_rate=Decimal("0.05"),
        take_profit_rate=Decimal("0.10")
    )
    engine.add_strategy(strategy)
    engine.run()

    print_backtest_report(account, strategy, config, initial_quote, {
        "快线周期": strategy._fast_period,
        "慢线周期": strategy._slow_period,
        "信号线周期": strategy._signal_period,
        "止损率": f"{float(strategy._drawdown_rate) * 100:.2f}%",
        "止盈率": f"{float(strategy._take_profit_rate) * 100:.2f}%",
    })


def run_atr():
    """ATR追踪止损策略"""
    provider = create_provider()
    config = create_config()
    initial_quote = Decimal("10000")
    account = create_account(initial_quote)

    engine = BackTestEngine(provider, config, account)
    strategy = ATRTrailingStopStrategy(
        context=engine.broker,
        atr_period=14,
        atr_multiplier=Decimal("2"),
        breakout_period=20,
        take_profit_rate=Decimal("0.10")
    )
    engine.add_strategy(strategy)
    engine.run()

    print_backtest_report(account, strategy, config, initial_quote, {
        "ATR周期": strategy._atr_period,
        "ATR倍数": float(strategy._atr_multiplier),
        "突破周期": strategy._breakout_period,
        "止盈率": f"{float(strategy._take_profit_rate) * 100:.2f}%",
    })


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


if __name__ == "__main__":
    main()

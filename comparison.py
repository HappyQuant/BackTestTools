"""
多级别K线策略对比测试

支持不同K线周期和策略参数的对比测试
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional

from data import APIKLineProvider
from domain import Account, KLineSymbol, KLineInterval
from engine import BackTestConfig, BackTestEngine
from strategies import MovingAverageTrendStrategy


@dataclass
class StrategyConfig:
    """策略配置"""
    fast_ma_period: int
    slow_ma_period: int
    trend_strength: Decimal
    drawdown_rate: Decimal
    take_profit_rate: Optional[Decimal] = None


@dataclass
class BacktestResult:
    """回测结果"""
    interval: KLineInterval
    strategy_config: StrategyConfig
    buy_count: int
    sell_count: int
    stop_loss_count: int
    take_profit_count: int
    total_value: Decimal
    profit_rate: Decimal
    hold_profit_rate: Decimal
    excess_return: Decimal
    total_fee: Decimal
    initial_quote: Decimal

    def __str__(self) -> str:
        return (
            f"  K线周期: {self.interval.value}\n"
            f"  策略参数: 快均线={self.strategy_config.fast_ma_period}, "
            f"慢均线={self.strategy_config.slow_ma_period}, "
            f"趋势强度={float(self.strategy_config.trend_strength)*100:.2f}%\n"
            f"  交易次数: 买入={self.buy_count}, 卖出={self.sell_count}, "
            f"止损={self.stop_loss_count}, 止盈={self.take_profit_count}\n"
            f"  收益率: {float(self.profit_rate):.2f}% (持有不动: {float(self.hold_profit_rate):.2f}%)\n"
            f"  超额收益: {float(self.excess_return):.2f}%\n"
            f"  总手续费: {float(self.total_fee):.2f}"
        )


# 预设策略配置
STRATEGY_PRESETS = {
    "conservative": StrategyConfig(
        fast_ma_period=20,
        slow_ma_period=50,
        trend_strength=Decimal("0.003"),
        drawdown_rate=Decimal("0.03"),
        take_profit_rate=Decimal("0.08")
    ),
    "balanced": StrategyConfig(
        fast_ma_period=10,
        slow_ma_period=30,
        trend_strength=Decimal("0.002"),
        drawdown_rate=Decimal("0.05"),
        take_profit_rate=Decimal("0.10")
    ),
    "aggressive": StrategyConfig(
        fast_ma_period=5,
        slow_ma_period=20,
        trend_strength=Decimal("0.001"),
        drawdown_rate=Decimal("0.08"),
        take_profit_rate=Decimal("0.15")
    ),
}

# K线周期配置
INTERVAL_CONFIGS = [
    KLineInterval.OneMinute,
    KLineInterval.FiveMinute,
    KLineInterval.FifteenMinute,
    KLineInterval.OneHour,
    KLineInterval.FourHour,
]


def run_single_backtest(
    provider: APIKLineProvider,
    symbol: KLineSymbol,
    interval: KLineInterval,
    start_ts: int,
    end_ts: int,
    strategy_config: StrategyConfig,
    initial_quote: Decimal = Decimal("10000"),
    fee_rate: Decimal = Decimal("0.002")
) -> BacktestResult:
    """运行单个回测"""
    config = BackTestConfig(
        symbol=symbol,
        interval=interval,
        start_ts=start_ts,
        end_ts=end_ts
    )

    account = Account()
    account.set_balance(Decimal("0"), initial_quote)
    account.set_fee_rate(fee_rate)

    strategy = MovingAverageTrendStrategy(
        context=account,
        fast_ma_period=strategy_config.fast_ma_period,
        slow_ma_period=strategy_config.slow_ma_period,
        trend_strength=strategy_config.trend_strength,
        drawdown_rate=strategy_config.drawdown_rate,
        take_profit_rate=strategy_config.take_profit_rate
    )

    engine = BackTestEngine(provider, config, account)
    engine.add_strategy(strategy)
    engine.run()

    # 计算结果
    base, quote = account.get_balance()
    last_price = strategy.last_kline.close_price if strategy.last_kline else Decimal("0")
    total_value = base * last_price + quote

    profit_rate = (total_value - initial_quote) / initial_quote * 100

    hold_profit_rate = Decimal("0")
    if strategy.first_kline and strategy.last_kline:
        hold_profit_rate = (
            (strategy.last_kline.close_price - strategy.first_kline.close_price)
            / strategy.first_kline.close_price * 100
        )

    base_fee, quote_fee = account.get_total_fee()
    total_fee = base_fee * last_price + quote_fee

    return BacktestResult(
        interval=interval,
        strategy_config=strategy_config,
        buy_count=strategy.buy_count,
        sell_count=strategy.sell_count,
        stop_loss_count=strategy.stop_loss_count,
        take_profit_count=strategy.take_profit_count,
        total_value=total_value,
        profit_rate=profit_rate,
        hold_profit_rate=hold_profit_rate,
        excess_return=profit_rate - hold_profit_rate,
        total_fee=total_fee,
        initial_quote=initial_quote
    )


def run_comparison_backtest(
    provider_url: str,
    symbol: KLineSymbol = KLineSymbol.BtcUsdt,
    days: int = 30,
    intervals: Optional[List[KLineInterval]] = None,
    presets: Optional[List[str]] = None,
    initial_quote: Decimal = Decimal("10000")
) -> List[BacktestResult]:
    """运行对比回测"""
    import time

    provider = APIKLineProvider(provider_url)
    end_ts = int(time.time())
    start_ts = end_ts - 86400 * days

    if intervals is None:
        intervals = INTERVAL_CONFIGS
    if presets is None:
        presets = ["conservative", "balanced", "aggressive"]

    results = []

    for interval in intervals:
        for preset_name in presets:
            if preset_name not in STRATEGY_PRESETS:
                continue

            strategy_config = STRATEGY_PRESETS[preset_name]
            print(f"Running: {interval.value} with {preset_name} preset...")

            try:
                result = run_single_backtest(
                    provider=provider,
                    symbol=symbol,
                    interval=interval,
                    start_ts=start_ts,
                    end_ts=end_ts,
                    strategy_config=strategy_config,
                    initial_quote=initial_quote
                )
                results.append(result)
            except Exception as e:
                print(f"  Error: {e}")

    return results


def print_comparison_report(results: List[BacktestResult]) -> None:
    """打印对比报告"""
    print("\n" + "=" * 70)
    print("多级别K线策略对比报告")
    print("=" * 70)

    if not results:
        print("无回测结果")
        return

    # 按收益率排序
    sorted_results = sorted(results, key=lambda r: r.profit_rate, reverse=True)

    print(f"\n共 {len(results)} 组回测结果，按收益率排序：\n")

    for i, result in enumerate(sorted_results, 1):
        print(f"[{i}]")
        print(result)
        print()

    # 最佳配置
    best = sorted_results[0]
    print("=" * 70)
    print("最佳配置：")
    print(f"  K线周期: {best.interval.value}")
    print(f"  策略: 快均线={best.strategy_config.fast_ma_period}, "
          f"慢均线={best.strategy_config.slow_ma_period}")
    print(f"  收益率: {float(best.profit_rate):.2f}%")
    print("=" * 70)

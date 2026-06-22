# BackTestTools

一个模块化的回测工具框架，支持多数据源、多策略并行运行。

## 项目结构

```
BackTestTools/
├── domain/                    # 领域模型层 (无外部依赖)
│   ├── enumeration.py        # 枚举定义
│   ├── kline.py              # K线实体 (不可变)
│   ├── order.py              # 订单实体
│   └── account.py            # 账户管理
│
├── data/                      # 数据层 (依赖 domain)
│   ├── provider.py           # IKLineProvider 接口
│   ├── api_provider.py       # API 数据源实现
│   └── memory_provider.py    # 内存数据源 (测试用)
│
├── engine/                    # 回测引擎 (依赖 domain + data)
│   ├── config.py             # 回测配置
│   ├── feeder.py             # K线数据迭代器
│   ├── strategy_base.py      # 策略基类 + 接口
│   └── engine.py             # 回测引擎核心
│
├── strategies/                # 策略实现
│   └── moving_average_trend.py
│
├── tests/                     # 单元测试
│   ├── test_domain.py
│   ├── test_data.py
│   ├── test_engine.py
│   └── test_strategy.py
│
└── main.py                    # 入口文件
```

## 核心特性

- **多数据源支持**: 通过 `IKLineProvider` 接口，可轻松切换 API/内存/文件数据源
- **策略解耦**: 策略只依赖 `ITradingContext` Protocol，不依赖具体实现
- **多策略并行**: `BackTestEngine.add_strategy()` 支持多策略同时运行
- **单元测试覆盖**: 完整的测试用例覆盖核心模块

## 安装说明

```bash
pipenv install
```

## 快速开始

```bash
# 设置环境变量
export KLINE_PROVIDER=http://your-api-server:8080

# 运行回测
python main.py
```

## 自定义数据源

```python
from data import IKLineProvider
from domain import KLine, KLineSymbol, KLineInterval

class MyCustomProvider(IKLineProvider):
    def fetch_next_klines(self, symbol, interval, from_time, limit):
        # 实现你的数据获取逻辑
        return [KLine(...), ...]
    
    def fetch_previous_klines(self, symbol, interval, end_time, limit):
        # 实现你的数据获取逻辑
        return [KLine(...), ...]
```

## 自定义策略

```python
from engine import StrategyBase
from domain import KLine

class MyStrategy(StrategyBase):
    def _process_kline(self, kline: KLine):
        # 实现你的策略逻辑
        base, quote = self.context.get_balance()
        
        if base > 0:
            # 持仓逻辑
            self.context.sell(kline.open_time, kline.close_price, base)
        else:
            # 空仓逻辑
            quantity = quote / kline.close_price
            self.context.buy(kline.open_time, kline.close_price, quantity)
```

## 运行测试

```bash
python -m unittest discover -s tests -v
```

## 依赖关系

```
domain (无依赖)
   ↑
   ├── data
   ├── engine
   └── strategies
         ↑
        main.py
```

## 许可证

MIT License
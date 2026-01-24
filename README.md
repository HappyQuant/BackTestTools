# BackTestTools

一个简单快速的交易回测框架，用于测试和验证交易策略的性能。

## 项目简介

BackTestTools 是一个轻量级的交易回测框架，专注于提供简洁、高效的回测环境，帮助交易者测试各种交易策略的表现。框架支持K线数据获取、策略执行、资产计算和手续费统计等功能。

## 核心功能

- **K线数据管理**：支持获取和缓存K线数据
- **回测上下文**：管理资产余额、订单记录和手续费计算
- **策略实现**：内置移动平均线趋势策略示例
- **精度计算**：使用 Decimal 类型确保计算精度
- **灵活配置**：支持自定义交易对、K线级别、手续费率等参数

## 项目结构

```
BackTestTools/
├── strategies/           # 策略目录
│   ├── __init__.py
│   └── moving_average_trend.py  # 移动平均线趋势策略
├── test/                 # 测试目录
│   └── test_kline.py     # K线测试文件
├── context.py            # 回测上下文
├── enumeration.py        # 枚举定义
├── executor.py           # 主执行文件
├── kline.py              # K线数据结构
├── kline_cache.py        # K线缓存
├── kline_cli.py          # K线命令行工具
├── order.py              # 订单结构
├── Pipfile               # 依赖管理
├── Pipfile.lock          # 依赖锁定
├── LICENSE               # 许可证
└── README.md             # 项目说明
```

## 安装说明

### 前提条件

- Python 3.7+
- pipenv

### 安装步骤

1. 克隆项目到本地
2. 进入项目目录
3. 安装依赖

```bash
pipenv lock
pipenv install
```

## 使用方法

### 基本使用

运行默认的移动平均线趋势策略回测：

```bash
pipenv run python executor.py
```

### 自定义策略

1. 在 `strategies` 目录下创建新的策略文件
2. 继承 `IStrategy` 基类并实现 `run` 方法
3. 在 `executor.py` 中导入并使用自定义策略

### 配置参数

在 `executor.py` 中可以修改以下参数：

- `kline_provider`：K线数据源
- `kline_symbol`：交易对
- `kline_interval`：K线级别
- `start_ts`：回测开始时间
- `strategy`：使用的策略及参数

## 策略示例

### 移动平均线趋势策略

`MovingAverageTrendStrategy` 是一个基于移动平均线的趋势跟随策略，主要参数包括：

- `kline_wnd_size`：K线滑动窗口大小
- `avg_line_wnd_size`：均线滑动窗口大小
- `buy_volatility_rate`：买入波动率阈值
- `sell_volatility_rate`：卖出波动率阈值
- `drawdown_rate`：止损率

策略逻辑：
1. 计算K线收盘价的移动平均值
2. 基于移动平均线的变化趋势判断买入/卖出信号
3. 当价格下跌超过止损率时执行止损操作

## 回测结果

回测完成后，系统会输出以下信息：

- 首根K线收盘价
- 末根K线收盘价
- 最终资产价值（base资产 * 末根K线收盘价 + quote资产）
- 总手续费消耗（base手续费 * 末根K线收盘价 + quote手续费）

## 扩展指南

### 添加新策略

1. 在 `strategies` 目录创建新的策略文件
2. 实现 `IStrategy` 接口
3. 在 `executor.py` 中配置使用新策略

### 自定义K线数据源

1. 修改 `kline_cli.py` 中的 `get_next_klines` 函数
2. 实现自定义的K线数据获取逻辑

## 依赖管理

项目使用 pipenv 管理依赖，主要依赖包括：

- `python-dotenv`：环境变量管理
- `_decimal`：高精度数值计算

## 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

## 贡献指南

欢迎提交 Issue 和 Pull Request 来改进这个项目。

## 联系方式

如果有任何问题或建议，请随时联系项目维护者。
from enum import Enum


class KLineSymbol(Enum):
    BtcUsdt = "BTCUSDT"
    EthUsdt = "ETHUSDT"
    LtcUsdt = "LTCUSDT"


class KLineInterval(Enum):
    OneMinute = "1m"
    ThreeMinute = "3m"
    FiveMinute = "5m"
    FifteenMinute = "15m"
    ThirtyMinute = "30m"
    OneHour = "1h"
    TwoHour = "2h"
    FourHour = "4h"
    SixHour = "6h"
    EightHour = "8h"
    TwelveHour = "12h"
    OneDay = "1d"


class Side(Enum):
    Buy = "buy"
    Sell = "sell"

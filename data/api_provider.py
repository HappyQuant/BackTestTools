from typing import List

import requests

from data.provider import IKLineProvider
from domain import KLine, KLineSymbol, KLineInterval
from domain.kline import Decimal


class KLineAPIError(Exception):
    """K线API请求错误"""
    pass


class APIKLineProvider(IKLineProvider):
    """API数据源实现"""

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _fetch_klines(
        self,
        symbol: KLineSymbol,
        interval: KLineInterval,
        direction: str,
        time_param: int,
        limit: int
    ) -> List[KLine]:
        if limit > 1000:
            raise ValueError("limit cannot exceed 1000")

        time_key = "endTime" if direction == "previous" else "fromTime"
        url = (
            f"{self.base_url}/api/kline/{symbol.value}/{interval.value}/{direction}"
            f"?{time_key}={time_param * 1000}&limit={limit}"
        )

        session = requests.Session()
        session.trust_env = False

        try:
            resp = session.get(url=url, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.Timeout:
            raise KLineAPIError(f"Request timeout for {url}")
        except requests.exceptions.HTTPError as e:
            raise KLineAPIError(f"HTTP error: {e}")
        except requests.exceptions.RequestException as e:
            raise KLineAPIError(f"Request failed: {e}")

        return [
            KLine(
                open_time=item["open_time"],
                open_price=Decimal(item["open_price"]),
                close_price=Decimal(item["close_price"]),
                high_price=Decimal(item["high_price"]),
                low_price=Decimal(item["low_price"])
            )
            for item in data
        ]

    def fetch_next_klines(
        self,
        symbol: KLineSymbol,
        interval: KLineInterval,
        from_time: int,
        limit: int
    ) -> List[KLine]:
        return self._fetch_klines(symbol, interval, "next", from_time, limit)

    def fetch_previous_klines(
        self,
        symbol: KLineSymbol,
        interval: KLineInterval,
        end_time: int,
        limit: int
    ) -> List[KLine]:
        return self._fetch_klines(symbol, interval, "previous", end_time, limit)

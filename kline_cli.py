import json
import requests

from enumeration import KLineSymbol, KLineInterval


def _fetch_klines(kline_provider: str, symbol: KLineSymbol, interval: KLineInterval,
                  direction: str, time_param: int, limit: int, proxies: dict = None) -> list:
    assert limit <= 1000
    url = '{}/api/kline/{}/{}/{}?{}={}&&limit={}'.format(
        kline_provider, symbol.value, interval.value, direction,
        'endTime' if direction == 'previous' else 'fromTime', time_param * 1000, limit
    )
    session = requests.Session()
    session.trust_env = False
    resp = session.get(url=url, proxies=proxies)
    return json.loads(resp.text)


def get_previous_klines(kline_provider: str, symbol: KLineSymbol, interval: KLineInterval,
                        end_time: int, limit: int, proxies: dict = None) -> list:
    return _fetch_klines(kline_provider, symbol, interval, 'previous', end_time, limit, proxies)


def get_next_klines(kline_provider: str, symbol: KLineSymbol, interval: KLineInterval,
                    from_time: int, limit: int, proxies: dict = None) -> list:
    return _fetch_klines(kline_provider, symbol, interval, 'next', from_time, limit, proxies)
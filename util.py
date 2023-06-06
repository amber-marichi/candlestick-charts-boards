import json
from datetime import datetime

import requests


from conf import API_URL


def fetch_candlesticks(symb: str = "BNBUSDT", limit: str = 8, interval: str = "30m"):
    data = []

    params = {
        "symbol": symb,
        "interval": interval,
        "limit": limit,
    }

    response = requests.get(API_URL, params=params)

    if response.status_code == 200:
        hist_candles = json.loads(response.text)
        for candle in hist_candles:

            timestamp = candle[6]
            timestamp /= 1000
            data.append((
                datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S"),
                candle[1],
                candle[2],
                candle[3],
                candle[4]
            ))
    return data

import websocket
import json
from datetime import datetime
from decimal import Decimal
from threading import Thread

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from util import fetch_candlesticks
import conf


class MyCandlestickApp:
    def __init__(self) -> None:
        self.chart = st.empty()
        self.sma_alerts = st.empty()
        self._sma_limit = 3
        self._curr_steak = 0
        self._data = []
        self._sma_list = []
    
    @staticmethod
    def _on_open(ws) -> None:
        print("Connection opened")

    @staticmethod
    def _on_error(ws, error) -> None:
        print(error)

    @staticmethod
    def _on_close(ws, close_status_code, close_msg) -> None:
        print("Connection closed", close_status_code, close_msg)

    def _on_message(self, ws, message) -> None:
        print(message)
        data = json.loads(message)
        current_candle = data["k"]
        if current_candle["x"]:
            timestamp = current_candle["T"]
            timestamp /= 1000
            conv_date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

            _new_row = (
                conv_date,
                current_candle["o"],
                current_candle["h"],
                current_candle["l"],
                current_candle["c"]
            )

            self._data.append(_new_row)
            self._data.pop(0)
            self._update_sma(conv_date, current_candle["c"])
            self._update_charts()

    def _update_charts(self) -> None:
        candles = pd.DataFrame(self._data, columns=["DateTime", "Open", "High", "Low", "Close"])
        sma_chart = pd.DataFrame(self._sma_list, columns=["DateTime", "SMA"])
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=candles["DateTime"],
            open=candles["Open"],
            high=candles["High"],
            low=candles["Low"],
            close=candles["Close"])
        )
        fig.add_trace(go.Scatter(
            x=sma_chart["DateTime"],
            y=sma_chart["SMA"],
            mode="lines+markers",
            name="SMA Value",
            line=dict(color="#5c3566"))
        )
        self.chart.plotly_chart(fig, use_container_width=True)

    def _update_sma(self, timestamp: str, close: str) -> None:
        curr_sma = sum(Decimal(unit[-1]) for unit in self._data) / len(self._data)
        self._sma_list.append((timestamp, curr_sma))
        if len(self._sma_list) > self.candles:
            self._sma_list.pop(0)
        if curr_sma >= Decimal(close):
            self._curr_steak += 1
            if self._curr_steak >= self._sma_limit:
                self.sma_alerts.warning(
                    f"{timestamp} - SMA is {curr_sma} and exceeds close value {close}"
                )
        else:
            self._curr_steak = 0

    def run(self, symbol: str, candle_count: int, timer: str) -> None:
        self.candles = candle_count
        self._data = fetch_candlesticks(symbol, candle_count, timer)
        self._update_sma(self._data[-1][0], self._data[-1][-1])
        self._update_charts()
        self._ws = websocket.WebSocketApp(
            conf.SOCK_URL.format(symbol=symbol.lower(), timer=timer),
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )

        self._ws.run_forever()


app = MyCandlestickApp()

st.title("Check the candlecharts and SMA")

with st.sidebar:
    timelimit = st.selectbox(
        label="Select time limit",
        options=conf.timestamps,
        index=conf.timestamps.index("30m"),
    )

    binance_symbols = st.selectbox(
        label="Select binance symbol",
        options=conf.symbols,
        index=conf.symbols.index("BNBUSDT"),
    )

    candle_count = st.number_input(
        label="Number of candles to display",
        min_value=1,
        max_value=20,
        value=8,
    )

    if st.button("Get Candlecharts"):
        st.write("Updating...")
        app.run(binance_symbols, candle_count, timelimit)

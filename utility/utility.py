import plotly.graph_objects as go
import pandas as pd
import os
import random
import yfinance as yf
import datetime
from XTBClient.api import XTBClient, MODES


class CandleStick(go.Figure):
    def __init__(self, df, add_MAs=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._df = df.set_index("datetime")
        self.add_trace(
            go.Candlestick(
                x=self._df.index,
                open=self._df.open,
                close=self._df.close,
                high=self._df.high,
                low=self._df.low,
                line=dict(width=1),
                opacity=1,
                increasing_fillcolor="#24A06B",
                decreasing_fillcolor="#CC2E3C",
                increasing_line_color="#2EC886",
                decreasing_line_color="#FF3A4C",
            )
        )
        self.update_layout(
            margin=dict(l=0, r=0, b=0, t=0),
            font=dict(size=10, color="#e1e1e1"),
            paper_bgcolor="#1e1e1e",
            plot_bgcolor="#1e1e1e",
        )
        self.update_xaxes(
            gridcolor="#fff", showgrid=True, rangeslider=dict(visible=False)
        )
        self.update_yaxes(gridcolor="#1f292f", showgrid=True)

        if add_MAs:
            for ma in [col for col in self._df.columns if "MA" in col]:
                self._add_line(self._df.index, self._df[ma])

        self.mark_trades()

    def _add_line(self, x, y, color=None):
        if not color:
            color = "#" + "".join(
                [random.choice("0123456789ABCDEF") for j in range(6)]
            )
        self.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines",
                marker=dict(color=color, size=25),
                name=y.name,
            )
        )

    def mark_trades(self):
        trades = self._df[self._df.is_trade != 0]
        for trade in trades.iterrows():
            self.add_vline(
                x=trade[0],
                line_width=5,
                line_dash="dash",
                line_color="green" if trade[1].is_trade > 0 else "red",
            )


def get_df(symbol):
    return pd.read_csv(os.path.join("csvs", symbol + "_data.csv"))


def collect_yf(symbol, period, interval):
    def adjust_df(df):
        df.index = df.index + datetime.timedelta(hours=1)
        df.reset_index(inplace=True)
        for col in df.columns:
            df.rename(columns={col: col.lower()}, inplace=True)
        df.drop(["volume"], axis=1, inplace=True)
        # df.reset_index(inplace=True)
        # if "Datetime" not in df.columns:
        # df['Datetime'] = df.index

    df = yf.download("EURUSD=x", period=period, interval=interval)
    adjust_df(df)

    if not os.path.exists('csvs'):
        os.makedirs('csvs')
    df[[col for col in df.columns if col not in "index"]].to_csv(
        os.path.join("csvs", symbol + "_data.csv"), index=False
    )
    return df


def analyze(df, means):
    target = df["close"]

    ma_cols = []
    for i, mean in enumerate(means):
        name = "MA_" + str(mean)
        df[name] = target.rolling(window=mean).mean()
        df[name] = df[name].shift(periods=i)
        ma_cols.append(name)

    df["diff"] = df[ma_cols[0]] - df[ma_cols[1]]
    df["diff"] = df["diff"].astype(float)
    df["diff_prev"] = df["diff"].shift(1)

    df.dropna(how="any", inplace=True)
    df.reset_index(drop=True, inplace=True)

    def is_trade(row):
        if row["diff"] >= 0 and row["diff_prev"] < 0:
            return 1
        if row["diff"] <= 0 and row["diff_prev"] > 0:
            return -1

        return 0

    df["is_trade"] = df.apply(is_trade, axis=1)

    # return df.iloc[0]["is_trade"]
    df_trades = df[df.is_trade != 0].copy().reset_index()

    df_trades["delta"] = (df_trades.close.diff() / 0.0001).shift(-1)
    df_trades["gain"] = (
        df_trades["delta"] * df_trades["is_trade"] + 10 * df_trades["is_trade"]
    )


def open_transaction(mode: MODES, symbol: str, tp=0, sl=0, volume=0.01):
    client = XTBClient()
    client.login(
        os.environ.get("XTB_login"), os.environ.get("XTB_pass")
    )
    client.open_transaction(mode, symbol, volume, tp=tp, sl=sl)
    client.logout()

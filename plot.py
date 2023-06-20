import dash
import logging
import os
from datetime import datetime, timedelta
from dash import dcc
from dash import html
from utility import utility
from dash.dependencies import Output, Input
from XTBClient.api import XTBClient, MODES
from dotenv import load_dotenv

load_dotenv()

YF_SYMBOL = os.environ.get("yf_symbol")
SYMBOL = os.environ.get("xtb_symbol")
PERIOD = os.environ.get("period")
INTERVAL = os.environ.get("interval")
MEAN1 = int(os.environ.get("mean1"))
MEAN2 = int(os.environ.get("mean2"))
VOLUME = float(os.environ.get("volume"))
USER_NUM = os.environ.get("XTB_user_num")
PASSWORD = os.environ.get("XTB_pass")

target_time = datetime.now() + timedelta(minutes=1)
time = 60

# LOGGER
logFormatter = logging.Formatter(
    "%(asctime)s\t%(levelname)s\t%(buy_or_sell)s TRANSACTION "
    + "%(status)s\t%(message)s"
)
logger = logging.getLogger(__name__)

fileHandler = logging.FileHandler(".log")
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)

logger.setLevel(logging.INFO)


# LAYOUT
external_scripts = [
    {"src": "https://code.jquery.com/jquery-3.5.1.min.js"},
    {"src": "./assets/actions.js"},
]

app = dash.Dash(
    __name__,
    url_base_pathname="/{}/".format(os.environ.get("path_prefix")),
    external_scripts=external_scripts,
)


app.layout = html.Div(
    [
        dcc.Graph(
            id="candlestick-chart",
            style={"width": "100%", "height": "100vh"},
        ),
        dcc.Interval(
            id="interval-component",
            interval=60000,
            n_intervals=0,
        ),
        html.Div(
            [
                html.Button(id="hide-button"),
                html.Div(
                    [html.H2("Symbol: "), html.H2(SYMBOL)],
                    className="parameter",
                ),
                html.Div(
                    [html.H2("Countdown: "), html.H2(id="countdown")],
                    className="parameter",
                ),
                html.Div(
                    [
                        html.H2("Profit: "),
                        html.H2(id="profit"),
                    ],
                    className="parameter",
                ),
                dcc.Interval(id="interval", interval=1000, n_intervals=0),
            ],
            id="info",
        ),
    ],
    className="container",
)


def report(status):
    status["status"] = status["request_status"].name
    logger.info(status.pop("message"), extra=status)


@app.callback(
    Output("candlestick-chart", "figure"),
    [Input("interval-component", "n_intervals")],
)
def update_candlestick_chart(n):
    global target_time

    df = utility.collect_yf(YF_SYMBOL, PERIOD, INTERVAL)
    utility.analyze(df, means=[MEAN1, MEAN2])
    # df = get_df("EURUSD")
    # df = df[-50:]

    target_time = datetime.now() + timedelta(minutes=1)
    action_marker = df.iloc[-1].is_trade
    if action_marker != 0:
        client = XTBClient()
        client.login(USER_NUM, PASSWORD)

        status = client.close_all()
        # utility.report(status)

        status = client.open_transaction(
            MODES.BUY if action_marker > 0 else MODES.SELL,
            SYMBOL,
            volume=VOLUME,
            # tp=10,
            # sl=20,
        )
        status["buy_or_sell"] = "BUY" if action_marker > 0 else "SELL"
        report(status)
        client.logout()

    fig = utility.CandleStick(df)
    fig["layout"]["uirevision"] = "some-constant"

    return fig


# Update the countdown value
@app.callback(
    dash.dependencies.Output("countdown", "children"),
    dash.dependencies.Input("interval", "n_intervals"),
)
def update_countdown(n):
    global time, target_time

    current_time = datetime.now()
    remaining_time = target_time - current_time

    remaining_seconds = remaining_time.total_seconds()

    return str(int(remaining_seconds))


# Update the countdown value
@app.callback(
    dash.dependencies.Output("profit", "children"),
    dash.dependencies.Input("interval-component", "n_intervals"),
)
def update_profit(n):
    client = XTBClient()
    client.login(USER_NUM, PASSWORD)
    profit = client.get_profits()
    client.logout()
    return str(profit)


if __name__ == "__main__":
    app.run_server(port=8000, host="0.0.0.0", debug=True)

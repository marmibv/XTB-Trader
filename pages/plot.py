import dash
import logging
import os
from datetime import datetime, timedelta
from tabulate import tabulate
from dash import dcc, html, callback
from utility import utility
from dash.dependencies import Output, Input
from XTBClient.api import XTBClient, MODES
from dotenv import load_dotenv
import plotly.graph_objects as go

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


def logger_init():
    logFormatter = logging.Formatter(
        "%(asctime)s  %(levelname)-5s  %(theme)-9s  "
        + "%(status)-8s  %(message)s"
    )
    logger = logging.getLogger(__name__)

    fileHandler = logging.FileHandler(".log")
    fileHandler.setFormatter(logFormatter)
    logger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)

    logger.setLevel(logging.INFO)

    return logger


logger = logger_init()

dash.register_page(__name__)


layout = html.Div(
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
        html.Button(id="hide-button"),
        html.Div(
            [
                html.Div(
                    [html.H2("Symbol: "), html.H2(SYMBOL)],
                    className="parameter",
                ),
                html.Div(
                    [html.H2("Countdown: "), html.H2(id="countdown")],
                    className="parameter",
                ),
                html.Div(
                    [html.H2("Profit: "), html.H2(id="profit")],
                    className="parameter",
                ),
                dcc.Interval(id="interval", interval=1000, n_intervals=0),
            ],
            className="info",
            id="info",
        ),
        html.Div(
            [html.Pre(id="logs-plot-page")],
        ),
        dcc.Interval(id="logs-plot-interval", interval=2000, n_intervals=0),
    ],
    className="container",
)


def report(status):
    status["status"] = status["request_status"].name

    if status.get("message") is None:
        status["message"] = "-"
    logger.info(status.pop("message"), extra=status)


def err(message):
    logger.error(message, extra={"theme": "", "status": "ERROR"})


@callback(
    Output("candlestick-chart", "figure"),
    [Input("interval-component", "n_intervals")],
)
def update_candlestick_chart(n):
    global target_time

    df = None
    try:
        df = utility.collect_yf(YF_SYMBOL, PERIOD, INTERVAL)
    except Exception as e:
        err(str(e))
        return go.Figure()

    utility.analyze(df, means=[MEAN1, MEAN2])

    target_time = datetime.now() + timedelta(minutes=1)
    action_marker = df.iloc[-1].is_trade
    action_marker = 1
    if action_marker != 0:
        try:
            client = XTBClient()
            client.login(USER_NUM, PASSWORD)

            # CLOSE ALL
            profits = str(client.get_profits())
            status = client.close_all()
            status["message"] += " PROFIT: " + profits
            status["theme"] = "CLOSE ALL"
            report(status)

            # OPEN NEW
            status = client.open_transaction(
                MODES.BUY if action_marker > 0 else MODES.SELL,
                SYMBOL,
                volume=VOLUME,
                # tp=10,
                # sl=20,
            )
            status["theme"] = "NEW BUY" if action_marker > 0 else "NEW SELL"

            report(status)

            client.logout()
        except Exception as e:
            err(str(e))

    fig = utility.CandleStick(df)
    fig["layout"]["uirevision"] = "some-constant"

    return fig


# Update the countdown value
@callback(
    dash.dependencies.Output("countdown", "children"),
    dash.dependencies.Input("interval", "n_intervals"),
)
def update_countdown(n):
    global time, target_time

    current_time = datetime.now()
    remaining_time = target_time - current_time

    remaining_seconds = remaining_time.total_seconds()

    return str(int(remaining_seconds))


# Update the profit value
@callback(
    dash.dependencies.Output("profit", "children"),
    dash.dependencies.Input("interval-component", "n_intervals"),
)
def update_profit(n):
    client = XTBClient()
    try:
        client.login(USER_NUM, PASSWORD)
        profit = client.get_profits()
        client.logout()
    except Exception as e:
        err("Update_profit: " + str(e))

    return str(profit)


# Update the logs
@callback(
    dash.dependencies.Output("logs-plot-page", "children"),
    dash.dependencies.Input("logs-plot-interval", "n_intervals"),
)
def update_logs(n):
    if not os.path.exists(".log"):
        return "Logs not found."
    with open(".log", "r") as file:
        data = file.read().rstrip()
    return data

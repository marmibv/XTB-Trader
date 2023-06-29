import dash
import logging
import os
from datetime import datetime, timedelta
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


def logger_init():
    logFormatter = logging.Formatter(
        "%(asctime)s  %(levelname)-5s  %(theme)-9s  "
        + "%(status)-8s  %(message)s"
    )
    logger = logging.getLogger(__name__)

    fileHandler = logging.FileHandler("./.log")
    fileHandler.setFormatter(logFormatter)
    logger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)

    logger.setLevel(logging.INFO)

    return logger


logger = utility.KLogger(__name__)

dash.register_page(__name__)


layout = html.Div(
    [
        dcc.Graph(
            id="candlestick-chart",
            style={"width": "100%", "height": "100vh"},
        ),
        dcc.Interval(
            id="plot-interval",
            interval=30000,
            n_intervals=0,
        ),
        html.Div(
            [html.Pre(id="logs-plot-page")],
        ),
        dcc.Interval(id="logs-plot-interval", interval=2000, n_intervals=0),
    ],
    className="container",
)


@callback(
    Output("candlestick-chart", "figure"),
    [Input("plot-interval", "n_intervals")],
)
def update_candlestick_chart(n):
    global target_time

    df = None
    try:
        df = utility.collect_yf(YF_SYMBOL, PERIOD, INTERVAL)
    except Exception as e:
        logger.err(str(e))
        return go.Figure()

    utility.analyze(df, means=[MEAN1, MEAN2])

    target_time = datetime.now() + timedelta(minutes=1)
    action_marker = df.iloc[-1].is_trade
    if action_marker != 0:
        logger.report("Trade found.")
        try:
            client = XTBClient()
            client.login(USER_NUM, PASSWORD)

            # CLOSE ALL
            profits = str(client.get_profits())
            status = client.close_all()
            status["message"] += " PROFIT: " + profits
            status["theme"] = "CLOSE ALL"
            logger.report(status)

            # OPEN NEW
            status = client.open_transaction(
                MODES.BUY if action_marker > 0 else MODES.SELL,
                SYMBOL,
                volume=VOLUME,
                # tp=10,
                # sl=20,
            )
            status["theme"] = "NEW BUY" if action_marker > 0 else "NEW SELL"

            logger.report(status)

            client.logout()
        except Exception as e:
            logger.err(str(e))

    fig = utility.CandleStick(df)
    fig["layout"]["uirevision"] = "some-constant"

    return fig


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

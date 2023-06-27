import dash
import os
from dash import dcc, html, callback
from utility import utility
from dotenv import load_dotenv

load_dotenv()

YF_SYMBOL = os.environ.get("yf_symbol")
PERIOD = os.environ.get("period")
INTERVAL = os.environ.get("interval")
MEAN1 = int(os.environ.get("mean1"))
MEAN2 = int(os.environ.get("mean2"))

dash.register_page(__name__)

layout = html.Div(
    [
        html.Div(
            [html.Pre(id="trades-page")],
        ),
        dcc.Interval(id="trades-interval", interval=2000, n_intervals=0),
    ],
    className="container",
)


# Update the trades
@callback(
    dash.dependencies.Output("trades-page", "children"),
    dash.dependencies.Input("trades-interval", "n_intervals"),
)
def update_trades(n):
    df = None
    df = utility.collect_yf(YF_SYMBOL, PERIOD, INTERVAL)

    utility.analyze(df, means=[MEAN1, MEAN2])
    df.set_index("datetime", inplace=True)

    return (
        df[df.is_trade != 0][["is_trade"]]
        .sort_index(ascending=False)
        .to_string()
    )

import dash
import logging
import os
from datetime import datetime, timedelta
from dash import dcc
from dash import html
from utility import utility
from dash.dependencies import Output, Input
from XTBClient.api import XTBClient, MODES

app = dash.Dash(__name__, url_base_pathname="/dash/")

logging.getLogger("XTBApi.api").setLevel(logging.WARNING)

target_time = datetime.now() + timedelta(minutes=1)
time = 60

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
                html.H2(id="countdown"),
                html.H2(id="profit"),
                dcc.Interval(id="interval", interval=1000, n_intervals=0),
            ],
            id="info",
        ),
    ],
    id="container",
)


def report(status):
    rep = "TRANSACTION\t{}\t{}".format(
        status["request_status"].name, status["message"]
    )
    print(rep)
    with open("report", "a+") as f:
        f.write(rep)


@app.callback(
    Output("candlestick-chart", "figure"),
    [Input("interval-component", "n_intervals")],
)
def update_candlestick_chart(n):
    global target_time

    df = utility.collect_yf("EURUSD", "2d", "5m")
    utility.analyze(df, means=[5, 10])
    # df = get_df("EURUSD")
    # df = df[-50:]

    target_time = datetime.now() + timedelta(minutes=1)
    action_marker = df.iloc[-1].is_trade
    if action_marker != 0:
        client = XTBClient()
        client.login(
            os.environ.get("XTB_user_num"), os.environ.get("XTB_pass")
        )

        status = client.close_all()
        report(status)

        status = client.open_transaction(
            MODES.BUY if action_marker > 0 else MODES.SELL,
            "EURUSD",
            volume=0.2,
            # tp=10,
            # sl=20,
        )
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
    client.login(os.environ.get("XTB_user_num"), os.environ.get("XTB_pass"))
    profit = client.get_profits()
    client.logout()
    return str(profit)


if __name__ == "__main__":
    app.run_server(port=8000, host="0.0.0.0", debug=True)

import dash
from dash import dcc
from dash import html
from utility import utility
from dash.dependencies import Output, Input
from XTBClient.api import MODES

app = dash.Dash(__name__)


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
    ],
    style={"width": "100%", "height": "100vh", "margin": "0"},
)


@app.callback(
    Output("candlestick-chart", "figure"),
    [Input("interval-component", "n_intervals")],
)
def update_candlestick_chart(n):
    df = utility.collect_yf("EURUSD", "1d", "1m")
    utility.analyze(df, [5, 6])
    print("Refreshing...")
    # df = get_df("EURUSD")
    # df = df[-10:]

    action_marker = df.iloc[-1].is_trade
    if action_marker != 0:
        utility.open_transaction(
            MODES.BUY if action_marker > 0 else MODES.SELL,
            "EURUSD",
            volume=0.2,
            tp=10,
            sl=20,
        )

    fig = utility.CandleStick(df)
    fig["layout"]["uirevision"] = "some-constant"

    return fig


if __name__ == "__main__":
    app.run_server(port=8000, host="0.0.0.0", debug=True)

import dash
import os
from dash import dcc, html, callback
from dotenv import load_dotenv

load_dotenv()

dash.register_page(__name__)


layout = html.Div(
    [
        html.Div(
            [html.Pre(id="logs-page")],
        ),
        dcc.Interval(id="logs-interval", interval=2000, n_intervals=0),
    ],
    className="container",
)


# Update the logs
@callback(
    dash.dependencies.Output("logs-page", "children"),
    dash.dependencies.Input("logs-interval", "n_intervals"),
)
def update_logs(n):
    if not os.path.exists(".log"):
        return "Logs not found."
    with open(".log", "r") as file:
        data = file.read().rstrip()
    return data

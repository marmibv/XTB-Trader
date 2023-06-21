from dash import Dash, html
import dash
import os

# # LAYOUT
external_scripts = [
    {"src": "https://code.jquery.com/jquery-3.5.1.min.js"},
]
app = Dash(
    __name__,
    use_pages=True,
    url_base_pathname="/{}/".format(os.environ.get("path_prefix")),
    external_scripts=external_scripts,
)

app.layout = html.Div(
    [
        dash.page_container,
    ]
)

if __name__ == "__main__":
    app.run_server(port=8000, host="0.0.0.0", debug=True)

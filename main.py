import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from analyst.analist import download_csv, top_20 , pie_chart, ratio, best_day_to_publish
import os

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server  

FILE_ID = '1K-dP_S7se5K6h7o6e6ocKdBtetCU2Fyc'

app.layout = html.Div([
    html.Div(id='graph-container'),
    html.Div(id='pie-container'),
    html.Div(id='ratio-container'),
    html.Div(id='best_day_to_publish-container'),
    dcc.Interval(
        id='interval-component',
        interval=60 * 1000,  
        n_intervals=0
    )
])

@app.callback(
    Output('graph-container', 'children'),
    Output('pie-container', 'children'),
    Output('ratio-container', 'children'),
    Output('best_day_to_publish-container', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_graph(n_intervals):
    df = download_csv(FILE_ID)
    figure = top_20(df)
    fig = pie_chart(df)
    figs = ratio(df)
    fig_days = best_day_to_publish(df)
    return dcc.Graph(figure=figure), dcc.Graph(figure=fig), dcc.Graph(figure=figs), dcc.Graph(figure=fig_days)

if __name__ == '__main__':
    app.run_server(debug=True)
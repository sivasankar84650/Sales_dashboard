
import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.express as px
import base64
import io

app = dash.Dash(__name__)
app.title = "Sales Dashboard"

app.layout = html.Div([
    html.H2("📊 Upload Your Sales CSV", style={'textAlign': 'center'}),

    dcc.Upload(
        id='upload-data',
        children=html.Div(['📁 Drag and Drop or ', html.A('Select File')]),
        style={
            'width': '98%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '2px',
            'borderStyle': 'dashed',
            'borderRadius': '10px',
            'textAlign': 'center',
            'margin': '10px'
        },
        multiple=False
    ),

    dcc.Store(id='stored-data'),

    html.Div(id='output-container'),

    html.Div(id='controls-container', children=[
        html.Div([
            html.Label("Select Category"),
            dcc.Dropdown(id='category-filter', clearable=False)
        ], style={'width': '30%', 'display': 'inline-block'}),

        html.Div([
            html.Label("Date Range"),
            dcc.DatePickerRange(id='date-range')
        ], style={'width': '40%', 'display': 'inline-block', 'paddingLeft': '20px'}),

        html.Div([
            html.Button("🔍 Search", id='search-button', n_clicks=0)
        ], style={'width': '20%', 'display': 'inline-block', 'paddingLeft': '20px', 'paddingTop': '22px'})
    ], style={'margin': '20px'}),

    dcc.Graph(id='sales-by-month'),
    dcc.Graph(id='top-products')
])


def parse_data(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    return pd.read_csv(io.StringIO(decoded.decode('utf-8')))


@app.callback(
    [Output('stored-data', 'data'),
     Output('category-filter', 'options'),
     Output('category-filter', 'value'),
     Output('date-range', 'min_date_allowed'),
     Output('date-range', 'max_date_allowed'),
     Output('date-range', 'start_date'),
     Output('date-range', 'end_date'),
     Output('output-container', 'children')],
    Input('upload-data', 'contents')
)
def update_filters(contents):
    if contents:
        df = parse_data(contents)
        df['Date'] = pd.to_datetime(df['Date'])

        options = [{'label': cat, 'value': cat} for cat in df['Category'].unique()]
        min_date = df['Date'].min().date()
        max_date = df['Date'].max().date()

        return (
            df.to_json(date_format='iso', orient='split'),
            options,
            options[0]['value'],
            min_date,
            max_date,
            min_date,
            max_date,
            html.Div("✅ File Uploaded Successfully")
        )

    return None, [], None, None, None, None, None, ""


@app.callback(
    [Output('sales-by-month', 'figure'),
     Output('top-products', 'figure')],
    Input('search-button', 'n_clicks'),
    [State('category-filter', 'value'),
     State('date-range', 'start_date'),
     State('date-range', 'end_date'),
     State('stored-data', 'data')],
    prevent_initial_call=True
)
def update_graphs(n_clicks, category, start_date, end_date, data):
    if data is None:
        return {}, {}

    df = pd.read_json(data, orient='split')
    df['Date'] = pd.to_datetime(df['Date'])

    mask = (
        (df['Category'] == category) &
        (df['Date'] >= pd.to_datetime(start_date)) &
        (df['Date'] <= pd.to_datetime(end_date))
    )
    filtered = df.loc[mask]

    monthly = filtered.groupby(filtered['Date'].dt.to_period('M'))['Revenue'].sum().reset_index()
    monthly['Date'] = monthly['Date'].dt.strftime('%Y-%m')
    fig1 = px.line(monthly, x='Date', y='Revenue', title='Monthly Revenue')

    top = filtered.groupby('Product')['Revenue'].sum().nlargest(5).reset_index()
    fig2 = px.bar(top, x='Product', y='Revenue', title='Top Products')

    return fig1, fig2


if __name__ == '__main__':
    app.run_server(debug=True)


import dash
from dash import dcc, html, Input, Output, State, callback_context
import pandas as pd
import plotly.express as px
import io
import base64
from datetime import datetime

app = dash.Dash(__name__)
app.title = "Sales Dashboard"
server = app.server

default_data = pd.DataFrame({
    "Date": pd.date_range(start="2024-01-01", periods=50, freq="D"),
    "Product": ["Product A", "Product B", "Product C", "Product D", "Product E"] * 10,
    "Category": ["Electronics", "Electronics", "Clothing", "Clothing", "Accessories"] * 10,
    "Revenue": [100, 150, 200, 130, 180] * 10
})

global_df = default_data.copy()

app.layout = html.Div([
    html.H2("📊 Sales Dashboard"),

    dcc.Upload(
        id='upload-data',
        children=html.Button('📤 Upload CSV'),
        multiple=False,
        accept=".csv"
    ),

    html.Div(id='file-info'),

    dcc.Dropdown(id='category-filter', multi=True, placeholder="Select Category"),
    dcc.DatePickerRange(id='date-filter'),

    dcc.Graph(id='revenue-chart'),
    dcc.Graph(id='top-products')
])

def parse_contents(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    return df

@app.callback(
    Output('file-info', 'children'),
    Output('category-filter', 'options'),
    Input('upload-data', 'contents'),
    prevent_initial_call=True
)
def handle_file(contents):
    global global_df
    try:
        df = parse_contents(contents)
        df['Date'] = pd.to_datetime(df['Date'])
        global_df = df
        return "✅ File uploaded successfully", [{'label': c, 'value': c} for c in df['Category'].unique()]
    except Exception as e:
        global_df = default_data.copy()
        return f"⚠️ Error loading file. Using sample data. ({e})", [{'label': c, 'value': c} for c in global_df['Category'].unique()]

@app.callback(
    Output('revenue-chart', 'figure'),
    Output('top-products', 'figure'),
    Input('category-filter', 'value'),
    Input('date-filter', 'start_date'),
    Input('date-filter', 'end_date')
)
def update_charts(categories, start_date, end_date):
    df = global_df.copy()
    if categories:
        df = df[df['Category'].isin(categories)]
    if start_date and end_date:
        df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

    fig1 = px.line(df, x='Date', y='Revenue', title='📈 Revenue Over Time')
    top_products = df.groupby('Product')['Revenue'].sum().nlargest(5).reset_index()
    fig2 = px.bar(top_products, x='Product', y='Revenue', title='🏆 Top 5 Products')

    return fig1, fig2

if __name__ == '__main__':
    app.run_server(debug=True)


import pandas as pd
import plotly.graph_objs as go
from my_modules.metrics import calculate_metrics

def generate_dashboard(trade_log, output_html="backtest_report.html"):
    df = pd.DataFrame(trade_log)
    if df.empty or 'return' not in df.columns:
        print("No trades found.")
        return

    df['cumulative_return'] = (1 + df['return']).cumprod()
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Equity curve
    equity_curve = go.Scatter(x=df['timestamp'], y=df['cumulative_return'], mode='lines', name='Equity Curve')

    # Trade scatter
    buy_signals = df[df['signal'] == 'Buy']
    sell_signals = df[df['signal'] == 'Sell']

    buy_points = go.Scatter(
        x=buy_signals['timestamp'], y=buy_signals['price'],
        mode='markers', name='Buy', marker=dict(color='green', symbol='triangle-up', size=8)
    )
    sell_points = go.Scatter(
        x=sell_signals['timestamp'], y=sell_signals['price'],
        mode='markers', name='Sell', marker=dict(color='red', symbol='triangle-down', size=8)
    )

    # Performance stats table
    stats = calculate_metrics(trade_log)
    stats_table = go.Table(
        header=dict(values=["Metric", "Value"], fill_color='paleturquoise', align='left'),
        cells=dict(values=[list(stats.keys()), list(stats.values())], fill_color='lavender', align='left')
    )

    # Combine plots
    fig = go.Figure(data=[equity_curve, buy_points, sell_points])
    fig.update_layout(title='Backtest Equity Curve', xaxis_title='Time', yaxis_title='Cumulative Return')

    # Save plots
    fig.write_html(output_html.replace(".html", "_equity.html"), auto_open=False)

    # Save stats
    stats_fig = go.Figure(data=[stats_table])
    stats_fig.update_layout(title='Performance Summary')
    stats_fig.write_html(output_html.replace(".html", "_stats.html"), auto_open=False)

    print(f"✅ Dashboard saved to: {output_html.replace('.html', '_equity.html')} and _stats.html")

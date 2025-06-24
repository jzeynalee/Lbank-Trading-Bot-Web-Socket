
import pandas as pd
import numpy as np

def calculate_metrics(trade_log, risk_free_rate=0.01):
    df = pd.DataFrame(trade_log)
    if df.empty or 'return' not in df.columns:
        return {}

    df['cumulative_return'] = (1 + df['return']).cumprod()
    df['drawdown'] = df['cumulative_return'] / df['cumulative_return'].cummax() - 1

    # Metrics
    total_trades = len(df)
    wins = df[df['return'] > 0]
    losses = df[df['return'] <= 0]
    win_rate = len(wins) / total_trades if total_trades > 0 else 0
    avg_gain = wins['return'].mean() if not wins.empty else 0
    avg_loss = losses['return'].mean() if not losses.empty else 0
    profit_factor = abs(avg_gain / avg_loss) if avg_loss != 0 else np.inf

    # Sharpe ratio
    excess_returns = df['return'] - (risk_free_rate / 252)
    sharpe_ratio = excess_returns.mean() / (excess_returns.std() + 1e-10) * np.sqrt(252)

    # Max drawdown
    max_drawdown = df['drawdown'].min()

    # Expectancy
    expectancy = (win_rate * avg_gain) + ((1 - win_rate) * avg_loss)

    # CAGR approximation (optional if data has full year)
    period_days = len(df)
    cagr = (df['cumulative_return'].iloc[-1])**(252/period_days) - 1 if period_days > 0 else 0

    return {
        "Total Trades": total_trades,
        "Win Rate": round(win_rate * 100, 2),
        "Average Gain": round(avg_gain, 4),
        "Average Loss": round(avg_loss, 4),
        "Profit Factor": round(profit_factor, 3),
        "Sharpe Ratio": round(sharpe_ratio, 3),
        "Expectancy": round(expectancy, 4),
        "Max Drawdown": round(max_drawdown * 100, 2),
        "CAGR": round(cagr * 100, 2)
    }

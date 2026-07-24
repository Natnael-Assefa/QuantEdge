import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def run_backtest(model_output_path):
    print("Loading model output and running backtester...")
    # Load our engineered features
    df = pd.read_csv(model_output_path, index_col='Date', parse_dates=True)
    
    # Calculate simple daily log-returns for both assets
    df['GLD_Return'] = np.log(df['GLD'] / df['GLD'].shift(1))
    df['GDX_Return'] = np.log(df['GDX'] / df['GDX'].shift(1))
    
    # Calculate the change in the spread return day-over-day
    # Spread return = GLD_Return - (Beta * GDX_Return)
    df['Spread_Return'] = df['GLD_Return'] - (df['Beta'].shift(1) * df['GDX_Return'])
    
    # Strategy Return is yesterday's position multiplied by today's spread return
    df['Strategy_Return'] = df['Position'].shift(1) * df['Spread_Return']
    
    # Fill any NaNs with 0 (especially the first 252 days and flat days)
    df['Strategy_Return'] = df['Strategy_Return'].fillna(0.0)
    
    # Calculate Cumulative Returns (Equity Curve)
    df['Cumulative_Strategy'] = np.exp(df['Strategy_Return'].cumsum()) - 1
    df['Cumulative_GLD'] = np.exp(df['GLD_Return'].fillna(0.0).cumsum()) - 1
    
    # --- PERFORMANCE METRICS ---
    # 1. Total Return
    final_return = df['Cumulative_Strategy'].iloc[-1]
    
    # 2. Sharpe Ratio (Annualized)
    # Assuming 252 trading days a year
    active_returns = df['Strategy_Return'][df['Position'].shift(1) != 0]
    if len(active_returns) > 0 and active_returns.std() != 0:
        daily_std = df['Strategy_Return'].std()
        daily_mean = df['Strategy_Return'].mean()
        sharpe_ratio = (daily_mean / daily_std) * np.sqrt(252)
    else:
        sharpe_ratio = 0.0
        
    # 3. Maximum Drawdown
    # Peak is the running maximum value of the equity curve
    cumulative_equity = np.exp(df['Strategy_Return'].cumsum())
    running_max = cumulative_equity.cummax()
    drawdown = (cumulative_equity - running_max) / running_max
    max_drawdown = drawdown.min()
    
    print("\n==============================================")
    print("           STRATEGY PERFORMANCE METRICS       ")
    print("==============================================")
    print(f"Total Cumulative Return:     {final_return * 100:.2f}%")
    print(f"Annualized Sharpe Ratio:     {sharpe_ratio:.4f}")
    print(f"Maximum Drawdown:            {max_drawdown * 100:.2f}%")
    print("==============================================")
    
    # --- PLOT THE EQUITY CURVE ---
    plt.figure(figsize=(12, 6))
    plt.plot(df['Cumulative_Strategy'] * 100, label='Pairs Trading Strategy (L/S Spread)', color='forestgreen', lw=2)
    plt.plot(df['Cumulative_GLD'] * 100, label='Buy & Hold GLD (Benchmark)', color='gold', linestyle='--', alpha=0.7)
    plt.title('Pairs Trading Strategy vs. Buy & Hold GLD', fontsize=14, fontweight='bold')
    plt.ylabel('Cumulative Return (%)', fontsize=12)
    plt.xlabel('Date', fontsize=12)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(fontsize=10)
    plt.tight_layout()
    
    # Save the plot
    plt.savefig('data/equity_curve.png')
    print("Equity Curve plot saved as 'data/equity_curve.png'")
    plt.show()

if __name__ == "__main__":
    run_backtest("data/pair_model_output.csv")
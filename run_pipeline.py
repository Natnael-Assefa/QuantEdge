import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# 1. Setup Parameters
TICKERS = ["GLD", "GDX"]
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Define a 5-year lookback window
END_DATE = datetime.today()
START_DATE = END_DATE - timedelta(days=5*365)

print(f"Starting data pipeline. Lookback window: {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}")

# 2. Download and Extract Adjusted Close Cleanly
processed_series = {}

for ticker in TICKERS:
    print(f"Downloading raw data for {ticker}...")
    raw_data = yf.download(ticker, start=START_DATE, end=END_DATE, auto_adjust=False, progress=False)
    
    if isinstance(raw_data.columns, pd.MultiIndex):
        raw_data.columns = raw_data.columns.get_level_values(0)
    
    if 'Adj Close' in raw_data.columns:
        series = raw_data['Adj Close'].copy()
        series.index = pd.to_datetime(series.index).tz_localize(None)
        processed_series[ticker] = series
        print(f"Successfully processed {len(series)} rows for {ticker}.")
    else:
        raise KeyError(f"Could not find 'Adj Close' column for {ticker}.")

# 3. The Inner-Join Alignment Engine
print("Aligning time series data via an inner join...")
master_df = pd.DataFrame(processed_series).dropna()
master_df.columns = ['GLD', 'GDX']

output_path = os.path.join(DATA_DIR, "aligned_pairs.csv")
master_df.to_csv(output_path)

print("\n### PIPELINE SUCCESS ###")
print(f"Clean matrix saved to: {output_path}")
print(f"Total matched trading days: {master_df.shape[0]}")
print("\nFirst 5 rows of your trading matrix:")
print(master_df.head())

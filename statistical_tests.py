import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller

def run_rolling_ols(input_path, output_path, window=252):
    print("Loading aligned pairs data...")
    df = pd.read_csv(input_path, index_col='Date', parse_dates=True)
    
    Y = np.log(df['GLD'])
    X = np.log(df['GDX'])
    
    betas = np.full(len(df), np.nan)
    alphas = np.full(len(df), np.nan)
    spreads = np.full(len(df), np.nan)
    
    print(f"Running Rolling OLS Engine (Window size: {window} days)...")
    
    for t in range(window, len(df)):
        Y_slice = Y.iloc[t - window : t]
        X_slice = X.iloc[t - window : t]
        
        X_slice_with_const = sm.add_constant(X_slice)
        model = sm.OLS(Y_slice, X_slice_with_const).fit()
        
        beta_t = model.params['GDX']
        alpha_t = model.params['const']
        
        current_gld = Y.iloc[t]
        current_gdx = X.iloc[t]
        
        spread_t = current_gld - (alpha_t + beta_t * current_gdx)
        
        betas[t] = beta_t
        alphas[t] = alpha_t
        spreads[t] = spread_t

    df['Beta'] = betas
    df['Alpha'] = alphas
    df['Spread'] = spreads
    
    df.to_csv(output_path)
    print(f"Step 2 Complete! Output saved to: {output_path}")
    return df

def run_cointegration_test(output_path):
    print("\n==============================================")
    print("      RUNNING ENGLE-GRANGER STEP TWO          ")
    print("==============================================")
    
    df = pd.read_csv(output_path, index_col='Date', parse_dates=True)
    clean_spread = df['Spread'].dropna()
    
    result = adfuller(clean_spread, autolag='AIC')
    
    print(f"ADF Test Statistic: {result[0]:.4f}")
    print(f"p-value:            {result[1]:.6f}")
    print("\nCritical Values:")
    for key, val in result[4].items():
        print(f"   {key}: {val:.4f}")
    print("==============================================")

def generate_signals(output_path, z_window=30, entry_thresh=2.0, exit_thresh=0.0):
    print("\nGenerating Trading Signals and Z-Scores...")
    df = pd.read_csv(output_path, index_col='Date', parse_dates=True)
    
    # Calculate Dynamic Rolling Mean and Std Dev of the Spread
    rolling_mean = df['Spread'].rolling(window=z_window).mean()
    rolling_std = df['Spread'].rolling(window=z_window).std()
    
    # Calculate Dynamic Z-Score
    df['Z_Score'] = (df['Spread'] - rolling_mean) / rolling_std
    
    # State-based Signal Logic (0 = Flat, 1 = Long Spread, -1 = Short Spread)
    positions = np.zeros(len(df))
    current_position = 0  # Start flat
    
    z_scores = df['Z_Score'].values
    
    for i in range(len(df)):
        z = z_scores[i]
        
        # Skip until we have valid Z-Scores
        if np.isnan(z):
            positions[i] = 0
            continue
            
        if current_position == 0:
            # Entry Conditions
            if z <= -entry_thresh:
                current_position = 1  # Long Spread
            elif z >= entry_thresh:
                current_position = -1 # Short Spread
        elif current_position == 1:
            # Exit Conditions for Long Position (Reverted to Mean)
            if z >= -exit_thresh:
                current_position = 0
        elif current_position == -1:
            # Exit Conditions for Short Position (Reverted to Mean)
            if z <= exit_thresh:
                current_position = 0
                
        positions[i] = current_position
        
    df['Position'] = positions
    
    # Calculate daily signal changes (Trades executed)
    # +1 means buy signal, -1 means sell signal, 0 means hold
    df['Signal_Change'] = df['Position'].diff().fillna(0)
    
    # Save the finalized trading model output
    df.to_csv(output_path)
    print("Step 4 Complete! Trading signals generated.")
    
    # Print out summary statistics
    total_trades = int(df['Signal_Change'].abs().sum() / 2) # Enter + Exit = 2 changes per trade
    print(f"Total Completed Trades: {total_trades}")
    print(f"Position breakdown: {df['Position'].value_counts().to_dict()}")

if __name__ == "__main__":
    out_file = "data/pair_model_output.csv"
    
    # 1. Run Regression
    run_rolling_ols(input_path="data/aligned_pairs.csv", output_path=out_file)
    
    # 2. Run Cointegration Test
    run_cointegration_test(output_path=out_file)
    
    # 3. Generate Trading Signals
    generate_signals(output_path=out_file, z_window=30)
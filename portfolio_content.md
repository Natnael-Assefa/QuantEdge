# QuantEdge — Portfolio Content

<img src="data/equity_curve.png" alt="Equity Curve — Strategy vs Buy & Hold GLD" style="width: 100%; height: auto; display: block;">

---

## Short Description (for beside the image)

QuantEdge is a statistical pairs trading pipeline for gold-related ETFs, built entirely in Python. It automates the full quantitative workflow — from downloading five years of historical market data via Yahoo Finance, through rolling OLS regression and Engle-Granger cointegration testing, to signal generation and backtested performance evaluation. The pipeline compares GLD (SPDR Gold Shares) against GDX (VanEck Gold Miners ETF), exploiting the statistical relationship between the spot price of gold and gold mining equities. A 252-day rolling Ordinary Least Squares regression dynamically estimates the hedge ratio (Beta) and intercept (Alpha) between the two log-priced series, while an Augmented Dickey-Fuller test validates cointegration — the prerequisite that the spread between the pair is stationary and mean-reverting. Trading signals are derived from a 30-day rolling Z-Score of the residual spread, entering long or short positions at ±2 standard deviations and exiting at mean reversion. The backtest engine computes daily log-returns, applies a one-day lag for realistic execution, and benchmarks the strategy against a buy-and-hold GLD position, reporting cumulative return, annualized Sharpe ratio, and maximum drawdown. The entire pipeline is a three-stage linear architecture with strict separation between data ingestion, statistical modeling, and backtesting — each stage reads from and writes to CSV, making every intermediate artifact inspectable and every stage independently runnable.

---

## Detailed Project Page

### Overview

**QuantEdge** is a quantitative research pipeline that implements a classic mean-reversion pairs trading strategy on two gold-correlated ETFs: GLD and GDX. The project demonstrates the complete lifecycle of a statistical arbitrage strategy — data acquisition, econometric modeling, signal generation, and backtested performance analysis — in a clean, modular Python codebase with no framework overhead.

The design philosophy is **"pipeline-first, inspectable at every stage"**: each of the three stages is a standalone script that reads input from a CSV file produced by the previous stage and writes its own output CSV. This makes the intermediate data fully transparent — you can open any CSV in Excel, a Jupyter notebook, or another tool to audit the intermediate results without modifying any code.

### What It Does

QuantEdge lets you:

- **Download and align market data** for GLD and GDX — five years of daily adjusted-close prices from Yahoo Finance, inner-joined so only dates with valid data for both tickers are retained.
- **Fit a rolling OLS regression** of log(GLD) on log(GDX) with a 252-day (one trading year) window, producing a dynamic hedge ratio (Beta), intercept (Alpha), and residual spread that evolves over time.
- **Test for cointegration** using the Augmented Dickey-Fuller (ADF) test on the spread series. A stationary spread is the statistical foundation of pairs trading — if the spread is mean-reverting, divergences are tradeable.
- **Generate trading signals** from a 30-day rolling Z-Score of the spread. Enter long or short when the Z-Score breaches ±2.0, exit when it reverts to zero.
- **Backtest the strategy** against a buy-and-hold GLD benchmark, computing cumulative equity curves, annualized Sharpe ratio, and maximum drawdown.

### Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3 |
| Market data | yfinance (Yahoo Finance API) |
| Data manipulation | pandas, NumPy |
| Statistical modeling | statsmodels (OLS, ADF test) |
| Visualization | matplotlib |

### Architecture

The codebase follows a three-stage linear pipeline with strict separation of concerns:

```
data_pipeline/
├── run_pipeline.py          # Stage 1: Data ingestion & alignment
├── statistical_tests.py     # Stage 2: Modeling, cointegration, signals
├── backtest_engine.py       # Stage 3: Backtesting & performance
├── data/
│   ├── aligned_pairs.csv    # Output of Stage 1 (1,254 rows)
│   ├── pair_model_output.csv# Output of Stage 2 (9 columns)
│   └── equity_curve.png     # Output of Stage 3 (equity chart)
```

Each stage is a self-contained script with an `if __name__ == "__main__"` block, meaning you can run any stage independently after its dependencies are in place. The pipeline parameters (ticker symbols, lookback window, rolling window sizes, Z-score thresholds) are defined as constants at the top of each script for easy tuning.

### Data Flow

```
Yahoo Finance API (GLD, GDX)
        │
        ▼
  ┌─────────────────────┐
  │  run_pipeline.py     │
  │  - Download 5yr of   │
  │    Adj Close prices  │
  │  - Inner-join align  │
  │  - Drop NaN rows     │
  └─────────┬───────────┘
            │
            ▼
   data/aligned_pairs.csv
   [Date, GLD, GDX]  (1,254 rows)
            │
            ▼
  ┌──────────────────────┐
  │  statistical_tests.py │
  │  - Rolling OLS (252d) │
  │  - ADF cointegration   │
  │  - Z-Score signals     │
  └─────────┬────────────┘
            │
            ▼
  data/pair_model_output.csv
  [Date, GLD, GDX, Beta, Alpha,
   Spread, Z_Score, Position,
   Signal_Change]  (1,254 rows)
            │
            ▼
  ┌──────────────────────┐
  │  backtest_engine.py   │
  │  - Log returns        │
  │  - Spread returns     │
  │  - Equity curve       │
  │  - Sharpe, Max DD     │
  └─────────┬────────────┘
            │
            ▼
   data/equity_curve.png
   (Strategy vs. Buy & Hold GLD)
```

### Key Technical Highlights

**Rolling OLS Regression with Dynamic Hedge Ratio:** Rather than fitting a single static regression over the full period, the pipeline uses a 252-day rolling window. This captures the evolving relationship between GLD and GDX — the hedge ratio (Beta) drifts significantly over time (e.g., ~0.28 in late 2022 to ~0.63 in mid-2026), reflecting changes in gold mining equity leverage and market conditions.

**Engle-Granger Cointegration Testing:** The ADF test on the spread series validates the core assumption of pairs trading: that the spread between GLD and GDX is stationary. The test reports the ADF statistic, p-value, and critical values at 1%, 5%, and 10% significance levels. A low p-value (< 0.05) confirms the pair is cointegrated and the strategy premise is statistically sound.

**State-Based Signal Generation:** The trading logic implements a finite state machine with three states — flat, long, and short. Entry signals fire at ±2.0 standard deviations from the mean spread, and exits occur at mean reversion (Z-Score = 0). The `Signal_Change` column flags exact trade execution dates, making the signal history fully auditable.

**One-Day Lag Execution:** Strategy returns are computed using lagged position values, ensuring trades are executed on the next day's open rather than the same day's close. This avoids look-ahead bias and produces realistic backtest results.

**Benchmark Comparison:** The strategy is benchmarked against a buy-and-hold GLD position, with both equity curves plotted on the same chart. The backtest reports three key metrics: total cumulative return, annualized Sharpe ratio (assuming 252 trading days), and maximum drawdown.

### Key Parameters

| Parameter | Value | Description |
|---|---|---|
| Tickers | GLD, GDX | Gold spot ETF vs. gold miners ETF |
| Lookback | 5 years | Historical data window |
| Rolling OLS window | 252 days | One trading year for regression |
| Z-Score lookback | 30 days | Rolling window for spread normalization |
| Entry threshold | ±2.0 σ | Z-Score level to enter a position |
| Exit threshold | 0.0 σ | Z-Score level to exit (mean reversion) |

### Getting Started

#### Prerequisites

- Python 3.10 or higher
- pip

#### Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/bini-ye-maryam/data_pipeline.git
cd data_pipeline
pip install pandas numpy yfinance statsmodels matplotlib
```

#### Run the Full Pipeline

```bash
python run_pipeline.py
python statistical_tests.py
python backtest_engine.py
```

Or run each stage individually — each script prints its results and saves output to the `data/` directory.

#### Inspect Results

Open `data/equity_curve.png` to see the strategy's equity curve versus buy-and-hold GLD. Open `data/pair_model_output.csv` to inspect the full model output — Beta, Alpha, Spread, Z-Score, Position, and Signal_Change for every trading day.

### Source Code

QuantEdge is fully open-source under the MIT license. Contributions, issues, and pull requests are welcome.

**[View on GitHub →](https://github.com/bini-ye-maryam/data_pipeline)**

### License

This project is open-source and available under the MIT License. Feel free to use, modify, and distribute it.

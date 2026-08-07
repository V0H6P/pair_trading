# Ornstein-Uhlenbeck Pairs Trading

A statistical arbitrage framework that identifies cointegrated equity pairs, models their spread as an Ornstein-Uhlenbeck process, and generates mean-reversion trading signals with full backtesting capabilities.

---

## Overview

**Problem.** Cointegrated asset pairs exhibit a long-run equilibrium relationship: their spread is mean-reverting. This property can be exploited through pairs trading — going long (short) the spread when it deviates below (above) its equilibrium, and closing when it reverts.

**Approach.** The spread between two cointegrated assets is modeled as a continuous-time Ornstein-Uhlenbeck (OU) process:


$$
dS_t = \theta(\mu − S_t) dt + \sigma dW_t
$$


where:
- `θ` — speed of mean reversion
- `μ` — long-term mean of the spread
- `σ` — volatility of the process
- `W_t` — standard Brownian motion

The calibrated OU parameters define the stationary distribution of the spread, from which z-score-based entry/exit thresholds are derived. A state-machine signal generator then produces trading decisions (long spread, short spread, or flat).

---

## Features

- **Pair universe screening** — Pre-filtered universe of 100+ economically justified pairs across sectors (healthcare, semis, energy, financials, etc.)
- **Rigorous cointegration testing** — Battery of 6 statistical tests: ADF, KPSS, Phillips-Perron, Engle-Granger, Johansen trace test, and Hurst exponent
- **Spread construction** — Hedge ratio computed via Johansen eigenvector normalization
- **OU calibration** — OLS-based maximum likelihood estimation of `(θ, μ, σ)` from the discretized AR(1) representation
- **Model diagnostics** — Jarque-Bera, Ljung-Box, and ARCH-LM tests on residuals; asymptotic confidence intervals via delta method
- **Signal generation** — State-machine logic with configurable entry/exit z-score thresholds, stop-loss, and max holding period
- **Backtesting engine** — PnL computation with transaction costs, Sharpe ratio, max drawdown, win rate, and trade count
- **Capital simulation** — Position sizing with fractional risk per trade and full mark-to-market accounting

---

## Methodology

### 1. Data Acquisition

Historical daily close prices are fetched via `yfinance` for all tickers in the candidate universe (2010-01-01 to 2024-01-01 for calibration; 2024-01-02 to 2026-07-01 for out-of-sample backtesting).

### 2. Cointegration Verification

For each candidate pair `(A, B)`, the following tests are run sequentially:

| Step | Test | Purpose |
|------|------|---------|
| 1 | ADF on levels | Confirm both series are non-stationary ($I(1)$) |
| 2 | ADF on first differences | Confirm both series are stationary after differencing |
| 3 | Johansen eigenvector | Compute hedge ratio `β` and spread `S = A − βB` |
| 4 | ADF + KPSS + Phillips-Perron on spread | Confirm spread stationarity |
| 5 | Engle-Granger + Johansen trace | Formal cointegration tests |
| 6 | Hurst exponent | Confirm mean-reverting behavior (`H < 0.5`) |

A pair must pass **all** tests to be retained.

### 3. OU Model Calibration

The spread is discretized as an AR(1) process:

```
S_{t+1} = b + a · S_t + ε_t
```

OLS yields `(â, b̂, σ̂_ε)`, which map to OU parameters:

```
θ = −ln(â) / Δt
μ = b̂ / (1 − â)
σ = σ̂_ε · √(−2 ln(â) / (Δt · (1 − â²)))
```

Half-life of mean reversion: `t_{1/2} = ln(2) / θ`

### 4. Signal Generation

The signal generator operates as a finite state machine with three states: `{−1, 0, +1}` (short spread, flat, long spread).

```
z = (S_t − μ) / σ_∞       where σ_∞ = σ / √(2θ)
```

**Entry rules:**
- `z > k_entry` → short the spread (state = −1)
- `z < −k_entry` → long the spread (state = +1)

**Exit rules (from long):**
- `z > −k_exit` → take profit
- `z < −stop_loss` → stop loss
- `t − t_entry > max_holding` → time stop

Symmetric rules apply for short positions.

### 5. Backtesting

Two backtesting modes are implemented:

- **Spread-level PnL** — Computes cumulative P&L from spread movements, with proportional transaction costs at position changes.
- **Capital simulation** — Allocates a fixed fraction `f` of available capital per trade, tracks share quantities for both legs, and computes mark-to-market equity at each timestep.

### 6. Performance Metrics

| Metric | Formula |
|--------|---------|
| Sharpe Ratio | `mean(PnL_active) / std(PnL_active) × √252` |
| Max Drawdown | `min(cumPnL − running_max(cumPnL))` |
| Win Rate | `count(PnL > 0) / count(active days)` |
| Trade Count | `sum(|ΔPosition| > 0) / 2` |

---

## Repository Structure

```
.
├── Pair_trading_strat.py       # Strategy class: signal generation, backtesting, capital simulation
├── fit_ou_model.py             # OUEstimator class: OLS calibration, diagnostics, confidence intervals
├── test_coint.py               # Coint_verif class: full cointegration test battery
├── test_pair.ipynb             # Main notebook: pair screening, OU fitting, backtesting workflow
├── pairs_universe.csv          # Candidate pairs with economic justification (100+ pairs)
├── financial_datas.csv         # Historical prices 2010–2024 (calibration window)
├── backtest_datas.csv          # Out-of-sample prices 2024–2026 (backtesting window)
├── image_rapport/              # Backtest PnL charts
│   ├── PnL_UNH-ELV.png
│   ├── PnL_UNH-ELV_10000_init.png
│   └── PnL_PNO-DHR.png
├── docs/                       # Theoretical documentation
│   ├── 01_Fondements.md
│   ├── 02_Processus_Ornstein_Uhlenbeck.md
│   ├── 03_Construction_du_spread.md
│   ├── 04_Validation_statistique.md
│   ├── 05_Calibration.md
│   ├── 06_Pairs_Trading.md
│   ├── 07_Limites_du_modele.md
│   ├── 08_Roadmap_implementation.md
│   └── Bibliographie.md
└── images/                     # Diagrams for documentation
```

---

## Installation

```bash
git clone https://github.com/<your-username>/ou-pairs-trading.git
cd ou-pairs-trading
pip install -r requirements.txt
```

### Dependencies

| Package | Purpose |
|---------|---------|
| `numpy` | Numerical computations |
| `pandas` | Data manipulation |
| `scipy` | OLS regression, statistical tests |
| `statsmodels` | ADF, KPSS, Engle-Granger, Johansen, Ljung-Box, ARCH-LM |
| `arch` | Phillips-Perron unit root test |
| `hurst` | Hurst exponent estimation |
| `yfinance` | Market data retrieval |
| `matplotlib` | Visualization |

> **Note:** No `requirements.txt` is currently present in the repository. Install dependencies manually with:
> ```bash
> pip install numpy pandas scipy statsmodels arch hurst yfinance matplotlib
> ```

---

## Usage

### Quick Start

```python
from test_coint import Coint_verif
from fit_ou_model import OUEstimator
from Pair_trading_strat import Strategie

# 1. Verify cointegration
verifier = Coint_verif(prices_A, prices_B)
verifier.test_batterie()  # raises CointError if tests fail
spread, hedge_ratio = verifier.spread_n_hedge_ratio

# 2. Calibrate OU model
ou = OUEstimator(dt=1.0)
ou.fit_ols(spread)
print(f"θ={ou.theta:.4f}, μ={ou.mu:.4f}, σ={ou.sigma:.4f}, t½={ou.half_life:.1f}d")

# 3. Backtest strategy
strategy = Strategie(ou_estimator=ou, k_entry=2, k_exit=0.2, stop_loss=3)
spread_oos = prices_A_oos - hedge_ratio * prices_B_oos
cumulative_pnl, stats = strategy.backtest(spread_oos)

# 4. Capital simulation
equity_curve = strategy.simulate_capital(
    prixA=prices_A_oos, prixB=prices_B_oos,
    hedge=hedge_ratio, capital=10000, f=0.05
)
```

### Default Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `k_entry` | 2.0 | Entry threshold in z-score units |
| `k_exit` | 0.2 | Exit (take-profit) threshold |
| `stop_loss` | 3.0 | Stop-loss threshold |
| `max_holding_days` | None | Maximum holding period (disabled) |
| `transaction_cost_bps` | 30 | Transaction costs in basis points |

---

## Results

Cointegrated pairs retained after full test battery (2010–2024 calibration):

| Pair | Half-Life (days) | σ (OU) | Sector |
|------|-----------------|--------|--------|
| UNH – ELV | 55 | 2.70 | Health Insurance |
| TMO – DHR | 69 | 3.11 | Life Sciences |
| DE – AGCO | 49 | 3.61 | Agricultural Equipment |
| SNPS – CDNS | 25 | 1.72 | EDA Software |

Out-of-sample backtest (2024–2026) with default parameters shows positive PnL for the UNH–ELV pair. Other pairs exhibit losses under the default parameterization, suggesting the need for pair-specific parameter optimization.

---

## Limitations

- Cointegration is estimated over a fixed window and may break down (regime changes, structural breaks).
- The OU model assumes constant `(θ, μ, σ)` — real spreads exhibit time-varying dynamics.
- No parameter optimization has been performed yet (grid search, walk-forward, etc.).
- The capital simulation contains a known variable scoping issue in the first-step initialization (variable `t` referenced before assignment).
- Transaction costs are simplified (proportional to spread value, no slippage or market impact model).

---

## Roadmap

- [ ] Walk-forward parameter optimization (rolling window recalibration)
- [ ] Grid search over `(k_entry, k_exit, stop_loss)` per pair
- [ ] Regime detection for dynamic pair selection
- [ ] Intraday data support for faster OU convergence
- [ ] Multi-pair portfolio construction with correlation constraints

---

## License

This project is for educational and research purposes.

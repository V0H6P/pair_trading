# Quantitative Finance Technical Interview Preparation

## Project Overview

This project implements a complete statistical arbitrage pipeline based on pair trading. It covers: (1) economic pre-filtering of candidate equity pairs, (2) a battery of cointegration tests, (3) spread construction via Johansen eigenvector normalization, (4) Ornstein-Uhlenbeck model calibration via OLS on the discretized AR(1) form, (5) z-score-based signal generation through a finite state machine, and (6) out-of-sample backtesting with both spread-level PnL and capital simulation.

The codebase consists of three Python modules (`test_coint.py`, `fit_ou_model.py`, `Pair_trading_strat.py`), an orchestration notebook (`test_pair.ipynb`), and supporting data files. The project identifies 8 cointegrated pairs from 40+ candidates, retains 4 based on half-life/volatility criteria, and backtests on Jan 2024–Jul 2026 out-of-sample data.

---

## Interview Questions

### 1. Project Understanding and Architecture

**Q001 — Fundamental — Pipeline Overview**
Walk me through the complete pipeline of this project from raw market data to a backtest result. What are the key stages and how do they connect?

**Q002 — Fundamental — Module Responsibilities**
Explain the role of each of the three Python modules (`test_coint.py`, `fit_ou_model.py`, `Pair_trading_strat.py`). Why is this separation useful?

**Q003 — Intermediate — In-sample vs Out-of-sample**
How does the project separate in-sample and out-of-sample data? What parameters are estimated in-sample and which are held fixed during the backtest? What risks arise from this design?

**Q004 — Intermediate — Economic Pre-filtering**
Why does the pipeline begin with an economic pre-filter before running statistical tests? What problem does this solve, and what would happen if you skipped it?

**Q005 — Advanced — Static Parameters**
The hedge ratio, mu, and sigma are estimated once on the training set and never updated. What are the consequences of this choice for a strategy running over 2.5 years of out-of-sample data? How would you modify the architecture to address this?

---

### 2. Mathematical and Statistical Foundations

**Q006 — Fundamental — Cointegration vs Correlation**
What is the difference between correlation and cointegration? Why is cointegration the correct concept for pair trading?

**Q007 — Fundamental — Integration Order**
What does it mean for a time series to be I(1)? Why is verifying the integration order of both price series a necessary precondition for cointegration testing?

**Q008 — Intermediate — Ornstein-Uhlenbeck SDE**
Write the Ornstein-Uhlenbeck stochastic differential equation and explain each term. Under what conditions does the process have a stationary distribution, and what is that distribution?

**Q009 — Intermediate — OU Discretization**
Derive the exact discretization of the continuous-time OU process at uniform time intervals Δt. Show how the discrete parameters (a, b, σ_ε) map to the continuous-time parameters (θ, μ, σ).

**Q010 — Advanced — Half-life Derivation**
Derive the half-life formula t½ = ln(2)/θ from the OU SDE. What exactly does the half-life measure in the context of this strategy?

**Q011 — Advanced — Stationary Variance Derivation**
Derive the stationary variance σ²/(2θ) of the OU process. Start from the SDE and compute E[X(t)²] as t → ∞.

**Q012 — Expert — OLS vs MLE Equivalence**
The report claims that OLS estimation on the discretized AR(1) form is "equivalent to MLE for the Gaussian case." Under what precise conditions is this true? When does the equivalence break down?

**Q013 — Expert — Johansen vs Engle-Granger**
Compare the Johansen procedure and the Engle-Granger two-step method for testing cointegration. In what sense is Johansen "symmetric"? When would you prefer one over the other?

---

### 3. Statistical Testing Pipeline

**Q014 — Fundamental — Test Battery Logic**
The class `Coint_verif` in `test_coint.py` runs five sequential tests via `test_batterie()`. List them in order and explain the purpose of each test in the screening process.

**Q015 — Intermediate — ADF Test Mechanics**
Explain how the Augmented Dickey-Fuller test works. What is its null hypothesis? In `test_coint.py:auto_integration()`, why is the test applied twice — once expecting to fail to reject H₀, and once expecting to reject it?

**Q016 — Intermediate — KPSS Complementarity**
In `test_coint.py:spread_stationnarity()`, both ADF and KPSS tests are used on the spread. Why use both when they appear to test the same thing? What are the four possible combined outcomes and how should each be interpreted?

**Q017 — Advanced — Phillips-Perron Bug**
In `test_coint.py`, line 91–92, the Phillips-Perron test statistic is compared against the ADF critical values (`adf[4][crit_level]`). Is this correct? What are the consequences of this implementation choice?

**Q018 — Advanced — Hurst Exponent**
Explain what the Hurst exponent measures. Why is H < 0.5 required for a mean-reverting process? What are the limitations of the R/S method used in the implementation?

**Q019 — Expert — Multiple Testing Problem**
Running five sequential tests on each pair creates a multiple-testing issue. If each test has a 5% significance level, what is the approximate probability of incorrectly passing or failing a pair? How would you adjust for this?

**Q020 — Expert — Johansen det_order and k_ar_diff**
In `test_coint.py:spread_n_hedge_ratio`, `coint_johansen` is called with `det_order=0` and `k_ar_diff=1`. What do these parameters mean? What happens if you choose `det_order=1` instead? When would a different `k_ar_diff` be appropriate?

---

### 4. Ornstein-Uhlenbeck Estimation

**Q021 — Fundamental — OLS Fit Procedure**
Walk me through the `fit_ols()` method in `fit_ou_model.py` step by step. What is being regressed on what, and how are the OU parameters recovered?

**Q022 — Intermediate — Validity Check**
The `fit_ols()` method checks that `0 < a_hat < 1` and raises a `ValueError` if not. Why is this condition necessary? What would `a_hat >= 1` or `a_hat <= 0` imply about the underlying process?

**Q023 — Intermediate — Residual Variance Denominator**
In `fit_ou_model.py` line 57, the residual variance is computed with denominator `(n - 2)`. Why `n - 2` and not `n` or `n - 1`?

**Q024 — Advanced — Sigma Recovery Formula**
The formula for recovering σ from the discrete residual variance is: `σ² = σ²_ε · (−2 ln(â)) / (Δt · (1 − â²))`. Derive this formula from the exact discrete-time variance of the OU transition density.

**Q025 — Advanced — Confidence Intervals and Delta Method**
The `confidence_intervals()` method in `fit_ou_model.py` uses the delta method to propagate uncertainty from â to θ. Explain the delta method and assess whether the implementation is correct. What is the standard error formula used for â?

**Q026 — Expert — Diagnostic Tests Interpretation**
The `diagnostic_tests()` method runs Jarque-Bera, Ljung-Box, and ARCH-LM tests. For each test, explain what assumption of the OU model it validates. If the ARCH-LM test rejects, what does this imply about the OU model, and what alternative model would you consider?

**Q027 — Expert — Small-Sample Bias**
OLS estimation of AR(1) parameters is known to be biased in small samples. In which direction is the bias for â? How does this bias affect the estimated θ and half-life? Is this a concern for this project given the sample sizes involved?

---

### 5. Signal Generation and Strategy Logic

**Q028 — Fundamental — Z-Score and State Machine**
Explain how the z-score is computed in the `signal()` method of `Pair_trading_strat.py` and describe the state machine transitions. What do the states {-1, 0, 1} represent?

**Q029 — Intermediate — Entry and Exit Asymmetry**
The default parameters are k_entry=2 and k_exit=0.2. Why is the exit threshold so much smaller than the entry threshold? What is the financial intuition behind this asymmetry?

**Q030 — Intermediate — Stop-Loss Role**
Why is a stop-loss mechanism included in a mean-reversion strategy? Under what scenario would the stop-loss trigger, and what does it imply about the underlying cointegration relationship?

**Q031 — Advanced — Exit Condition Sign Convention**
In `Pair_trading_strat.py`, lines 43–44, the exit condition for a long spread position is `z_score > -self.k_exit`. Explain why the negative sign is present. What would happen if the condition were `z_score > self.k_exit` instead?

**Q032 — Advanced — Transaction Cost Bug**
In `Pair_trading_strat.py`, line 86, the transaction costs are computed as:
`costs = np.abs(trades[:1]) * self.tc * np.abs(spread[1:-1])`
Identify the bug in this line. What is the actual effect on the backtest results?

**Q033 — Expert — Spread-Level PnL Interpretation**
The `backtest()` method computes PnL as `positions[:-1] * np.diff(spread)`. What are the units of this PnL? How does it relate to actual dollar profit? Is this a realistic measure of strategy performance?

---

### 6. Capital Simulation

**Q034 — Intermediate — Variable Scoping Bug**
In `Pair_trading_strat.py`, the `simulate_capital()` method references variable `t` in lines 153–154 (inside the `if op == 1` block at the first time step), but `t` is only defined as the loop variable starting at line 168. What happens when this code executes? Under what conditions would this bug trigger?

**Q035 — Intermediate — Long Spread Mechanics**
When the strategy goes long the spread (buy A, short B), explain line by line how the capital allocation works in `simulate_capital()`. Specifically, explain what `n_A`, `n_B`, and the liquidity update represent.

**Q036 — Advanced — Risk Fraction f=0.5**
The notebook backtests with `f=0.5` (50% risk per trade). Is this a reasonable risk fraction for a pair trading strategy? What does a Kelly criterion analysis suggest about optimal sizing for an OU-based strategy?

**Q037 — Advanced — Mark-to-Market Accounting**
In the `simulate_capital()` method, when a long spread position is held (lines 181–183), the patrimoine is updated as `liquidité + n_A*prixA[t] - n_B*prixB[t]`. Explain why the short position in B appears as a subtraction. What implicit assumptions are made about short selling?

**Q038 — Expert — Missing Transaction Costs**
The `simulate_capital()` method does not apply the `self.tc` transaction costs. Why is this a problem for comparing results between the two backtest modes? How would you add transaction costs to this method?

---

### 7. Backtest Methodology and Results

**Q039 — Intermediate — Sharpe Ratio Computation**
The Sharpe ratio in `Pair_trading_strat.py` line 98–99 is computed only on active days. Is this the correct approach? What bias does this introduce compared to computing it on all calendar days?

**Q040 — Intermediate — Backtest Loop Bug**
In the orchestration notebook `test_pair.ipynb`, the loop that backtests all four pairs contains:
```python
df_bt = pd.concat([data_bt["UNH"], data_bt["ELV"]], axis=1).dropna()
```
inside the loop body. What is the bug? What are its consequences for the reported results?

**Q041 — Advanced — Look-Ahead Bias**
Does this backtest suffer from look-ahead bias? Analyze each step of the pipeline (pair selection, hedge ratio, OU estimation, signal parameters) for potential information leakage.

**Q042 — Advanced — Win Rate as a Metric**
The win rate is computed as the proportion of positive daily PnL on active days. Why is this a poor standalone metric for evaluating a pair trading strategy? What metric would be more informative?

**Q043 — Expert — Regime Change Detection**
Only UNH–ELV shows positive out-of-sample PnL. The other pairs lose money. How could you distinguish before entering a trade whether the cointegration relationship is still intact? Propose a concrete statistical test or monitoring approach.

---

### 8. Performance and Optimization

**Q044 — Intermediate — Computational Bottleneck**
Which part of the pipeline is the most computationally expensive? How does it scale with the number of candidate pairs and the length of the time series?

**Q045 — Advanced — Vectorization Opportunities**
The `backtest()` method uses a Python for-loop to generate signals. Could the signal generation be vectorized? What makes this non-trivial?

**Q046 — Advanced — Parameter Optimization**
How would you optimize the strategy parameters (k_entry, k_exit, stop_loss) per pair? Describe a walk-forward optimization approach and explain how to avoid overfitting.

---

### 9. Limitations, Robustness, and Alternative Approaches

**Q047 — Intermediate — Constant Volatility Assumption**
The OU model assumes constant σ. What evidence from the diagnostic tests would indicate this assumption is violated? What alternative model would accommodate time-varying volatility?

**Q048 — Advanced — Kalman Filter Alternative**
The report mentions using a Kalman filter for a dynamic hedge ratio as a potential improvement. Explain how a Kalman filter could be applied here. What is the state-space model, and what are the advantages over a static Johansen estimate?

**Q049 — Advanced — Spread Construction Choice**
The project constructs the spread using price levels: `spread = A - β·B`. An alternative is to use log prices. What are the advantages and disadvantages of each approach? When would the choice matter?

**Q050 — Expert — Structural Break Impact**
Suppose a major merger announcement occurs between the two companies in a pair. How would this event propagate through each stage of the pipeline? What would happen to the OU parameters, the z-score, and the trading signal?

**Q051 — Expert — Heavy Tails**
If the spread exhibits heavy tails (excess kurtosis), which components of the pipeline would be most affected? How would you modify the z-score signal generation to be robust to heavy tails?

**Q052 — Expert — Multi-Pair Portfolio**
If you were to trade all four pairs simultaneously, how would you allocate capital across them? What correlation structure between pairs would you need to account for, and how does this relate to the diversification benefit?

---

### 10. Challenging Follow-Up Questions

**Q053 — Expert — Derive the OU Transition Density**
Starting from the OU SDE dX = θ(μ − X)dt + σ dW, derive the conditional distribution X(t+Δt) | X(t). Show that it is Gaussian and compute its mean and variance.

**Q054 — Expert — Why Not Log-Likelihood Directly?**
Write the exact log-likelihood function for the discretized OU model. Show that maximizing it is equivalent to the OLS procedure implemented in `fit_ols()`. Under what conditions does this equivalence hold?

**Q055 — Expert — Cointegration Rank**
The Johansen procedure can detect multiple cointegration relationships in a system with more than two variables. In the bivariate case used here, what are the possible cointegration ranks and what does each imply? How does the implementation extract the hedge ratio when rank = 1?

**Q056 — Expert — Asymptotic vs Finite-Sample Critical Values**
The ADF, KPSS, and Engle-Granger tests all use tabulated critical values. Are these exact or asymptotic? How reliable are they for the sample sizes in this project (~3500 daily observations)?

---

## Key Areas to Master

1. **Ornstein-Uhlenbeck process**: SDE, exact discretization, stationary distribution, half-life derivation, transition density.
2. **Cointegration theory**: I(1) processes, Engle-Granger theorem, Johansen procedure (eigenvector problem, trace statistic), relationship between cointegration and error correction models.
3. **Statistical testing**: ADF, KPSS, Phillips-Perron (null hypotheses, power, complementarity), Hurst exponent, multiple testing issues.
4. **OLS/MLE estimation**: AR(1) regression, parameter recovery formulas, residual diagnostics, small-sample bias, delta method for confidence intervals.
5. **Strategy mechanics**: z-score normalization, state machine logic, entry/exit asymmetry, stop-loss rationale, transaction cost modeling.
6. **Backtesting methodology**: in-sample/out-of-sample split, look-ahead bias, Sharpe ratio computation, win rate limitations, regime change risk.
7. **Capital simulation**: position sizing, fractional risk, mark-to-market accounting, Kelly criterion for mean-reversion strategies.
8. **Known bugs**: transaction cost computation (`trades[:1]`), backtest loop hardcoding UNH/ELV, `simulate_capital` variable `t` scoping, Phillips-Perron using ADF critical values.

## Potential Weaknesses

### Verified Issues
- **Transaction cost bug** (`Pair_trading_strat.py:86`): `trades[:1]` only computes costs for the first trade instead of all trades. This makes the backtest unrealistically optimistic.
- **Backtest loop bug** (`test_pair.ipynb`): All pairs are backtested using UNH/ELV out-of-sample prices, making comparative results meaningless.
- **Variable scoping bug** (`Pair_trading_strat.py:153–154`): `t` is referenced before definition in `simulate_capital()` for the first time step.
- **Phillips-Perron critical values** (`test_coint.py:91–92`): PP test statistic is compared against ADF critical values instead of PP-specific critical values.
- **No transaction costs in capital simulation**: `simulate_capital()` ignores `self.tc` entirely.

### Potential Concerns
- Static parameters over a 2.5-year backtest period may lead to parameter drift.
- The Sharpe ratio is computed on active days only, which inflates it relative to a full-capital allocation basis.
- No parameter optimization is performed — results depend entirely on default values.
- Only one pair (UNH–ELV) shows positive performance, limiting conclusions about the strategy's viability.
- The OU model's constant volatility assumption is likely violated in practice (ARCH effects).

## Coverage Summary

**Covered areas**: Cointegration theory, Ornstein-Uhlenbeck modeling, statistical testing (ADF, KPSS, PP, Engle-Granger, Johansen, Hurst), OLS/MLE estimation, AR(1) discretization, z-score signal generation, state machine architecture, backtest methodology, capital simulation, transaction costs, performance metrics, regime change risk, parameter optimization, Kalman filter alternatives, code-level bugs and implementation analysis.

**Areas not deeply assessable**: Actual numerical results of the backtest (outputs not fully visible), behavior of the strategy on intraday data, specific performance of walk-forward optimization, real-world execution considerations (slippage, market impact, borrowing costs).

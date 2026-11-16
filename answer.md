# Quantitative Finance Technical Interview — Detailed Answers

## 1. Project Understanding and Architecture

---

### Q001 — Pipeline Overview

**Question:** Walk me through the complete pipeline of this project from raw market data to a backtest result. What are the key stages and how do they connect?

**Answer:**

The pipeline has six sequential stages:

**Stage 1 — Universe definition and data acquisition.** A manually curated CSV (`pairs_universe.csv`) lists ~40 candidate equity pairs, each justified by a fundamental economic relationship (direct competitors, same macro driver, same commodity exposure, etc.). Historical daily close prices are downloaded via `yfinance` for the period Jan 2010–Jan 2024 and cached in `financial_datas.csv`. A separate out-of-sample dataset (Jan 2024–Jul 2026) is stored in `backtest_datas.csv`.

**Stage 2 — Cointegration screening.** For each candidate pair, the `Coint_verif` class (`test_coint.py`) runs a battery of five sequential tests via `test_batterie()`:
1. Integration order verification (ADF on levels and first differences) — confirms both series are I(1).
2. Spread construction via Johansen eigenvector normalization — computes the hedge ratio β and the spread S = A − β·B.
3. Spread stationarity verification (ADF + KPSS + Phillips-Perron) — confirms the spread is stationary.
4. Formal cointegration tests (Engle-Granger + Johansen trace) — validates the cointegration relationship.
5. Hurst exponent — confirms mean-reverting behavior (H < 0.5).

Any test failure raises a `CointError`, immediately discarding the pair. From ~40 candidates, 8 survive.

**Stage 3 — OU model calibration.** For each surviving pair, the `OUEstimator` class (`fit_ou_model.py`) fits an Ornstein-Uhlenbeck model to the spread by OLS regression on the exact AR(1) discretization. This yields three continuous-time parameters: θ (mean-reversion speed), μ (long-run mean), σ (diffusion coefficient). Derived quantities include the half-life t½ = ln(2)/θ and the stationary standard deviation σ/√(2θ).

**Stage 4 — Tradability filtering.** Pairs with half-lives exceeding ~80 days or insufficient volatility are discarded. This reduces the set from 8 to 4 pairs.

**Stage 5 — Signal generation.** The `Strategie` class (`Pair_trading_strat.py`) receives the OU parameters and implements a z-score-based finite state machine. The z-score z(t) = (spread(t) − μ) / σ_stationary determines transitions between three states: flat (0), long spread (+1), short spread (−1). Entry occurs when |z| > k_entry; exit occurs when |z| < k_exit or |z| > stop_loss.

**Stage 6 — Backtesting.** Two modes are available:
- `backtest()`: computes PnL from spread movements with proportional transaction costs.
- `simulate_capital()`: tracks explicit share quantities, liquidity, and mark-to-market portfolio value.

The backtest uses out-of-sample data with all parameters (hedge ratio, μ, σ, θ) frozen from the in-sample estimation.

**Key takeaway:** The pipeline is strictly sequential and one-directional: each stage produces outputs consumed by the next. There is no feedback loop or rolling re-estimation — parameters estimated in-sample are held fixed throughout the backtest.

---

### Q002 — Module Responsibilities

**Question:** Explain the role of each of the three Python modules (`test_coint.py`, `fit_ou_model.py`, `Pair_trading_strat.py`). Why is this separation useful?

**Answer:**

**`test_coint.py` — Cointegration verification module.** Contains the `Coint_verif` class, which takes two price series as input and provides:
- `auto_integration()`: verifies both series are I(1) via ADF tests.
- `spread_n_hedge_ratio` (property): computes the spread and hedge ratio via the Johansen procedure. Also available as a static method `spread_n_hedge_ratio_static()`.
- `spread_stationnarity()`: tests stationarity of the spread using ADF, KPSS, and Phillips-Perron.
- `coint_test()`: runs formal Engle-Granger and Johansen trace tests.
- `Hurst_test()`: computes the Hurst exponent.
- `test_batterie()`: chains all tests in sequence.

The class also defines `CointError`, a custom exception used as a rejection signal.

**`fit_ou_model.py` — OU estimation module.** Contains:
- `simulate_OU()`: a standalone function to simulate OU sample paths (used for validation and exploration).
- `OUEstimator` class: fits OU parameters from observed spread data via `fit_ols()`, exposes derived quantities (`half_life`, `stationary_variance`, `stationary_std` as properties), computes asymptotic confidence intervals (`confidence_intervals()`), and runs residual diagnostic tests (`diagnostic_tests()`).

**`Pair_trading_strat.py` — Strategy and backtesting module.** Contains the `Strategie` class, which:
- Takes an `OUEstimator` instance to initialize μ and σ_stationary.
- `signal()`: implements the z-score state machine for one time step.
- `backtest()`: runs the full backtest on a spread array, returning cumulative PnL and performance metrics.
- `simulate_capital()`: runs a more realistic capital simulation with explicit position sizing.

**Why this separation is useful:**

1. **Testability**: each module can be tested independently. You can verify cointegration tests on synthetic data without touching the strategy logic.
2. **Reusability**: the `OUEstimator` could be used in a completely different context (e.g., interest rate modeling) without modification.
3. **Separation of concerns**: statistical validation (is this pair tradable?), model calibration (what are the dynamics?), and strategy execution (how do we trade it?) are conceptually distinct questions. Mixing them in one module would create coupling between unrelated decisions.
4. **Composability**: the orchestration notebook (`test_pair.ipynb`) imports all three and composes them into a pipeline. A different notebook or script could reuse the same modules with different orchestration logic (e.g., rolling recalibration).

**Key takeaway:** The three modules correspond to the three core questions of a statistical arbitrage pipeline: *Is this pair cointegrated?* → *What are its mean-reversion dynamics?* → *How should we trade it?*

---

### Q003 — In-sample vs Out-of-sample

**Question:** How does the project separate in-sample and out-of-sample data? What parameters are estimated in-sample and which are held fixed during the backtest? What risks arise from this design?

**Answer:**

**Data split:**
- **In-sample (training):** Jan 2010 – Jan 2024 (~14 years, ~3500 daily observations). Stored in `financial_datas.csv`.
- **Out-of-sample (backtest):** Jan 2024 – Jul 2026 (~2.5 years, ~630 daily observations). Stored in `backtest_datas.csv`.

The split is temporal — there is no overlap and no data leakage between the two periods.

**What is estimated in-sample and held fixed:**
- The **pair selection itself** (which pairs are cointegrated) — determined by the test battery on 2010–2024 data.
- The **hedge ratio β** — computed by the Johansen eigenvector on 2010–2024 prices.
- The **OU parameters θ, μ, σ** — estimated by OLS on the in-sample spread.
- The **stationary standard deviation** σ/√(2θ) — used to normalize the z-score during the backtest.

**What is NOT re-estimated:**
- None of the above is updated during the backtest. The strategy parameters (k_entry, k_exit, stop_loss) are fixed defaults, not optimized at all.

**Risks arising from this design:**

1. **Parameter drift.** The hedge ratio β captures the long-run equilibrium relationship as of Jan 2024. Over 2.5 years, the relative fundamentals of the two companies may shift (earnings divergence, sector rotation, regulatory changes), causing the true β to drift away from the estimated value. This would mean the constructed spread S = A − β·B is no longer stationary, and the strategy would trade on a signal that no longer mean-reverts.

2. **μ and σ drift.** Even if β remains stable, the long-run mean μ and volatility σ of the spread may change. If σ decreases, the z-score thresholds become too tight (frequent entries into weak signals). If μ shifts, the strategy trades around a stale equilibrium level.

3. **Survivorship bias in pair selection.** The 8 pairs that pass the cointegration tests on 2010–2024 may include pairs that were cointegrated by chance over that specific window but whose relationship breaks down out-of-sample. Indeed, only 1 of 4 backtested pairs (UNH–ELV) shows positive PnL.

4. **No adaptation mechanism.** A production strategy would typically re-estimate parameters on a rolling window (e.g., re-run Johansen every month on the most recent 2–3 years of data). The static approach used here means the strategy cannot adapt to changing market conditions.

**Key takeaway:** The in-sample/out-of-sample split is clean and avoids look-ahead bias in the backtest, but the static parameter approach is a significant limitation. A 14-year training window may be too long — older data may reflect relationships that no longer hold, diluting the signal from more recent dynamics.

---

### Q004 — Economic Pre-filtering

**Question:** Why does the pipeline begin with an economic pre-filter before running statistical tests? What problem does this solve, and what would happen if you skipped it?

**Answer:**

**The spurious cointegration problem.** If you test all possible pairs from a universe of N stocks, you are testing N·(N−1)/2 pairs. For N = 500 stocks (a typical mid-cap universe), that is ~125,000 pairs. At a 5% significance level, you would expect ~6,250 pairs to falsely appear cointegrated by pure chance, even if no genuine economic relationship exists. This is a severe multiple testing problem.

Spuriously cointegrated pairs are dangerous because:
- The statistical relationship is a sample artifact — it has no structural reason to persist out-of-sample.
- A strategy based on a spurious relationship will enter positions expecting mean-reversion that never occurs, leading to systematic losses.
- The backtest may even look profitable in-sample (overfitting), making the problem harder to detect.

**What the economic pre-filter does.** The `pairs_universe.csv` file restricts the candidate set to ~40 pairs where a fundamental economic link exists: direct competitors (KO/PEP), same macro driver (CAT/DE), same commodity exposure (XOM/CVX), payment networks (V/MA), etc. This serves two purposes:

1. **Reduces the multiple testing burden.** Testing 40 pairs instead of 125,000 dramatically reduces the expected number of false positives.
2. **Ensures structural plausibility.** If two companies share the same revenue drivers, cost structure, and regulatory environment, any cointegration detected is more likely to reflect a genuine economic equilibrium — and therefore more likely to persist out-of-sample.

**What would happen without the pre-filter:**
- You would find many more "cointegrated" pairs, but most would be spurious.
- Out-of-sample performance would be much worse on average.
- You would need much more aggressive statistical corrections (e.g., Bonferroni or Benjamini-Hochberg) to control the false discovery rate, which would dramatically reduce statistical power.

**A nuance:** The economic pre-filter is itself subjective. The choice of which pairs to include depends on domain knowledge and judgment. A pair with a valid economic rationale could still fail to be cointegrated (different capital structures, different growth trajectories), and conversely, a statistically cointegrated pair without an obvious economic rationale might still be tradable if the relationship is driven by latent factors. But on balance, the pre-filter is a strong prior that significantly improves the signal-to-noise ratio of the screening process.

**Key takeaway:** The economic pre-filter is not just a convenience — it is a critical component that transforms a multiple-testing nightmare into a tractable problem. Without it, the statistical tests alone cannot reliably distinguish real cointegration from noise.

---

### Q005 — Static Parameters

**Question:** The hedge ratio, μ, and σ are estimated once on the training set and never updated. What are the consequences of this choice for a strategy running over 2.5 years of out-of-sample data? How would you modify the architecture to address this?

**Answer:**

**Consequences of static parameters:**

1. **Hedge ratio β drift.** The hedge ratio captures the ratio of price sensitivities between the two assets as estimated over 2010–2024. Over 2.5 years, this ratio can shift due to:
   - Fundamental divergence: one company grows faster, acquires businesses, or faces regulatory changes.
   - Sector rotation: relative valuations shift as capital flows into different sectors.
   - M&A activity: a merger announcement can permanently alter the price relationship.
   
   When β drifts, the spread S = A − β·B is no longer the optimal linear combination. The spread may appear non-stationary, triggering false signals or failing to mean-revert as expected.

2. **μ drift (mean shift).** If the equilibrium level of the spread shifts, the z-score is computed around a stale mean. For example, if the true μ increases by one standard deviation, the strategy systematically under-estimates z when the spread is above the old mean — it enters short positions too late and exits too early, and enters long positions too early when the spread drops to the old μ level.

3. **σ drift (volatility regime change).** If the true σ increases:
   - The z-score is deflated (movements appear smaller than they are), so entry thresholds are hit less often → the strategy trades less, potentially missing profitable opportunities.
   - But when positions are taken, the actual spread movements are larger than expected, so both profits and losses are amplified.
   
   If σ decreases, the z-score is inflated — the strategy enters positions on noise and experiences many small losses.

4. **Compounding effect.** Over 2.5 years, all three parameters may drift simultaneously. The drift in β affects the spread itself, which in turn affects the relevance of μ and σ. The errors compound and the strategy can end up trading a signal that bears little resemblance to the original mean-reverting process.

**Evidence from the backtest results.** The fact that 3 out of 4 pairs show negative out-of-sample PnL is consistent with parameter drift. The pairs that were well-behaved over 14 years of in-sample data may have entered a different regime in 2024–2026.

**How to modify the architecture:**

1. **Rolling window re-estimation.** The simplest fix: re-estimate β, μ, and σ on a rolling window (e.g., the most recent 2–3 years) at regular intervals (e.g., monthly). This tracks slow drifts in the relationship. Implementation: at each re-estimation point, run `Coint_verif.spread_n_hedge_ratio_static()` and `OUEstimator.fit_ols()` on the most recent N observations.

2. **Kalman filter for dynamic β.** Model the hedge ratio as a time-varying state: β(t) = β(t−1) + η(t). The observation equation is: price_A(t) = β(t)·price_B(t) + spread(t). A Kalman filter continuously updates the estimate of β(t) as new price data arrives, without requiring a fixed window. This is more adaptive than rolling estimation and better handles gradual drift.

3. **Cointegration monitoring.** Add a real-time cointegration stability check (e.g., recursive ADF tests, CUSUM statistics on the spread residuals). When the test indicates that cointegration has broken down, the strategy stops trading that pair until the relationship is re-established.

4. **Adaptive μ and σ.** Use an exponentially weighted moving average (EWMA) for μ and σ of the spread, with a decay factor calibrated to the half-life. This allows the z-score normalization to adapt to recent spread dynamics without requiring a full re-estimation.

**Architectural impact.** The current architecture cleanly separates estimation (in-sample) from execution (out-of-sample). Adding rolling re-estimation requires merging these phases: the strategy must periodically call back into `Coint_verif` and `OUEstimator` during the backtest. This adds complexity but is essential for a realistic strategy. The `Strategie` class would need access to a data buffer and a re-estimation schedule.

**Key takeaway:** Static parameters are a reasonable first approximation for a research prototype but are fundamentally incompatible with a production strategy. The primary improvement would be rolling window re-estimation of the hedge ratio and OU parameters, combined with a cointegration stability monitor that halts trading when the relationship breaks down.

---

## 2. Mathematical and Statistical Foundations

---

### Q006 — Cointegration vs Correlation

**Question:** What is the difference between correlation and cointegration? Why is cointegration the correct concept for pair trading?

**Answer:**

**Correlation** measures the linear co-movement of *returns* (or more generally, of two stationary series) over a given window. Two assets can have high correlation — their daily returns tend to move in the same direction — yet their *price levels* can drift arbitrarily far apart over time. Correlation is a short-horizon, stationary concept: it says nothing about whether the price spread between two assets will revert to a mean.

**Cointegration** is a property of *non-stationary* (I(1)) price level series. Two series X(t) and Y(t) are cointegrated if there exists a linear combination X(t) − β·Y(t) = S(t) that is stationary (I(0)). This means the spread S(t) fluctuates around a constant mean and cannot diverge permanently. The key difference: cointegration is a *long-run equilibrium* concept. Even if the two prices temporarily diverge, the spread will eventually revert.

**Why cointegration is correct for pair trading:**

Pair trading profits from mean-reversion of the spread. This requires:
1. The spread must be stationary (bounded fluctuations around a mean).
2. Deviations from the mean must be temporary and predictable in direction (they will revert).

Correlation does *not* guarantee either property. Two highly correlated stocks can have a spread that trends upward indefinitely (a random walk with correlated increments). Conversely, two assets with low return correlation could still be cointegrated if their prices share a common stochastic trend.

**Concrete example:** If KO and PEP both have daily return correlation of 0.85, their prices might still drift apart by $50 over 10 years with no tendency to revert. The high correlation tells you they move together day-to-day but says nothing about the price gap. If they are cointegrated, the spread KO − β·PEP is stationary: it fluctuates in a bounded band and any deviation from the mean is a trading opportunity.

**Mathematical formulation:** Let X(t) ~ I(1), Y(t) ~ I(1). Correlation concerns the stationary series ΔX(t) and ΔY(t). Cointegration concerns the existence of β such that X(t) − β·Y(t) ~ I(0). These are fundamentally different properties. The Granger representation theorem establishes that cointegrated series admit an error correction model (ECM), which formalizes the mean-reversion mechanism that pair trading exploits.

**Key takeaway:** Correlation measures short-term co-movement of returns; cointegration measures long-run equilibrium of price levels. Pair trading exploits mean-reversion of the price spread, which requires cointegration, not correlation.

---

### Q007 — Integration Order

**Question:** What does it mean for a time series to be I(1)? Why is verifying the integration order of both price series a necessary precondition for cointegration testing?

**Answer:**

**Definition of I(d).** A time series X(t) is *integrated of order d*, written I(d), if it requires exactly d applications of the differencing operator Δ to become stationary. Formally:
- I(0): X(t) is stationary (stable mean, autocovariance depends only on lag).
- I(1): X(t) is non-stationary, but ΔX(t) = X(t) − X(t−1) is stationary.
- I(2): X(t) requires two differences to become stationary.

Most equity price series are well-modeled as I(1): the prices themselves exhibit a stochastic trend (random walk behavior), but the returns (first differences) are approximately stationary.

**Why verifying I(1) is a precondition for cointegration:**

Cointegration is defined *only* for I(1) processes. Formally, two series X(t) and Y(t) are cointegrated of order CI(1,1) if:
1. Both X(t) ~ I(1) and Y(t) ~ I(1).
2. There exists a linear combination X(t) − β·Y(t) that is I(0).

If either series is already I(0) (stationary), cointegration is undefined — a stationary series doesn't need another series to "cancel" its stochastic trend, because it has no stochastic trend. Taking any linear combination of an I(0) series with an I(1) series would still be I(1) (the non-stationary component dominates).

If a series is I(2), standard cointegration tests for CI(1,1) are invalid. The asymptotic distributions of the test statistics (ADF, Engle-Granger, Johansen) are derived under the I(1) assumption. Applying them to I(2) data produces misleading results.

**Implementation in `test_coint.py:auto_integration()`:** The method performs four ADF tests:
1. ADF on X(t): expects to *fail* to reject H₀ (unit root present) → confirms X is non-stationary.
2. ADF on Y(t): same check for the second series.
3. ADF on ΔX(t): expects to *reject* H₀ → confirms the first difference is stationary.
4. ADF on ΔY(t): same check.

Together, these four tests confirm that both series are I(1): non-stationary in levels, stationary in first differences. If a series is already stationary in levels, it is discarded (it's I(0)). If its first difference is not stationary, it might be I(2) or higher, and the standard cointegration framework does not apply.

**Key takeaway:** Cointegration is a relationship between I(1) series where a linear combination "cancels" the common stochastic trend. Verifying the integration order ensures the mathematical framework (Engle-Granger theorem, Johansen procedure) is applicable.

---

### Q008 — Ornstein-Uhlenbeck SDE

**Question:** Write the Ornstein-Uhlenbeck stochastic differential equation and explain each term. Under what conditions does the process have a stationary distribution, and what is that distribution?

**Answer:**

**The SDE:**

$$dX(t) = \theta(\mu - X(t))\,dt + \sigma\,dW(t)$$

**Term-by-term explanation:**

- **θ > 0** — the *mean-reversion speed*. It controls how quickly the process is pulled back toward μ. A larger θ means faster reversion. Its units are inverse-time (e.g., day⁻¹ if t is measured in days).

- **μ** — the *long-run mean* (or equilibrium level). When X(t) > μ, the drift term θ(μ − X(t)) is negative, pushing X downward. When X(t) < μ, the drift is positive, pushing X upward. This is the mean-reversion mechanism.

- **σ > 0** — the *diffusion coefficient* (or volatility parameter). It scales the random noise component. Its units are [X-units] · [time]^(−1/2).

- **W(t)** — a standard Brownian motion (Wiener process). dW(t) represents Gaussian white noise with variance dt. This is the source of randomness.

**Intuition:** The SDE describes a process that behaves like a spring: it is always being pulled toward μ (with strength proportional to the displacement) but is constantly perturbed by random shocks. The balance between the restoring force (θ) and the noise (σ) determines the equilibrium distribution.

**Condition for a stationary distribution:**

The OU process has a stationary distribution if and only if **θ > 0** (strictly positive mean-reversion speed). When θ > 0, the restoring force dominates over the diffusion at large displacements, preventing the process from diverging. When θ ≤ 0, the process is explosive (θ < 0) or a random walk (θ = 0) and has no stationary distribution.

**The stationary distribution:**

When θ > 0, as t → ∞, the distribution of X(t) converges to:

$$X(\infty) \sim \mathcal{N}\left(\mu, \frac{\sigma^2}{2\theta}\right)$$

The stationary mean is μ and the stationary variance is σ²/(2θ). This can be derived by computing the conditional variance Var[X(t) | X(0)] using the explicit solution and taking the limit as t → ∞ (see Q011 for the full derivation).

**Interpretation for pair trading:** The stationary distribution tells us the long-run behavior of the spread. The z-score used in the strategy is z(t) = (S(t) − μ) / √(σ²/(2θ)), which is simply the spread normalized to have mean 0 and variance 1 under the stationary distribution. Entry at z = ±2 means the spread is 2 standard deviations from equilibrium — a rare event under the stationary distribution that is expected to revert.

**Key takeaway:** The OU process is the simplest continuous-time mean-reverting process with Gaussian noise. It has a stationary distribution N(μ, σ²/(2θ)) when θ > 0, which provides the natural scale for defining trading thresholds.

---

### Q009 — OU Discretization

**Question:** Derive the exact discretization of the continuous-time OU process at uniform time intervals Δt. Show how the discrete parameters (a, b, σ_ε) map to the continuous-time parameters (θ, μ, σ).

**Answer:**

**Starting point:** The OU SDE dX(t) = θ(μ − X(t))dt + σ dW(t) has the explicit solution (obtained via the integrating factor e^(θt)):

$$X(t) = e^{-\theta t}X(0) + \mu(1 - e^{-\theta t}) + \sigma \int_0^t e^{-\theta(t-s)}\,dW(s)$$

**Conditional distribution at time t+Δt given X(t):**

Applying the solution over the interval [t, t+Δt]:

$$X(t+\Delta t) = e^{-\theta \Delta t} X(t) + \mu(1 - e^{-\theta \Delta t}) + \sigma \int_t^{t+\Delta t} e^{-\theta(t+\Delta t - s)}\,dW(s)$$

The stochastic integral is Gaussian with mean 0 and variance:

$$\text{Var}\left[\sigma \int_t^{t+\Delta t} e^{-\theta(t+\Delta t - s)}\,dW(s)\right] = \sigma^2 \int_t^{t+\Delta t} e^{-2\theta(t+\Delta t - s)}\,ds = \frac{\sigma^2}{2\theta}(1 - e^{-2\theta \Delta t})$$

So the conditional distribution is:

$$X(t+\Delta t) \mid X(t) \sim \mathcal{N}\left(e^{-\theta \Delta t}X(t) + \mu(1 - e^{-\theta \Delta t}),\; \frac{\sigma^2}{2\theta}(1 - e^{-2\theta \Delta t})\right)$$

**Defining the discrete parameters:**

Let a = e^(−θΔt), b = μ(1 − a), and σ_ε² = σ²(1 − a²)/(2θ). Then:

$$X_{n+1} = a \cdot X_n + b + \sigma_\varepsilon \cdot \varepsilon_n, \quad \varepsilon_n \sim \mathcal{N}(0, 1) \text{ i.i.d.}$$

This is an **exact** AR(1) representation — not an Euler approximation. The noise terms ε_n are independent because the OU process is Markov and the stochastic integrals over non-overlapping intervals are independent.

**Inverse mapping (discrete → continuous):**

Given estimates â, b̂, σ̂_ε from OLS regression:

$$\theta = -\frac{\ln(\hat{a})}{\Delta t}$$

$$\mu = \frac{\hat{b}}{1 - \hat{a}}$$

$$\sigma = \hat{\sigma}_\varepsilon \sqrt{\frac{-2\ln(\hat{a})}{\Delta t(1 - \hat{a}^2)}}$$

The last formula comes from solving σ_ε² = σ²(1 − a²)/(2θ) for σ, substituting θ = −ln(a)/Δt:

$$\sigma^2 = \sigma_\varepsilon^2 \cdot \frac{2\theta}{1 - a^2} = \sigma_\varepsilon^2 \cdot \frac{-2\ln(a)}{\Delta t(1 - a^2)}$$

**Validity conditions:**
- θ > 0 requires a ∈ (0, 1). This is checked at `fit_ou_model.py:60`.
- If â ≥ 1, the process is not mean-reverting (unit root or explosive).
- If â ≤ 0, the process oscillates with sign changes every step, which is non-physical for a spread.
- The discretization is exact regardless of the size of Δt — no small-Δt approximation is needed.

**What the implementation does:** `fit_ols()` in `fit_ou_model.py` performs exactly this procedure. Lines 51–53 set up the OLS regression X_{n+1} on [1, X_n]. Lines 67–72 apply the inverse mapping. The formulas match the derivation above.

**Key takeaway:** The OU process discretizes *exactly* to an AR(1) process. The mapping between discrete and continuous parameters is bijective (for a ∈ (0,1)), which is why OLS on the AR(1) form is a valid estimation strategy for the continuous-time OU parameters.

---

### Q010 — Half-life Derivation

**Question:** Derive the half-life formula t½ = ln(2)/θ from the OU SDE. What exactly does the half-life measure in the context of this strategy?

**Answer:**

**Derivation:**

Start from the OU SDE: dX(t) = θ(μ − X(t))dt + σ dW(t).

The half-life is defined in the *deterministic* limit (σ = 0), where the process follows the ODE:

$$\frac{dX(t)}{dt} = \theta(\mu - X(t))$$

This is a first-order linear ODE with solution:

$$X(t) = \mu + (X(0) - \mu)e^{-\theta t}$$

The deviation from the mean decays exponentially: D(t) = X(t) − μ = D(0)·e^(−θt).

The half-life t½ is the time at which the deviation has decayed to half its initial value:

$$D(t_{1/2}) = \frac{1}{2}D(0)$$

$$D(0) \cdot e^{-\theta t_{1/2}} = \frac{1}{2} D(0)$$

$$e^{-\theta t_{1/2}} = \frac{1}{2}$$

$$-\theta t_{1/2} = \ln\left(\frac{1}{2}\right) = -\ln(2)$$

$$\boxed{t_{1/2} = \frac{\ln(2)}{\theta}}$$

**What the half-life measures in the strategy context:**

The half-life is the *expected time for the spread to revert halfway to its mean*, assuming the deterministic dynamics dominate. In the stochastic setting, the spread is continuously buffeted by noise, so it never follows the deterministic path exactly. However, the half-life provides a useful order-of-magnitude estimate of the trading horizon.

Practical implications:
- **Position sizing and holding period:** If t½ = 55 days (UNH–ELV), a typical trade should be expected to last on the order of 1–2 half-lives (55–110 days). Setting `max_holding_days` should be calibrated relative to t½.
- **Pair selection:** A very large half-life (e.g., 200 days) means the spread reverts so slowly that transaction costs, parameter drift, and regime change risk erode any potential profit. The project discards pairs with t½ > 80 days.
- **Relationship to θ:** Since t½ = ln(2)/θ, doubling θ halves the half-life. The pairs retained have θ ∈ [0.010, 0.027], corresponding to half-lives of 25–69 days.

**Caveat:** The half-life is a deterministic concept applied to a stochastic process. In reality, the random noise σ·dW means the actual reversion time is a random variable. For a highly volatile spread (large σ relative to θ), the noise can push the spread further from the mean before reversion occurs, making the actual time to reach the mean much longer (or shorter) than t½. The half-life is best understood as characterizing the *expected* rate of mean-reversion in the drift, not as a prediction of actual trade duration.

**Key takeaway:** t½ = ln(2)/θ is derived from the deterministic part of the OU dynamics. It measures how fast the spread is *pulled* toward its mean, and serves as the primary criterion for deciding whether a pair is tradable within a practical time horizon.

---

### Q011 — Stationary Variance Derivation

**Question:** Derive the stationary variance σ²/(2θ) of the OU process. Start from the SDE and compute E[X(t)²] as t → ∞.

**Answer:**

**Method: from the explicit solution.**

The explicit solution of the OU SDE with initial condition X(0) = x₀ is:

$$X(t) = \mu + (x_0 - \mu)e^{-\theta t} + \sigma \int_0^t e^{-\theta(t-s)}\,dW(s)$$

The conditional mean is:

$$E[X(t)] = \mu + (x_0 - \mu)e^{-\theta t}$$

The conditional variance is (using the Itô isometry on the stochastic integral):

$$\text{Var}[X(t)] = E\left[\left(\sigma \int_0^t e^{-\theta(t-s)}\,dW(s)\right)^2\right] = \sigma^2 \int_0^t e^{-2\theta(t-s)}\,ds$$

Computing the integral with the substitution u = t − s:

$$\sigma^2 \int_0^t e^{-2\theta u}\,du = \sigma^2 \left[-\frac{1}{2\theta}e^{-2\theta u}\right]_0^t = \frac{\sigma^2}{2\theta}\left(1 - e^{-2\theta t}\right)$$

**Taking the limit as t → ∞** (requires θ > 0):

$$\lim_{t \to \infty} \text{Var}[X(t)] = \frac{\sigma^2}{2\theta}\left(1 - 0\right) = \boxed{\frac{\sigma^2}{2\theta}}$$

The mean converges to μ and the variance converges to σ²/(2θ), giving the stationary distribution N(μ, σ²/(2θ)).

**Intuitive interpretation:** The stationary variance represents the balance between two opposing forces:
- **σ² (diffusion):** noise pushes the process away from the mean, increasing variance.
- **2θ (mean-reversion):** the restoring force pulls the process back, reducing variance.

A larger θ (faster reversion) produces a tighter stationary distribution. A larger σ (more noise) produces a wider one. The factor of 2 in the denominator comes from the exponential decay rate of variance being 2θ (twice the decay rate of the mean), because variance involves squared deviations.

**Implementation:** In `fit_ou_model.py`, the `stationary_variance` property (line 91–95) returns `self.sigma**2 / (2 * self.theta)`, and `stationary_std` (line 98–101) returns its square root. The `Strategie` class uses `stationary_std` to normalize the z-score: z(t) = (S(t) − μ) / σ_∞ where σ_∞ = σ/√(2θ).

**Key takeaway:** The stationary variance σ²/(2θ) is the fundamental scale of the OU process. It determines the natural units for the z-score, and therefore directly controls when the strategy enters and exits positions.

---

### Q012 — OLS vs MLE Equivalence

**Question:** The report claims that OLS estimation on the discretized AR(1) form is "equivalent to MLE for the Gaussian case." Under what precise conditions is this true? When does the equivalence break down?

**Answer:**

**The conditional log-likelihood of the discretized OU:**

Given observations z₀, z₁, ..., z_n at intervals Δt, the exact transition density is:

$$z_{i+1} \mid z_i \sim \mathcal{N}(b + a \cdot z_i,\; \sigma_\varepsilon^2)$$

where a = e^(−θΔt), b = μ(1−a), σ_ε² = σ²(1−a²)/(2θ).

The conditional log-likelihood (conditioning on z₀) is:

$$\ell(a, b, \sigma_\varepsilon^2) = -\frac{n}{2}\ln(2\pi) - \frac{n}{2}\ln(\sigma_\varepsilon^2) - \frac{1}{2\sigma_\varepsilon^2}\sum_{i=0}^{n-1}(z_{i+1} - b - a z_i)^2$$

**Why OLS maximizes this likelihood:**

Maximizing ℓ with respect to (a, b) for fixed σ_ε² is equivalent to minimizing the sum of squared residuals Σ(z_{i+1} − b − az_i)², which is exactly the OLS criterion. The MLE for σ_ε² is then σ̂²_ε = (1/n)Σê_i², the average squared residual.

The key insight: when the errors ε_i are i.i.d. Gaussian with constant variance, the likelihood factorizes into a product of Gaussian densities, and the maximum likelihood estimates of the regression coefficients coincide with OLS estimates.

**Precise conditions for equivalence:**

1. **Gaussian innovations.** The transition density must be Gaussian. For the OU process with Brownian noise, this holds exactly by construction.
2. **Constant variance (homoscedasticity).** σ_ε² must be the same for all transitions. This holds when σ and θ are constant over time.
3. **Independence of residuals.** The ε_i must be independent. This holds because the OU process is Markov: given z_i, z_{i+1} is independent of z_{i−1}, z_{i−2}, .... The exact discretization preserves this property.
4. **Conditional likelihood, not full likelihood.** The equivalence is for the conditional likelihood given z₀. The full (unconditional) likelihood would include the marginal distribution of z₀, which depends on whether z₀ is drawn from the stationary distribution. In practice, the difference is negligible for large n.

**When the equivalence breaks down:**

1. **Non-Gaussian noise.** If the driving noise has heavy tails (e.g., a Lévy process instead of Brownian motion), the transition density is no longer Gaussian. OLS still minimizes squared errors but no longer maximizes the likelihood.
2. **Time-varying parameters.** If θ or σ change over time (regime switching, stochastic volatility), the residuals are no longer identically distributed. OLS gives a pooled estimate that averages over regimes, while MLE with the correct model specification would be more efficient.
3. **ARCH/GARCH effects.** If the residual variance is conditionally heteroscedastic (depends on past values), OLS is still consistent but inefficient. MLE with an ARCH model would be more efficient. The ARCH-LM diagnostic test in `diagnostic_tests()` specifically checks for this violation.
4. **Unequally spaced observations.** If Δt varies (e.g., weekends, holidays), the simple AR(1) form with constant a and σ_ε no longer applies. MLE would need to use the correct transition density for each observation interval. OLS on the raw data would be incorrect.
5. **Measurement noise.** If the observed spread contains measurement error (e.g., bid-ask bounce), the observations are z̃_i = z_i + η_i, and the AR(1) regression suffers from errors-in-variables bias. MLE with a state-space model (Kalman filter) would be needed.

**Minor discrepancy in the implementation:** The implementation uses n−2 as the denominator for σ̂²_ε (line 57 of `fit_ou_model.py`), which is the unbiased OLS estimator. The MLE would use n. The difference is negligible for n ≈ 3500 but represents a conceptual distinction: OLS and MLE give slightly different variance estimates in finite samples.

**Key takeaway:** OLS and conditional MLE are equivalent for the discretized OU because the transition density is Gaussian with constant variance and independent errors. The equivalence breaks down when any of these conditions is violated — most commonly through ARCH effects (time-varying volatility), non-Gaussian noise, or irregularly spaced observations.

---

### Q013 — Johansen vs Engle-Granger

**Question:** Compare the Johansen procedure and the Engle-Granger two-step method for testing cointegration. In what sense is Johansen "symmetric"? When would you prefer one over the other?

**Answer:**

**Engle-Granger two-step method:**

1. **Step 1 — Cointegrating regression.** Regress one variable on the other by OLS: Y(t) = α + β·X(t) + e(t). This gives the residuals ê(t) = Y(t) − α̂ − β̂·X(t).
2. **Step 2 — Unit root test on residuals.** Apply the ADF test to ê(t). If the residuals are stationary (reject H₀ of unit root), the series are cointegrated.

The `coint()` function from statsmodels (used at `test_coint.py:100`) implements exactly this procedure.

**Johansen procedure:**

The Johansen method works within a Vector Error Correction Model (VECM) framework. For a bivariate system (X, Y):

$$\Delta Z(t) = \Pi Z(t-1) + \Gamma_1 \Delta Z(t-1) + ... + u(t)$$

where Z(t) = (X(t), Y(t))' and Π = αβ'. The cointegration rank r equals the rank of Π, which is determined by eigenvalue analysis. The test uses two statistics:
- **Trace statistic:** tests H₀: rank ≤ r vs H₁: rank > r.
- **Maximum eigenvalue statistic:** tests H₀: rank = r vs H₁: rank = r + 1.

The eigenvector β associated with the largest eigenvalue gives the cointegrating vector (hedge ratio). In the implementation (`test_coint.py:56–62`), `coint_johansen` returns the eigenvectors, and the first eigenvector (associated with the largest eigenvalue) is normalized so that v[0] = 1, giving spread = X + v[1]·Y (where v[1] is typically negative).

**In what sense Johansen is "symmetric":**

The Engle-Granger method requires choosing which variable is the dependent variable. Regressing Y on X gives a different β̂ (and therefore different residuals and test outcome) than regressing X on Y. This asymmetry is a well-known problem: the test result can depend on an arbitrary choice.

The Johansen procedure treats all variables symmetrically. It works with the joint system Z(t) = (X, Y)' and finds the cointegrating vector by solving a generalized eigenvalue problem. There is no distinction between "dependent" and "independent" variables. Swapping the order of X and Y in the data matrix changes the eigenvector components but not the implied spread (up to a scalar normalization). This symmetry is particularly valuable when there is no economic reason to designate one asset as "dependent."

**When to prefer each:**

| Criterion | Engle-Granger | Johansen |
|-----------|---------------|----------|
| **Number of variables** | Bivariate only | Arbitrary dimension (can detect multiple cointegrating relationships) |
| **Simplicity** | Simpler to implement and interpret | More complex (eigenvalue problem, VECM framework) |
| **Symmetry** | Asymmetric (depends on which variable is "Y") | Fully symmetric |
| **Power** | Lower power in small samples | Generally higher power |
| **Multiple cointegrating relationships** | Cannot detect | Natural framework (tests rank 0, 1, 2, ...) |
| **Hedge ratio** | Obtained from OLS regression (potentially biased by endogeneity) | Obtained from eigenvalue problem (super-consistent, less biased) |
| **Specification** | No lag structure needed beyond the ADF regression | Requires choosing `k_ar_diff` (number of lagged differences in VECM) |

**Prefer Engle-Granger when:** you have a simple bivariate system, want a quick test, and don't need the hedge ratio from the test itself (e.g., you'll use a different method for β).

**Prefer Johansen when:** you want a symmetric test, need the hedge ratio as a byproduct, may have more than two variables, or want to test the cointegration rank explicitly. This is why the project uses Johansen for spread construction and runs Engle-Granger as an additional confirmation.

**Why the project uses both:** The project uses Johansen for spread construction (`spread_n_hedge_ratio`) because it provides the symmetric hedge ratio, and then uses both Engle-Granger and Johansen trace as independent confirmation tests in `coint_test()`. Running both tests reduces the probability of false positives: a pair must pass both tests, exploiting the fact that they have different power characteristics and different sensitivity to specification choices.

**Key takeaway:** Johansen is "symmetric" because it treats all variables equivalently in a joint system, unlike Engle-Granger which requires a dependent/independent designation. For this bivariate pair trading application, Johansen is the natural choice for hedge ratio estimation, while both tests are used together for robust cointegration validation.

---

## 3. Statistical Testing Pipeline

---

### Q014 — Test Battery Logic

**Question:** The class `Coint_verif` in `test_coint.py` runs five sequential tests via `test_batterie()`. List them in order and explain the purpose of each test in the screening process.

**Answer:**

The method `test_batterie()` (lines 118–124) chains the following five steps, each acting as a filter that raises `CointError` on failure:

**Step 1 — `auto_integration()` — Integration order verification.**
Purpose: confirm both price series are I(1). Four ADF tests are run:
- ADF on raw prices X(t) and Y(t): must *fail* to reject H₀ (unit root present), confirming both series are non-stationary.
- ADF on first differences ΔX(t) and ΔY(t): must *reject* H₀, confirming the first differences are stationary.

This establishes the precondition for cointegration: both series must be integrated of order 1. If a series is already stationary (I(0)) or requires more than one differencing (I(2)+), cointegration in the standard CI(1,1) framework is not applicable.

**Step 2 — `spread_n_hedge_ratio` (property) — Spread construction via Johansen.**
Purpose: compute the hedge ratio β and construct the spread S = A − β·B. Internally, `coint_johansen(data, det_order=0, k_ar_diff=1)` solves the generalized eigenvalue problem of the VECM representation. The eigenvector associated with the largest eigenvalue is extracted, normalized so that v[0] = 1, and the spread is computed as [X, Y] @ v. The hedge ratio returned is −v[1].

This step does not test or reject — it constructs the linear combination that will be tested in subsequent steps. However, the Johansen result object is stored for use in step 4.

**Step 3 — `spread_stationnarity()` — Spread stationarity verification.**
Purpose: confirm the constructed spread is stationary using three complementary tests:
- ADF (H₀: unit root): spread must reject H₀ → evidence of stationarity.
- KPSS (H₀: stationary): spread must fail to reject H₀ → no evidence against stationarity.
- Phillips-Perron (H₀: unit root): spread must reject H₀ → robust stationarity evidence.

Using tests with opposite null hypotheses (ADF/PP vs KPSS) provides a confirmatory framework. The spread must pass all three.

**Step 4 — `coint_test()` — Formal cointegration tests.**
Purpose: formally test whether the two series are cointegrated using two independent methods:
- Engle-Granger: tests whether the residuals from the cointegrating regression have a unit root. Both the test statistic and p-value are checked.
- Johansen trace test: the trace statistic for rank r=0 (from the Johansen object computed in step 2) must exceed the 95% critical value, rejecting the null of no cointegration.

This step provides formal statistical evidence for cointegration, beyond the indirect evidence from spread stationarity.

**Step 5 — `Hurst_test()` — Hurst exponent.**
Purpose: a final, non-parametric confirmation of mean-reversion. The Hurst exponent H is computed on the spread via the R/S (rescaled range) method. H < 0.5 indicates mean-reverting behavior, H = 0.5 indicates a random walk, and H > 0.5 indicates trending behavior. The spread must have H < 0.5.

This is complementary to the parametric tests because it captures the global scaling behavior of the spread rather than relying on a specific autoregressive model.

**Why sequential with early termination:** Each test raises a `CointError` that immediately halts the battery. This is efficient because later tests (especially Johansen and Hurst) are more expensive. If a pair fails the cheap ADF test on raw prices, there is no need to compute the Johansen decomposition. The ordering is roughly from cheapest/most fundamental to most expensive/most confirmatory.

**Key takeaway:** The five-step battery progressively builds confidence that the pair is genuinely cointegrated: first verifying the preconditions (I(1)), then constructing the spread, then testing stationarity from multiple angles, then running formal cointegration tests, and finally confirming mean-reversion via the Hurst exponent.

---

### Q015 — ADF Test Mechanics

**Question:** Explain how the Augmented Dickey-Fuller test works. What is its null hypothesis? In `test_coint.py:auto_integration()`, why is the test applied twice — once expecting to fail to reject H₀, and once expecting to reject it?

**Answer:**

**How the ADF test works:**

The ADF test is a unit root test. It tests whether a time series has a unit root (is non-stationary) or is stationary.

The test is based on the regression:

$$\Delta y_t = \alpha + \gamma y_{t-1} + \sum_{j=1}^{p} \delta_j \Delta y_{t-j} + \varepsilon_t$$

where:
- $\Delta y_t = y_t − y_{t−1}$ is the first difference.
- $\gamma$ is the coefficient of interest: under H₀ (unit root), $\gamma$ = 0.
- The lagged differences $\Delta y_{t−j}$ are included to absorb serial correlation in the residuals — this is the "augmented" part compared to the basic Dickey-Fuller test.
- $p$ (the number of lags) is typically chosen by an information criterion (AIC or BIC). The `adfuller` function from statsmodels does this automatically.

**Null and alternative hypotheses:**
- H₀: $\gamma = 0$ (unit root present → series is non-stationary, I(1) or higher).
- H₁: $\gamma < 0$ (no unit root → series is stationary, I(0)).

The test statistic is $t_\gamma = \frac{\hat \gamma} {se(\hat \gamma)}$. Under H₀, this statistic does NOT follow a standard t-distribution — it follows the Dickey-Fuller distribution, which has heavier left tails. This is why special critical values (not from the normal distribution) are needed.

Decision rule: reject H₀ if the test statistic is *more negative* than the critical value (i.e., stat < critical value at the chosen significance level).

**Why the test is applied twice in `auto_integration()`:**

The goal is to establish that both price series are I(1), which requires two properties:
1. The *raw series* is non-stationary (has a unit root).
2. The *first-differenced series* is stationary (no unit root).

**First application (lines 30–35) — expecting to FAIL to reject H₀:**
```python
result_x = adfuller(self.x)
if result_x[0] < result_x[4][crit_level]:
    raise CointError("La série prixA est stationnaire...")
```
Here, if stat < critical value, the test rejects H₀ (unit root), meaning the series IS stationary. But we *need* it to be non-stationary for the I(1) requirement. So rejecting H₀ is a failure condition → the pair is discarded. We want to fail to reject H₀, confirming the series has a unit root.

**Second application (lines 37–45) — expecting to REJECT H₀:**
```python
result_dx = adfuller(dx)
if result_dx[0] >= result_dx[4]['5%']:
    raise CointError("La série dprixA n'est pas stationnaire...")
```
Here, the first-differenced series is tested. If stat ≥ critical value, the test fails to reject H₀ (unit root still present in the differenced series). This would mean the series needs more than one differencing to become stationary (I(2) or higher), violating the I(1) requirement. We need the test to reject H₀, confirming the differenced series is stationary.

**Logical structure:**
- Test 1 on levels: H₀ NOT rejected → confirms non-stationarity of prices ✓
- Test 2 on differences: H₀ rejected → confirms stationarity of returns ✓
- Together: the series is I(1) — non-stationary, but one differencing suffices.

**A subtlety:** Failing to reject H₀ is not the same as accepting H₀. The ADF test has limited power, especially against near-unit-root alternatives. A series with a very slow mean-reversion (θ close to 0) might fail to reject H₀ even though it is technically stationary. This is an inherent limitation of using "fail to reject" as evidence of non-stationarity, and it is one motivation for using the KPSS test (which has stationarity as H₀) as a complement.

**Minor implementation note:** In lines 42–45, the critical level used for the differenced series is hardcoded to `'5%'` regardless of the `crit_level` parameter. This is likely an oversight — the error message references `crit_level` but the actual comparison uses `'5%'`.

**Key takeaway:** The ADF test is applied in two opposite modes: first to confirm non-stationarity (fail to reject H₀ of unit root on levels), then to confirm stationarity (reject H₀ of unit root on differences). Together, these establish the I(1) property required for cointegration analysis.

---

### Q016 — KPSS Complementarity

**Question:** In `test_coint.py:spread_stationnarity()`, both ADF and KPSS tests are used on the spread. Why use both when they appear to test the same thing? What are the four possible combined outcomes and how should each be interpreted?

**Answer:**

**Why both tests are needed:**

ADF and KPSS test *different* null hypotheses:
- **ADF H₀:** the series has a unit root (non-stationary).
- **KPSS H₀:** the series is stationary.

This distinction is critical. A statistical test can only *reject* its null hypothesis with confidence. Failing to reject is not evidence *for* the null — it could simply mean the test lacks power. Therefore:
- ADF rejecting H₀ is evidence *against* a unit root (pro-stationarity).
- ADF failing to reject H₀ is ambiguous — it might mean a unit root exists, or the test is underpowered.
- KPSS failing to reject H₀ is ambiguous — it might mean the series is stationary, or the test is underpowered.
- KPSS rejecting H₀ is evidence *against* stationarity (pro-unit-root).

By combining both, we get a *confirmatory* framework where both tests must point in the same direction.

**The four possible combined outcomes:**

| ADF result | KPSS result | Interpretation |
|-----------|-------------|----------------|
| Reject H₀ (no unit root) | Fail to reject H₀ (stationary) | **Both agree: series is stationary.** Strong evidence. This is the desired outcome for the spread. |
| Fail to reject H₀ (unit root possible) | Reject H₀ (not stationary) | **Both agree: series is non-stationary.** Strong evidence against stationarity. Pair should be rejected. |
| Reject H₀ (no unit root) | Reject H₀ (not stationary) | **Contradictory.** ADF says stationary, KPSS says not. This can happen with a trend-stationary series, or near the boundary. Requires further investigation — neither conclusion is reliable. |
| Fail to reject H₀ (unit root possible) | Fail to reject H₀ (stationary) | **Inconclusive.** Both tests fail to reject their respective nulls. Insufficient evidence in either direction. The series may be near the stationary/non-stationary boundary. Larger samples or additional tests may help. |

**Implementation in the code (lines 73–92):**

The implementation requires *both* tests to give pro-stationarity results:
- ADF must reject H₀ (`adf[0] > adf[4][crit_level]` triggers rejection — note the condition checks for failure to reject, which raises an error).
- KPSS must fail to reject H₀ (`stat >= crit[crit_level]` triggers rejection, which raises an error).

So the pair is kept only in outcome 1 (both agree: stationary). Any other outcome discards the pair.

**Why this is conservative:** Requiring both tests to agree is a conservative (strict) filter. It reduces false positives (accepting a non-stationary spread as tradable) at the cost of potentially increasing false negatives (discarding a genuinely stationary spread that one test happens to flag). For a trading strategy, this conservatism is appropriate — the cost of trading a non-stationary spread (unlimited losses) far exceeds the cost of missing a valid pair (opportunity cost).

**KPSS specification detail:** The implementation uses `regression='c'` (line 85), which tests stationarity around a constant level. The alternative `regression='ct'` would test stationarity around a deterministic trend. Using `'c'` is correct for the spread, which should fluctuate around a constant mean μ under the OU model.

**Key takeaway:** ADF and KPSS are complementary because they have opposite null hypotheses. Using both creates a confirmatory framework: the spread is accepted as stationary only when both tests agree, reducing the chance of false positives from any single test.

---

### Q017 — Phillips-Perron Bug

**Question:** In `test_coint.py`, line 91–92, the Phillips-Perron test statistic is compared against the ADF critical values (`adf[4][crit_level]`). Is this correct? What are the consequences of this implementation choice?

**Answer:**

**The code in question:**
```python
pp = PhillipsPerron(spread)
if pp.stat >= adf[4][crit_level]:
    raise CointError(...)
```

Here, `adf` is the result from the ADF test run on lines 80–82. The PP test statistic `pp.stat` is being compared against the ADF critical values `adf[4][crit_level]`.

**Is this correct? No — it is a bug.**

The ADF and Phillips-Perron tests, while both testing for unit roots, have *different* asymptotic distributions and therefore *different* critical values. The reason:

- **ADF** augments the Dickey-Fuller regression with lagged differences to handle serial correlation parametrically. Its critical values are from the Dickey-Fuller distribution.
- **Phillips-Perron** handles serial correlation non-parametrically by applying a correction to the Dickey-Fuller test statistic. The PP statistic uses a different adjustment (Newey-West HAC estimator), and while its asymptotic distribution is the same as the basic Dickey-Fuller distribution under certain conditions, the finite-sample distributions can differ.

The `arch.unitroot.PhillipsPerron` class provides its own critical values. The correct comparison would be:

```python
if pp.stat >= pp.critical_values[crit_level]:
    raise CointError(...)
```

or equivalently, checking `pp.pvalue` against the significance level.

**Consequences of the bug:**

In practice, the ADF and PP critical values at the 5% level for a given sample size are often *numerically close* (both are around −2.86 for large samples with a constant). So the bug may not cause many incorrect decisions. However:

1. **The test is technically invalid.** The rejection region is defined by the wrong distribution, so the nominal 5% significance level is not guaranteed. The actual Type I error rate may be slightly above or below 5%.

2. **Direction of the error.** If the ADF critical values happen to be more negative than the PP critical values for this sample, the PP test is effectively run at a *more conservative* significance level (harder to reject). If they are less negative, the test is more liberal. The direction depends on the sample size and specification.

3. **The PP test adds little value as implemented.** Since it uses the ADF critical values, it essentially becomes a "different test statistic compared against the same threshold." The intended benefit of PP — robustness to heteroscedasticity and serial correlation with its own calibrated distribution — is partially lost.

**How to fix:**

```python
pp = PhillipsPerron(spread)
if pp.pvalue > 0.05:
    raise CointError(f"Phillips-Perron p-value too high: {pp.pvalue:.4f}")
```

Or use the critical values from the PP object directly. The `arch` library's `PhillipsPerron` object exposes `.pvalue` and `.critical_values` attributes.

**Key takeaway:** Using ADF critical values for the PP test statistic is a bug. While the practical impact is likely small (the critical values are numerically similar), it undermines the theoretical validity of the PP test. The fix is straightforward: use `pp.pvalue` or `pp.critical_values` instead of `adf[4][crit_level]`.

---

### Q018 — Hurst Exponent

**Question:** Explain what the Hurst exponent measures. Why is H < 0.5 required for a mean-reverting process? What are the limitations of the R/S method used in the implementation?

**Answer:**

**What the Hurst exponent measures:**

The Hurst exponent H ∈ (0, 1) characterizes the long-range dependence (or scaling behavior) of a time series. It describes how the range of cumulative deviations scales with the observation window:

$$E[R(n)/S(n)] \propto n^H$$

where R(n) is the range of cumulative deviations from the mean over a window of size n, and S(n) is the standard deviation. The exponent H determines the scaling law.

**Interpretation of H:**

- **H = 0.5:** The series behaves like a random walk (Brownian motion). Increments are uncorrelated. There is no predictable tendency for the series to revert or trend.
- **H < 0.5 (anti-persistent / mean-reverting):** An increase is more likely to be followed by a decrease, and vice versa. The series tends to revert to its mean. The range grows *slower* than √n.
- **H > 0.5 (persistent / trending):** An increase is more likely to be followed by another increase. The series exhibits momentum or trending behavior. The range grows *faster* than √n.

**Why H < 0.5 is required for pair trading:**

The entire strategy relies on mean-reversion: when the spread deviates from μ, it should revert. This is precisely the anti-persistent behavior captured by H < 0.5. If H ≥ 0.5, the spread behaves like a random walk or a trending series, and there is no statistical basis for expecting reversion. Entering a position expecting mean-reversion on a trending series would lead to systematic losses.

For an OU process with parameters (θ, μ, σ), the theoretical Hurst exponent depends on the observation timescale relative to 1/θ. At short timescales (relative to the mean-reversion timescale), the process looks Brownian (H ≈ 0.5). At longer timescales, the mean-reversion becomes apparent and H < 0.5. For the R/S estimator to detect H < 0.5, the sample must span enough mean-reversion cycles.

**Limitations of the R/S method:**

1. **Bias and inefficiency.** The R/S method is one of the oldest Hurst estimators and is known to be biased, especially in small samples. It tends to overestimate H (bias toward 0.5 or above), which means it may fail to detect mean-reversion when it exists. More modern estimators (DFA — Detrended Fluctuation Analysis, or wavelet-based estimators) are more accurate.

2. **Sensitivity to short-range dependence.** The R/S statistic is affected by short-range serial correlation (e.g., AR(1) effects), which can inflate the estimated H. The spread, being the output of a cointegration procedure, may exhibit short-range correlation that biases H upward even if the long-range behavior is mean-reverting.

3. **No confidence intervals.** The `hurst` library's `compute_Hc` function returns a point estimate without standard errors or confidence intervals. There is no way to assess whether H = 0.48 is statistically distinguishable from H = 0.52.

4. **Sensitivity to the `kind` parameter.** The implementation uses `kind='random_walk'` (line 114), which means the input spread is treated as a random walk whose increments are analyzed. If the spread is already stationary (as verified by the previous tests), treating it as a random walk may not be the most appropriate choice. The alternative `kind='change'` would analyze the increments directly.

5. **The `simplified=True` flag.** This uses a simplified R/S computation that may be less robust than the full algorithm.

6. **Redundancy with other tests.** If the spread has already passed ADF, KPSS, and Phillips-Perron stationarity tests, the Hurst exponent provides somewhat redundant information. A stationary series should have H < 0.5 over long timescales. However, it is possible (in theory) for a series to be marginally stationary under ADF but have H close to 0.5, so the Hurst test adds a complementary perspective.

**Key takeaway:** The Hurst exponent provides a non-parametric measure of mean-reversion that complements the parametric stationarity tests. H < 0.5 confirms anti-persistent behavior. However, the R/S estimator used in the implementation is biased, provides no confidence intervals, and is less reliable than modern alternatives like DFA.

---

### Q019 — Multiple Testing Problem

**Question:** Running five sequential tests on each pair creates a multiple-testing issue. If each test has a 5% significance level, what is the approximate probability of incorrectly passing or failing a pair? How would you adjust for this?

**Answer:**

**Two distinct multiple-testing issues:**

There are actually two layers of multiple testing in this pipeline:

**Layer 1 — Multiple tests per pair (5 tests in `test_batterie()`):**

Each of the 5 tests uses a 5% significance level. However, the direction of the concern depends on which error matters:

For the tests where we want to *reject* H₀ (ADF on spread, Engle-Granger, Johansen trace, ADF on differences, Hurst):
- Type I error (false rejection) at each test: 5%.
- A pair must pass *all* of these tests — this is an intersection of rejections.
- The probability of a *genuinely non-cointegrated* pair passing all tests by chance is approximately the *product* of individual false rejection rates (assuming independence): ~0.05^k for k independent tests requiring rejection. This is very small — multiple testing actually *helps* here by making the overall filter more stringent.

For the tests where we want to *fail to reject* H₀ (ADF on raw prices, KPSS on spread):
- We are relying on "failure to reject" as evidence, which is inherently weaker. The probability of failing to reject depends on the test's power, not its significance level.
- If a series is borderline (e.g., near-stationary prices), the ADF test might fail to reject simply due to low power, not because the series is truly I(1).

**The net effect for false positives (accepting a non-cointegrated pair):** Because the pipeline requires passing ALL tests simultaneously, the overall false positive rate is substantially *lower* than 5%. The tests are not independent (they all depend on the same data), but the conservative nature of requiring unanimous agreement makes the pipeline quite strict. This is reflected in the results: from ~40 candidate pairs, only 8 pass.

**Layer 2 — Testing multiple pairs:**

This is the more serious concern. If you test 40 pairs at a 5% per-pair significance level (even after the battery reduces the effective rate), the expected number of false positives across the universe is:

$$E[\text{false positives}] = N \times \alpha_{\text{effective}}$$

Even if α_effective is reduced to, say, 1% by the battery, testing 40 pairs gives E[false positives] ≈ 0.4 — so there is roughly a 33% chance of at least one false positive.

**However**, the economic pre-filter substantially mitigates this. The 40 pairs are not randomly selected from a large universe — they are chosen because they have genuine economic relationships. This means the "null hypothesis" (no cointegration) is less likely to be true for these pairs compared to randomly chosen pairs, so the false discovery rate is lower than the naive calculation suggests.

**How to adjust:**

1. **Bonferroni correction:** Divide the significance level by the number of pairs tested: α_adjusted = 0.05 / 40 = 0.00125. This is very conservative and would likely reject all pairs.

2. **Benjamini-Hochberg (FDR control):** Instead of controlling the family-wise error rate (probability of ANY false positive), control the false discovery rate (expected proportion of false positives among rejections). This is less conservative and more appropriate when you expect some true positives.

3. **Out-of-sample validation as the ultimate filter:** The most practical adjustment is exactly what the project does — use the statistical tests for initial screening, then validate on out-of-sample data. A spuriously cointegrated pair will fail the out-of-sample backtest (as indeed 3 of 4 pairs do). This is the market's own multiple-testing correction.

4. **Bootstrap-based testing:** Instead of relying on asymptotic critical values, generate critical values by bootstrapping under the null hypothesis of no cointegration. This would account for the specific dependence structure in the data.

**Key takeaway:** The sequential battery of 5 tests makes the per-pair false positive rate very low (much less than 5%). The more relevant concern is testing multiple pairs — but the economic pre-filter and out-of-sample validation substantially mitigate this. Formal corrections like Bonferroni or Benjamini-Hochberg could be applied but are rarely used in practice for pair trading screening, where out-of-sample performance serves as the ultimate filter.

---

### Q020 — Johansen det_order and k_ar_diff

**Question:** In `test_coint.py:spread_n_hedge_ratio`, `coint_johansen` is called with `det_order=0` and `k_ar_diff=1`. What do these parameters mean? What happens if you choose `det_order=1` instead? When would a different `k_ar_diff` be appropriate?

**Answer:**

**`det_order` — Deterministic trend specification:**

This parameter controls which deterministic components are included in the VECM (Vector Error Correction Model). The Johansen procedure estimates the model:

$$\Delta Z_t = \Pi Z_{t-1} + \sum_{i=1}^{k} \Gamma_i \Delta Z_{t-i} + \Phi D_t + \varepsilon_t$$

where D_t contains deterministic terms. The `det_order` parameter specifies what goes into D_t:

- **`det_order = -1`:** No deterministic terms at all (no constant, no trend). This assumes the data has zero mean in differences and the cointegrating relationship passes through the origin. Rarely appropriate for financial data.

- **`det_order = 0`:** A constant is included (restricted to the cointegrating relationship). This is the most common choice for financial pairs: it allows the spread to have a non-zero mean (μ ≠ 0) but assumes no deterministic trend in the levels. The constant enters the error correction term as part of α·(β'Z_{t-1} + c).

- **`det_order = 1`:** A constant is included unrestricted (allowing for linear trends in the levels). This is appropriate when the individual series have deterministic trends (e.g., GDP, trending prices) in addition to stochastic trends. The model allows the cointegrating relationship to have a non-zero mean AND the individual series to drift linearly.

**What happens with `det_order=1`:**

For equity prices, which are typically modeled as random walks with drift (not with deterministic linear trends), `det_order=1` would be unnecessarily permissive. It would:
- Include additional parameters (trend coefficients) that absorb degrees of freedom without improving the model.
- Change the asymptotic distribution of the test statistics, which means different critical values apply. The critical values for `det_order=1` are larger (less negative), making it easier to reject the null of no cointegration — potentially increasing false positives.
- The estimated hedge ratio could be affected: allowing for a trend means the cointegrating vector now accounts for differential trends between the two series.

In practice, `det_order=0` is the standard choice for pair trading on equity prices, and the implementation is correct.

**`k_ar_diff` — Number of lagged differences in the VECM:**

This parameter specifies how many lagged first-differences (Γ_i ΔZ_{t-i} terms) are included in the VECM. It controls the short-run dynamics of the model.

- **`k_ar_diff = 1`** (as used in the implementation): includes one lagged difference, ΔZ_{t-1}. This corresponds to a VAR(2) in levels (a VECM with one lag of differences corresponds to a VAR with order k_ar_diff + 1 = 2).

- **Purpose of lagged differences:** They capture short-run autocorrelation in the changes. If the VECM residuals exhibit serial correlation, more lags are needed to whiten them. Too few lags → biased estimates due to omitted dynamics. Too many lags → loss of power and degrees of freedom.

**When a different `k_ar_diff` would be appropriate:**

1. **Information criteria approach:** Estimate the unrestricted VAR at several lag orders (e.g., 1 through 10) and select the order that minimizes AIC or BIC. Then set `k_ar_diff` = selected VAR order − 1.

2. **Residual diagnostics:** Fit the VECM with `k_ar_diff=1`, check the residuals for serial correlation (Ljung-Box test). If significant autocorrelation remains, increase `k_ar_diff`.

3. **Higher-frequency data:** If the data is daily (as here), short-term dynamics may require 2–5 lags to capture weekly effects. For monthly data, `k_ar_diff=1` is often sufficient.

4. **Practical consideration:** With ~3500 daily observations, increasing `k_ar_diff` to 2–5 would not significantly reduce degrees of freedom and might improve the model. The choice of `k_ar_diff=1` is a reasonable default but could be validated by checking the VECM residuals.

**What the implementation does:**

At `test_coint.py:56`:
```python
result = coint_johansen(data, det_order=0, k_ar_diff=1)
```

The Johansen result object `result` contains:
- `result.evec`: eigenvectors (cointegrating vectors). The first column (associated with the largest eigenvalue) is used for the hedge ratio.
- `result.lr1`: trace statistics for each rank hypothesis.
- `result.cvt`: critical values for the trace test.

The trace test at line 107–110 checks whether `lr1[0]` (trace statistic for r=0) exceeds `cvt[0,:][1]` (95% critical value for r=0). If it does, the null of no cointegration (rank = 0) is rejected.

**Key takeaway:** `det_order=0` includes a restricted constant (allowing non-zero spread mean, no linear trend) — correct for equity pairs. `k_ar_diff=1` is a reasonable default for the short-run dynamics, but could be validated with information criteria or residual diagnostics. Both choices directly affect the critical values of the Johansen test and the estimated hedge ratio.

---

## 4. Ornstein-Uhlenbeck Estimation

---

### Q021 — OLS Fit Procedure

**Question:** Walk me through the `fit_ols()` method in `fit_ou_model.py` step by step. What is being regressed on what, and how are the OU parameters recovered?

**Answer:**

The `fit_ols()` method (lines 32–81) estimates the continuous-time OU parameters (θ, μ, σ) from discrete observations of the spread by exploiting the exact AR(1) discretization.

**Step 1 — Set up the regression data (lines 43–48).**
```python
z = np.asarray(z)
n = len(z) - 1
z_lag = z[:-1]     # z[0], z[1], ..., z[n-1]
z_lead = z[1:]     # z[1], z[2], ..., z[n]
```
The input `z` is an array of n+1 spread observations at uniform intervals Δt. Two vectors are created: `z_lag` (today's values) and `z_lead` (tomorrow's values). The regression will model z_lead as a function of z_lag.

**Step 2 — OLS regression (lines 51–53).**
```python
X = np.column_stack([np.ones(n), z_lag])
beta_hat = np.linalg.lstsq(X, z_lead, rcond=None)[0]
b_hat, a_hat = beta_hat[0], beta_hat[1]
```
This regresses z_{i+1} on a constant and z_i:

$$z_{i+1} = \hat{b} + \hat{a} \cdot z_i + \hat{\varepsilon}_i$$

The design matrix X is [1, z_lag] (n × 2). `lstsq` solves the normal equations X'X β = X'y, returning β̂ = (b̂, â). This is the standard OLS estimator for the AR(1) model.

**Step 3 — Compute residual variance (lines 56–57).**
```python
residuals = z_lead - b_hat - a_hat * z_lag
sigma_eps_sq = np.sum(residuals**2) / (n - 2)
```
The residuals ê_i = z_{i+1} − b̂ − â·z_i are computed. The residual variance σ̂²_ε uses the unbiased estimator with denominator n − 2 (there are n observations and 2 estimated parameters: â and b̂).

**Step 4 — Validity check (lines 60–64).**
```python
if a_hat <= 0 or a_hat >= 1:
    raise ValueError(...)
```
For a mean-reverting OU process, the AR(1) coefficient must satisfy a = e^(−θΔt) ∈ (0, 1). If â ≤ 0, the process alternates in sign (non-physical). If â ≥ 1, the process is non-mean-reverting (unit root or explosive). Both cases indicate the OU model is inappropriate for the data.

**Step 5 — Convert to continuous-time OU parameters (lines 67–72).**
```python
self.theta = -np.log(a_hat) / self.dt
self.mu = b_hat / (1 - a_hat)
self.sigma = np.sqrt(
    sigma_eps_sq * (-2 * np.log(a_hat)) /
    (self.dt * (1 - a_hat**2))
)
```
These are the inverse mapping from the exact discretization:
- **θ = −ln(â)/Δt**: Since a = e^(−θΔt), taking logs gives θ = −ln(a)/Δt.
- **μ = b̂/(1 − â)**: Since b = μ(1 − a), solving for μ gives μ = b/(1 − a).
- **σ**: From the discrete variance σ²_ε = σ²(1 − a²)/(2θ), solving for σ² gives σ² = σ²_ε · 2θ/(1 − a²) = σ²_ε · (−2ln(a))/(Δt·(1 − a²)). The implementation computes this correctly.

**Step 6 — Store intermediate quantities (lines 75–79).**
```python
self.a_hat = a_hat
self.b_hat = b_hat
self.sigma_eps = np.sqrt(sigma_eps_sq)
self.residuals = residuals / self.sigma_eps  # standardized residuals
self.n = n
```
The standardized residuals ê_i/σ̂_ε are stored for diagnostic testing. Under the OU model assumptions, these should be i.i.d. N(0, 1).

**Key takeaway:** The procedure is: (1) regress z_{t+1} on [1, z_t] by OLS, (2) verify â ∈ (0, 1), (3) apply the analytical inverse mapping to recover (θ, μ, σ). The entire estimation reduces to a simple linear regression followed by algebraic transformations — no iterative optimization is needed.

---

### Q022 — Validity Check

**Question:** The `fit_ols()` method checks that `0 < a_hat < 1` and raises a `ValueError` if not. Why is this condition necessary? What would `a_hat >= 1` or `a_hat <= 0` imply about the underlying process?

**Answer:**

**Why the condition is necessary:**

The mapping from discrete to continuous parameters requires:
- θ = −ln(â)/Δt. For this to be well-defined and positive (mean-reverting), we need â > 0 (otherwise ln is undefined or complex) and â < 1 (otherwise ln(â) ≥ 0 and θ ≤ 0).

**What â ≥ 1 implies:**

- **â = 1 (exact unit root):** The AR(1) model becomes z_{i+1} = b + z_i + ε_i, which is a random walk with drift b. There is no mean-reversion: θ = −ln(1)/Δt = 0. The half-life is infinite. The process wanders without bound. This is exactly what the ADF test checks for — if the spread is a unit root process, the pair is not cointegrated.

- **â > 1 (explosive):** The process z_{i+1} = b + â·z_i + ε_i amplifies deviations from the equilibrium. θ = −ln(â)/Δt < 0, meaning the drift term pushes the process *away* from μ rather than toward it. The process diverges exponentially. This would be catastrophic for a mean-reversion strategy.

**What â ≤ 0 implies:**

- **â = 0:** z_{i+1} = b + ε_i — the process is pure noise with no memory. θ = +∞, meaning "infinite" mean-reversion speed. While not strictly wrong, it implies the process has zero autocorrelation, which is inconsistent with a spread that should exhibit some persistence.

- **â < 0:** The process oscillates in sign every step: if z_i is above its mean, z_{i+1} tends to be below, and vice versa. This corresponds to θ = −ln(|â|)/Δt + iπ/Δt in the complex domain — the continuous-time model would need negative a, which is not physical for an OU process. In financial terms, a spread that flips sign every day is not the slow mean-reversion that pair trading exploits.

**Typical values in this project:**

For the retained pairs, â is close to 1 but strictly below it. For example, UNH–ELV has θ = 0.0126, so â = e^(−0.0126·1) ≈ 0.9875. This reflects slow mean-reversion: the spread retains ~98.75% of its deviation from the mean each day, gradually reverting over ~55 days (the half-life).

**Edge case concern:** If â is very close to 1 (e.g., â = 0.999), the estimated θ is very small and the half-life is very large. The parameter estimates become increasingly unreliable as â → 1 because the standard errors of the AR(1) coefficient grow, and the OLS estimator becomes biased (see Q027). This is why the project applies a secondary filter on half-life, discarding pairs with t½ > 80 days.

**Key takeaway:** The check 0 < â < 1 ensures the estimated continuous-time process is well-defined and mean-reverting. â ≥ 1 means no reversion (random walk or explosive), â ≤ 0 means non-physical oscillatory behavior. Both cases invalidate the OU modeling assumption.

---

### Q023 — Residual Variance Denominator

**Question:** In `fit_ou_model.py` line 57, the residual variance is computed with denominator `(n - 2)`. Why `n - 2` and not `n` or `n - 1`?

**Answer:**

**The line:**
```python
sigma_eps_sq = np.sum(residuals**2) / (n - 2)
```

**Why n − 2:**

This is the *unbiased* OLS estimator for the error variance in a linear regression with 2 estimated parameters.

The general formula for the unbiased variance estimator in OLS is:

$$\hat{\sigma}^2 = \frac{\text{RSS}}{n - p}$$

where RSS = Σê²_i is the residual sum of squares, n is the number of observations, and p is the number of estimated parameters. The denominator n − p corrects for the degrees of freedom consumed by parameter estimation.

In this regression, z_{i+1} = b + a·z_i + ε_i, there are:
- n observations (pairs (z_i, z_{i+1}) for i = 0, ..., n−1).
- p = 2 estimated parameters (â and b̂).

So the denominator is n − 2.

**Why not n:** The MLE estimator uses denominator n:

$$\hat{\sigma}^2_{\text{MLE}} = \frac{\text{RSS}}{n}$$

This is biased: E[RSS/n] = σ²(n − 2)/n < σ². The bias is (−2/n)σ², which is negligible for large n but technically the estimator underestimates the true variance. The MLE estimator maximizes the likelihood, but the OLS estimator with n − 2 is unbiased.

**Why not n − 1:** The n − 1 denominator (Bessel's correction) applies when estimating the variance of a sample with one estimated parameter (the mean). Here, the regression has two parameters, so one additional degree of freedom is lost.

**Practical impact:** For n ≈ 3500 (the typical sample size in this project), the difference between n, n − 1, and n − 2 is negligible: 3500/3498 ≈ 1.0006. The choice only matters conceptually (bias properties) and for very small samples.

**How this propagates:** σ̂²_ε feeds into the σ estimate via the formula at line 69–72. A slightly different σ̂²_ε (from using n vs n − 2) would produce a slightly different σ̂, which in turn affects the stationary standard deviation σ/√(2θ) and the z-score normalization. For n ≈ 3500, the effect is negligible.

**Key takeaway:** The n − 2 denominator is the standard unbiased OLS variance estimator, correcting for 2 degrees of freedom consumed by estimating â and b̂. For the sample sizes in this project, the distinction from n or n − 1 is immaterial.

---

### Q024 — Sigma Recovery Formula

**Question:** The formula for recovering σ from the discrete residual variance is: `σ² = σ²_ε · (−2 ln(â)) / (Δt · (1 − â²))`. Derive this formula from the exact discrete-time variance of the OU transition density.

**Answer:**

**Starting point:** The exact discrete-time representation of the OU process is:

$$X_{n+1} = a X_n + b + \sigma_\varepsilon \varepsilon_n, \quad \varepsilon_n \sim \mathcal{N}(0,1)$$

where a = e^(−θΔt) and the conditional variance is:

$$\text{Var}[X_{n+1} | X_n] = \sigma_\varepsilon^2 = \frac{\sigma^2}{2\theta}(1 - e^{-2\theta\Delta t}) = \frac{\sigma^2}{2\theta}(1 - a^2)$$

**Derivation of the σ recovery formula:**

Starting from σ²_ε = σ²(1 − a²)/(2θ), solve for σ²:

$$\sigma^2 = \frac{2\theta \cdot \sigma_\varepsilon^2}{1 - a^2}$$

Now substitute θ = −ln(a)/Δt (which follows from a = e^(−θΔt)):

$$\sigma^2 = \frac{2 \cdot (-\ln a / \Delta t) \cdot \sigma_\varepsilon^2}{1 - a^2} = \frac{-2 \ln a \cdot \sigma_\varepsilon^2}{\Delta t \cdot (1 - a^2)}$$

Replacing a with â gives the estimator:

$$\boxed{\hat{\sigma}^2 = \frac{-2 \ln(\hat{a}) \cdot \hat{\sigma}_\varepsilon^2}{\Delta t \cdot (1 - \hat{a}^2)}}$$

**Verification against the code (lines 69–72):**
```python
self.sigma = np.sqrt(
    sigma_eps_sq * (-2 * np.log(a_hat)) /
    (self.dt * (1 - a_hat**2))
)
```
This computes √(σ̂²_ε · (−2·ln(â)) / (Δt·(1 − â²))), which matches the derived formula exactly.

**Why the formula involves −ln(â):** Since â ∈ (0, 1) for a mean-reverting process, ln(â) < 0, so −ln(â) > 0, ensuring σ̂² > 0. The factor −2ln(â) = 2θΔt converts between the continuous-time diffusion coefficient and the discrete-time residual variance.

**Alternative derivation via the variance formula directly:**

Starting from the conditional variance of the transition density derived in Q009:

$$\text{Var}[X(t+\Delta t) | X(t)] = \frac{\sigma^2}{2\theta}(1 - e^{-2\theta\Delta t})$$

The OLS residual variance estimates this conditional variance: σ̂²_ε ≈ σ²(1 − a²)/(2θ). The formula is just the algebraic inversion. There is no approximation involved — the discretization is exact, so the parameter recovery is also exact (up to estimation error in â and σ̂²_ε).

**Key takeaway:** The formula is a straightforward algebraic inversion of the exact discrete-time variance of the OU transition density. It converts the OLS residual variance (a discrete-time quantity) back to the continuous-time diffusion coefficient σ.

---

### Q025 — Confidence Intervals and Delta Method

**Question:** The `confidence_intervals()` method in `fit_ou_model.py` uses the delta method to propagate uncertainty from â to θ. Explain the delta method and assess whether the implementation is correct. What is the standard error formula used for â?

**Answer:**

**The delta method:**

The delta method is a technique for approximating the variance of a function of a random variable. If X̂ is an estimator with E[X̂] ≈ x and Var[X̂] = σ²_X, then for a differentiable function g:

$$\text{Var}[g(\hat{X})] \approx [g'(x)]^2 \cdot \sigma_X^2$$

This is a first-order Taylor expansion: g(X̂) ≈ g(x) + g'(x)(X̂ − x), so Var[g(X̂)] ≈ [g'(x)]² Var[X̂].

**Standard error formula for â (line 106):**
```python
se_a = np.sqrt((1 - self.a_hat**2) / self.n)
```

This uses the formula se(â) = √((1 − a²)/n). This is the *asymptotic* standard error of the OLS estimator of the AR(1) coefficient for a stationary process. It comes from the fact that for a stationary AR(1) with coefficient a, the asymptotic variance of √n(â − a) converges to (1 − a²). Therefore Var[â] ≈ (1 − a²)/n.

**Is this formula correct?** It is approximately correct for stationary AR(1) processes with large n. However, there is a subtlety: the standard OLS standard error for a regression coefficient β̂ is se(β̂) = σ̂_ε / √(Σx²_i) where x_i are the regressor values (centered). For the AR(1) model z_{i+1} = b + a·z_i + ε_i, the exact formula involves the sample variance of z_lag. The asymptotic formula (1 − a²)/n is a simplification that assumes the process has reached its stationary distribution. For n ≈ 3500, this is a good approximation.

**Confidence interval for θ (lines 113–115):**
```python
theta_low = -np.log(a_high) / self.dt
theta_high = -np.log(max(a_low, 1e-10)) / self.dt
```

Since θ = −ln(a)/Δt and g(a) = −ln(a)/Δt is a monotonically *decreasing* function of a, the endpoints are inverted: a_high maps to theta_low and a_low maps to theta_high. The `max(a_low, 1e-10)` prevents taking log of a non-positive number if the confidence interval for a extends below zero.

**Assessment: is this a proper delta method implementation?**

Strictly speaking, the implementation uses a *transformation of the endpoints* rather than the delta method. The delta method would compute:

$$\text{se}(\hat{\theta}) = |g'(\hat{a})| \cdot \text{se}(\hat{a}) = \frac{1}{\hat{a} \cdot \Delta t} \cdot \text{se}(\hat{a})$$

and then construct the CI as θ̂ ± z_crit · se(θ̂).

Instead, the code constructs the CI for a as [â ± z_crit · se(â)] and then applies the nonlinear transformation g to the endpoints. These two approaches give *different* results because g is nonlinear (concave in this case, since g''(a) = 1/(a²Δt) > 0).

The endpoint transformation approach is actually *better* than the delta method here because:
- It respects the monotonicity of the transformation (no need for first-order approximation).
- It produces an asymmetric CI for θ that correctly reflects the nonlinear mapping.
- The delta method would give a symmetric CI for θ, which is a poorer approximation because g(a) = −ln(a) is highly nonlinear near a = 1 (where the pairs in this project lie).

**Confidence interval for μ (lines 118–122):**
```python
se_mu = self.sigma_eps / (
    (1 - self.a_hat) * np.sqrt(self.n * np.var(self.residuals))
)
```

This formula is less standard. Since μ = b/(1 − a), the delta method would propagate uncertainty from both b̂ and â through the joint covariance matrix. The implementation appears to use a simplified formula. Note that `np.var(self.residuals)` operates on the *standardized* residuals (which should have variance ≈ 1), so `self.n * np.var(self.residuals)` ≈ n. The formula simplifies roughly to se(μ) ≈ σ̂_ε / ((1 − â)√n), which is an approximation of the standard error of μ̂ = b̂/(1 − â). The exact formula would require the full covariance matrix of (â, b̂) from the OLS regression.

**Key takeaway:** The confidence interval for θ uses endpoint transformation rather than the delta method, which is actually more accurate for this nonlinear mapping. The standard error of â uses the asymptotic AR(1) formula √((1 − a²)/n). The μ confidence interval uses a simplified approximation. All are reasonable for large n but would be less reliable for small samples.

---

### Q026 — Diagnostic Tests Interpretation

**Question:** The `diagnostic_tests()` method runs Jarque-Bera, Ljung-Box, and ARCH-LM tests. For each test, explain what assumption of the OU model it validates. If the ARCH-LM test rejects, what does this imply about the OU model, and what alternative model would you consider?

**Answer:**

**Jarque-Bera test (line 137):**

- **What it tests:** Normality of the residuals (tests whether skewness = 0 and excess kurtosis = 0 jointly).
- **OU assumption validated:** The OU process is driven by Brownian motion dW(t), which produces Gaussian innovations. If the discretized residuals ε_i are truly from the OU transition density, they should be i.i.d. N(0, σ²_ε).
- **If rejected:** The spread innovations have non-Gaussian features — typically heavy tails (excess kurtosis) or asymmetry (skewness). This means the Brownian motion assumption is violated. The z-score thresholds (which assume Gaussian probabilities for extreme events) are miscalibrated. Events at z = 2 or z = 3 may be more (or less) probable than the Gaussian model predicts.

**Ljung-Box test (line 141):**

- **What it tests:** Autocorrelation in the residuals at lags 1 through 10. H₀: residuals are white noise (no autocorrelation).
- **OU assumption validated:** The exact discretization of the OU process produces AR(1) residuals that should be i.i.d. (serially uncorrelated). If the AR(1) model is correctly specified, the residuals should be white noise.
- **If rejected:** The residuals exhibit serial correlation, meaning the AR(1) model does not fully capture the dynamics. Possible causes: (a) the spread has higher-order autoregressive structure (AR(2)+), (b) the mean-reversion speed θ is not constant, (c) there is a regime change in the sample. The signal generator would produce entries and exits based on stale z-scores, because the current spread depends on more than just the previous value.

**ARCH-LM test (line 146):**

- **What it tests:** Conditional heteroscedasticity (ARCH effects) in the residuals at 5 lags. H₀: residuals are homoscedastic (constant variance). The test regresses squared residuals on their own lags and tests whether the lag coefficients are jointly zero.
- **OU assumption validated:** The OU model assumes constant σ — the diffusion coefficient does not depend on the level of the spread or on time. This translates to constant variance of the AR(1) residuals.
- **If rejected:** The residual variance changes over time — periods of high volatility cluster together (volatility clustering). This is extremely common in financial data.

**What ARCH-LM rejection implies about the OU model:**

If the ARCH-LM test rejects, the constant-σ assumption is violated. The consequences are:

1. **Parameter estimates are still consistent but inefficient.** OLS remains a consistent estimator of â and b̂ even under heteroscedasticity, but the standard errors (and confidence intervals) are wrong. The true uncertainty in θ̂ and μ̂ is underestimated.

2. **The stationary variance σ²/(2θ) is a misleading summary.** If σ is time-varying, the z-score normalization uses a single number (σ_stationary) that may be too small during high-volatility periods and too large during low-volatility periods. This leads to:
   - During high-vol regimes: z-scores are deflated → entries are too infrequent, but when positions are taken, the actual P&L swings are larger than expected.
   - During low-vol regimes: z-scores are inflated → too many false entries on noise.

**Alternative model: OU with stochastic volatility or GARCH-like dynamics.**

The natural extension is to allow σ to vary. Several options:

1. **OU-GARCH:** Model the spread as an OU process but with GARCH(1,1) innovations:
   $$z_{i+1} = b + a \cdot z_i + \sigma_i \varepsilon_i$$
   $$\sigma_i^2 = \omega + \alpha \varepsilon_{i-1}^2 + \beta \sigma_{i-1}^2$$
   The z-score would be normalized by the current conditional volatility σ_i rather than the unconditional σ_stationary.

2. **Exponential OU (for volatility modeling):** The volatility itself follows an OU process: d(ln σ) = κ(ln σ̄ − ln σ)dt + ξ dW₂. This is the continuous-time analogue.

3. **Regime-switching OU:** The parameters (θ, μ, σ) switch between two or more regimes (e.g., high-vol and low-vol) governed by a hidden Markov chain. This captures structural changes in the cointegration relationship.

4. **Practical shortcut:** Use a rolling-window estimate of σ (e.g., 60-day rolling standard deviation of spread changes) to normalize the z-score, without fully specifying a stochastic volatility model. This is simpler to implement and often effective.

**Key takeaway:** Jarque-Bera validates Gaussian noise, Ljung-Box validates white-noise residuals (AR(1) sufficiency), ARCH-LM validates constant volatility. ARCH-LM rejection is the most likely and consequential failure for financial data — it means the z-score normalization is unreliable, and an OU-GARCH or rolling-volatility approach would be more appropriate.

---

### Q027 — Small-Sample Bias

**Question:** OLS estimation of AR(1) parameters is known to be biased in small samples. In which direction is the bias for â? How does this bias affect the estimated θ and half-life? Is this a concern for this project given the sample sizes involved?

**Answer:**

**Direction of bias:**

The OLS estimator of the AR(1) coefficient â is biased *downward* (toward zero) in finite samples. This is a well-known result, established by Marriott and Pope (1954) and Kendall (1954). For an AR(1) process z_{i+1} = b + a·z_i + ε_i with |a| < 1, the bias is approximately:

$$E[\hat{a}] - a \approx -\frac{1 + 3a}{n} + O(n^{-2})$$

For a near unity (as in this project, where â ≈ 0.99), the bias is approximately:

$$\text{Bias} \approx -\frac{4}{n}$$

**How this propagates to θ and half-life:**

Since â is biased downward (too small), and θ = −ln(â)/Δt:
- â too small → ln(â) more negative → θ too large.
- θ̂ overestimates the true θ (mean-reversion speed appears faster than it actually is).
- Half-life t½ = ln(2)/θ: since θ is overestimated, t½ is *underestimated*. The spread appears to revert faster than it actually does.

This is a dangerous direction for a pair trading strategy: it makes the strategy appear more promising than it is. You would:
- Enter trades expecting faster reversion than will actually occur.
- Set holding periods that are too short.
- Underestimate the risk of the spread wandering further before reverting.

**Quantitative assessment for this project:**

For UNH–ELV with â ≈ 0.9875 and n ≈ 3500:

$$\text{Bias} \approx -\frac{1 + 3 \times 0.9875}{3500} \approx -\frac{3.96}{3500} \approx -0.00113$$

So the biased estimate is â ≈ 0.9875 when the true value is approximately a ≈ 0.9886. The resulting bias in θ:

$$\hat{\theta} = -\ln(0.9875) \approx 0.01258$$
$$\theta_{\text{true}} \approx -\ln(0.9886) \approx 0.01145$$

This is about a 10% overestimation of θ, and correspondingly a 10% underestimation of the half-life (estimating 55 days when the true value is ~60 days).

**Is this a concern?**

For n ≈ 3500, the bias is meaningful but not dramatic — roughly a 10% effect on θ. It would be more problematic for:
- Shorter time series (e.g., 1 year of daily data, n ≈ 250: bias ≈ −0.016, which is a large fraction of 1 − a ≈ 0.01).
- Pairs with very slow mean-reversion (a very close to 1), where the bias is a larger fraction of the signal.

**Potential corrections:**

1. **Analytical bias correction:** Subtract the leading-order bias term: â_corrected = â + (1 + 3â)/n. This is simple to implement.
2. **Jackknife or bootstrap bias correction:** Resample the data and estimate the bias numerically.
3. **Exact MLE with bias correction:** Use the exact distribution of the AR(1) OLS estimator (which is known in closed form for Gaussian errors) to construct a bias-corrected estimator.

The project does not implement any bias correction. For the sample sizes involved (~3500), the bias is a secondary concern compared to the bigger issues (parameter drift, regime change, etc.), but it is worth being aware of in an interview context.

**Key takeaway:** OLS underestimates â, which causes θ to be overestimated and the half-life to be underestimated by roughly 10% at n ≈ 3500. This makes the strategy look slightly more attractive than it is. The bias is a known limitation but is small relative to other sources of uncertainty in the project.

---

## 5. Signal Generation and Strategy Logic

---

### Q028 — Z-Score and State Machine

**Question:** Explain how the z-score is computed in the `signal()` method of `Pair_trading_strat.py` and describe the state machine transitions. What do the states {-1, 0, 1} represent?

**Answer:**

**Z-score computation (line 30):**
```python
z_score = (spread - self.mean) / self.std
```

Where:
- `spread` is the current value of the spread S(t) = A(t) − β·B(t).
- `self.mean` = μ from the OU estimation (the long-run mean of the spread).
- `self.std` = σ/√(2θ), the stationary standard deviation of the OU process.

==The z-score measures how many stationary standard deviations the current spread is from its equilibrium==. Under the OU stationary distribution, z ~ N(0, 1). A z-score of +2 means the spread is 2σ_∞ above its mean — a rare event (approximately 2.3% probability in the stationary distribution) that is expected to revert.

**The three states:**

| State | Meaning | Position |
|-------|---------|----------|
| 0 | Flat | No position. Waiting for an entry signal. |
| +1 | Long spread | Long A, short B. Profitable if spread increases toward μ (from below). |
| −1 | Short spread | Short A, long B. Profitable if spread decreases toward μ (from above). |

**State machine transitions:**

**From state 0 (flat):**
- If z > k_entry (default 2.0): spread is far above mean → expect it to fall → **short the spread** (state → −1).
- If z < −k_entry: spread is far below mean → expect it to rise → **long the spread** (state → +1).
- Otherwise: remain flat (state stays 0).

**From state +1 (long spread):**
- If z > −k_exit (default −0.2): the spread has reverted up toward the mean → **take profit** (state → 0). Note: the long was entered when z < −k_entry, so z rising from below −k_entry to above −k_exit indicates reversion.
- If z < −stop_loss (default −3.0): spread has moved further against the position → **stop loss** (state → 0).
- If holding time exceeds max_holding (if set): **time stop** (state → 0).
- Otherwise: remain long (state stays +1).

**From state −1 (short spread):**
- If z < k_exit (default 0.2): spread has reverted down toward the mean → **take profit** (state → 0).
- If z > stop_loss (default 3.0): spread has moved further against the position → **stop loss** (state → 0).
- If holding time exceeds max_holding: **time stop** (state → 0).
- Otherwise: remain short (state stays −1).

**Key properties of the state machine:**
1. **Entry only from flat:** You cannot go directly from long to short or vice versa. You must close the current position first (return to flat), then potentially open a new one on the next time step.
2. **No re-entry within same deviation:** Once a position is closed (take-profit or stop-loss), the state returns to 0. A new entry requires the z-score to reach ±k_entry again.
3. **The machine is deterministic:** Given the current state and z-score, the next state is uniquely determined. No randomness beyond the spread itself.

**Key takeaway:** The z-score normalizes the spread by the OU stationary distribution. The state machine implements a disciplined entry/exit framework: enter at extreme z-scores (±2σ_∞), exit when the spread reverts near the mean (±0.2σ_∞), and cut losses if reversion fails (±3σ_∞).

---

### Q029 — Entry and Exit Asymmetry

**Question:** The default parameters are k_entry=2 and k_exit=0.2. Why is the exit threshold so much smaller than the entry threshold? What is the financial intuition behind this asymmetry?

**Answer:**

**Financial intuition:**

The asymmetry reflects the core mechanics of mean-reversion trading:

**Entry at z = ±2 (far from mean):** You want to enter only when the spread is significantly dislocated from equilibrium. A z-score of ±2 means the spread is 2 stationary standard deviations from the mean — a rare event under the stationary distribution (roughly 2.3% probability in each tail). Entering at this level provides:
- A high probability that the spread will revert (the OU model says the drift is strongly toward μ at this displacement).
- Sufficient distance to the exit target to generate meaningful profit.
- A safety margin against noise — small fluctuations don't trigger entries.

**Exit at z = ±0.2 (near the mean):** You want to exit when the spread has *nearly* reverted to its mean, capturing most of the mean-reversion move. The exit threshold is deliberately set close to zero (the mean) but not exactly at zero. The reasons for the small but non-zero exit threshold:

1. **Capture the bulk of the move.** If you enter at z = −2 (long spread) and exit at z = −0.2, you capture 1.8 standard deviations of spread movement. Waiting for z = 0 exactly would mean waiting for the spread to cross the mean, which (a) takes longer and (b) involves the spread oscillating around μ, adding noise to the exit timing.

2. **Avoid the "last mile" problem.** Near the mean, the OU drift is weak (θ(μ − X) ≈ 0 when X ≈ μ). The process spends a lot of time meandering near μ with no strong directional pull. Waiting for z = 0 means holding a position through a period of low expected return but non-zero risk.

3. **Transaction cost consideration.** Every extra day holding a position without significant expected movement is wasted capital. A tighter exit (closer to 0) captures more of the theoretical profit but extends the holding period and exposure to regime risk.

**Why not exit at exactly 0?** The z-score crosses zero with probability 1 (the OU process is recurrent), but the time to cross zero has high variance. Setting k_exit = 0.2 provides a slightly earlier exit that sacrifices ~10% of the theoretical profit (0.2 out of 2.0 standard deviations) but significantly reduces average holding time and exposure to tail risks.

**Trade-off formulation:** The k_entry/k_exit combination creates a "profit capture band" of width k_entry − k_exit = 1.8σ_∞. A wider band (higher k_entry, lower k_exit) captures more per trade but generates fewer entry signals (fewer trades). A narrower band generates more signals but smaller profit per trade, with higher transaction costs eroding the edge.

**Key takeaway:** k_entry = 2 requires a significant dislocation before entering (high conviction), while k_exit = 0.2 captures nearly the full reversion but avoids the diminishing-returns region near the mean. The 10:1 ratio reflects the fact that entry decisions need high confidence while exit decisions should capture the profit quickly.

---

### Q030 — Stop-Loss Role

**Question:** Why is a stop-loss mechanism included in a mean-reversion strategy? Under what scenario would the stop-loss trigger, and what does it imply about the underlying cointegration relationship?

**Answer:**

**Why a stop-loss in a mean-reversion strategy:**

This might seem paradoxical: if the spread is mean-reverting, shouldn't a larger deviation from the mean be *more* likely to revert? Under the OU model, yes — the drift θ(μ − X) is stronger at larger deviations. Entering at z = ±2 and seeing z reach ±3 should, under the model, predict an even stronger reversion.

The stop-loss exists because **the OU model might be wrong.** Specifically:

1. **Structural break in the cointegration relationship.** The economic link between the two assets may break permanently (merger, bankruptcy, regulatory change, sector disruption). When this happens, the spread is no longer mean-reverting — it becomes a random walk or trends in one direction. Without a stop-loss, the strategy would hold a losing position indefinitely, waiting for a reversion that never comes.

2. **Parameter drift.** Even without a sudden break, the OU parameters (especially μ and β) may have shifted. If the true μ is now 5σ above the estimated μ, the strategy sees z = −3 and believes the spread will revert upward, but in reality the spread is near its new equilibrium.

3. **Model specification error.** The OU model has thin Gaussian tails. Real spreads may have fat tails, meaning z = 3 events are more common than the Gaussian model predicts and may represent genuine regime changes rather than extreme mean-reversion opportunities.

**When the stop-loss triggers:**

The stop-loss triggers when |z| > stop_loss = 3.0 while a position is active. For example:
- A long spread position was entered at z = −2 (spread below mean).
- The spread moves further down, z drops to −3.1.
- The stop-loss fires, closing the position at a loss.

The loss on this trade is approximately (−3.0 − (−2.0)) × σ_∞ = −1.0σ_∞ of spread movement (ignoring the exact dynamics).

**What it implies about the cointegration relationship:**

A stop-loss trigger is a strong signal that something may have changed:
- The spread has moved 3σ_∞ from the estimated mean — a 0.13% event under the stationary Gaussian distribution.
- While such events can occur in a true OU process, their frequency provides diagnostic information. If stop-losses trigger often, it suggests the OU model is poorly calibrated or the cointegration has weakened.

**Trade-off:** Setting stop_loss too tight (e.g., 2.5) causes frequent exits during normal OU fluctuations, turning profitable mean-reversion trades into realized losses. Setting it too loose (e.g., 5.0) provides almost no protection against structural breaks. The default of 3.0 is a compromise: under the OU model, z = 3 occurs rarely enough (~0.3% of stationary time) that triggering it is informative, but it still limits the maximum loss per trade to approximately (stop_loss − k_entry) × σ_∞ = 1.0σ_∞.

**Key takeaway:** The stop-loss protects against model failure, not against normal spread behavior. Under a true OU process, it would rarely trigger. Its primary role is limiting catastrophic losses when the cointegration relationship breaks down — an event the OU model cannot predict by construction.

---

### Q031 — Exit Condition Sign Convention

**Question:** In `Pair_trading_strat.py`, lines 43–44, the exit condition for a long spread position is `z_score > -self.k_exit`. Explain why the negative sign is present. What would happen if the condition were `z_score > self.k_exit` instead?

**Answer:**

**Why the negative sign:**

A long spread position (state = +1) is entered when z < −k_entry, meaning the spread is far *below* the mean. The position profits as the spread rises back toward μ (z increases toward 0).

The take-profit condition should trigger when the spread has reverted close enough to the mean. With the convention that the long position was entered below the mean (z negative), the z-score needs to increase from a large negative value (z ≈ −2) back toward zero. The exit target should be just below zero, on the negative side — hence −k_exit.

**Tracing through the logic:**

1. Entry: z < −k_entry = −2.0. Example: z = −2.3. State → +1.
2. Spread reverts upward. z increases: −2.3 → −1.5 → −0.8 → −0.1.
3. Exit check: `z_score > -self.k_exit` → z > −0.2. When z = −0.1, the condition is satisfied (−0.1 > −0.2). State → 0. Take profit.

The exit occurs when z crosses −0.2 from below — just slightly below the mean. This captures the bulk of the reversion (from z ≈ −2 to z ≈ −0.2 = 1.8σ_∞ of movement).

**What would happen with `z_score > self.k_exit` (no negative sign):**

The exit condition would be z > +0.2. This means the long position would NOT be closed until the spread has crossed the mean AND moved 0.2σ_∞ *above* it.

Consequences:
- **Longer holding periods.** The spread must not only revert to the mean but overshoot it by 0.2σ_∞. Under the OU model, the spread oscillates around μ, so this overshoot will eventually happen, but it takes longer.
- **Higher theoretical profit per trade** (capturing ~2.2σ_∞ instead of ~1.8σ_∞).
- **Higher risk.** While waiting for the overshoot, the spread might reverse again, or the cointegration may weaken. The longer you hold, the more exposed you are to regime change.
- **Asymmetry with the short side.** For state = −1 (short spread), the exit is `z < k_exit = +0.2` (line 52). If the long exit were changed to `z > +0.2`, both sides would exit when z crosses +0.2, creating a directional bias (both long and short exit on the same side of the mean).

**Symmetry of the current implementation:**
- Long (state +1): entered at z < −2, exited at z > −0.2 (spread below mean, exiting near mean from below).
- Short (state −1): entered at z > +2, exited at z < +0.2 (spread above mean, exiting near mean from above).

Both sides exit at 0.2σ_∞ from the mean, on the side where the position was entered. This is symmetric and correct.

**Key takeaway:** The negative sign in `z > -k_exit` ensures the long position exits just below the mean (on the same side where it was entered), capturing the reversion without requiring an overshoot. It maintains symmetry with the short side's exit condition `z < +k_exit`.

---

### Q032 — Transaction Cost Bug

**Question:** In `Pair_trading_strat.py`, line 86, the transaction costs are computed as:
`costs = np.abs(trades[:1]) * self.tc * np.abs(spread[1:-1])`
Identify the bug in this line. What is the actual effect on the backtest results?

**Answer:**

**The bug:**

The expression `trades[:1]` takes a *slice* of the first element only — it returns an array of length 1 containing only `trades[0]`. The intended expression is almost certainly `trades[1:]` (all elements starting from the second) or simply `trades` (all elements).

Let's trace the dimensions:
- `positions` has length n (same as `spread`).
- `trades = np.diff(positions)` has length n − 1.
- `returns_spread = np.diff(spread)` has length n − 1.
- `pnl_gross = pos_for_returns * returns_spread` has length n − 1.

The cost array should have length n − 2 to match `pnl_net[1:]` (which subtracts costs from PnL starting at index 1):
```python
pnl_net = pnl_gross.copy()
pnl_net[1:] -= costs
```

So `costs` needs length n − 2. Let's check what the current code produces:
- `trades[:1]` has length 1.
- `spread[1:-1]` has length n − 2.
- Broadcasting: `np.abs(trades[:1]) * self.tc * np.abs(spread[1:-1])` → the scalar `trades[0]` is broadcast across all n − 2 elements.

**The result:** The cost array is `|trades[0]| * tc * |spread[1:-1]|` — it applies the magnitude of the *first trade only* as a multiplier to every element. If the first trade is 0 (no position change at time 0), then ALL costs are zero. If the first trade is ±1 or ±2, then costs are applied everywhere regardless of whether a trade actually occurred at that time step.

**What was likely intended:**

```python
costs = np.abs(trades[1:]) * self.tc * np.abs(spread[1:-1])
```

This would apply costs proportional to the absolute position change at each time step (|trades[i]| is 0 when no trade occurs, 1 for a simple entry/exit, and 2 for a flip from long to short or vice versa), multiplied by the transaction cost rate and the absolute spread value.

**Actual effect on backtest results:**

In the most likely scenario (the first signal is 0 = flat, because the initial z-score is probably inside the ±2 band):
- `trades[0] = positions[1] - positions[0]`. If both are 0 (no immediate entry), then `trades[0] = 0`.
- `costs = 0 * tc * |spread[1:-1]| = array of zeros`.
- **All transaction costs are zero.** The backtest effectively ignores transaction costs entirely.

This makes the backtest results unrealistically optimistic. With the default 30 bps cost and potentially dozens of trades, the actual transaction costs could meaningfully reduce profitability — especially for pairs where the profit margin per trade is small.

Even in the unlikely case where the first signal is non-zero (immediate entry), the costs would be applied to every time step regardless of whether a trade occurred, which is equally wrong (over-charging costs during holding periods).

**Key takeaway:** `trades[:1]` is a slicing bug — it should be `trades[1:]` or `trades`. In practice, it likely zeroes out all transaction costs, making the backtest results overly optimistic. This is one of the most consequential bugs in the codebase.

---

### Q033 — Spread-Level PnL Interpretation

**Question:** The `backtest()` method computes PnL as `positions[:-1] * np.diff(spread)`. What are the units of this PnL? How does it relate to actual dollar profit? Is this a realistic measure of strategy performance?

**Answer:**

**What the computation does (lines 78–82):**
```python
returns_spread = np.diff(spread)          # spread[t+1] - spread[t]
pos_for_returns = positions[:-1]           # position at start of period
pnl_gross = pos_for_returns * returns_spread
```

For each time step, the PnL is: position × (change in spread). If you're long the spread (position = +1) and the spread increases by Δ, you earn +Δ. If you're short (position = −1) and the spread decreases by Δ, you earn +|Δ|.

**Units of this PnL:**

The spread is S(t) = A(t) − β·B(t), where A(t) and B(t) are in dollars (price per share). So the spread is in dollar units (specifically, dollars per "unit of spread"). The daily PnL `position × ΔS` is also in dollars.

However, this is the PnL *per unit of spread traded*. It represents the profit from holding exactly 1 share of A and shorting exactly β shares of B. The PnL does not account for the capital required to put on the position — it is an absolute dollar P&L per spread unit, not a return.

**How it relates to actual dollar profit:**

To convert to actual dollar profit, you need to know:
1. **How many units of the spread you hold.** If you buy N_A shares of A and short N_B = β·N_A shares of B, your total PnL is N_A × ΔS. The `backtest()` method implicitly assumes N_A = 1.
2. **The capital required.** Going long 1 share of A costs A(t) dollars. Shorting β shares of B requires margin. The total capital deployed is approximately A(t) + β·B(t) (ignoring margin benefits). The *return* on this capital is ΔS / (A(t) + β·B(t)).

**Is this a realistic measure of strategy performance?**

It has significant limitations:

1. **No position sizing.** The PnL assumes a fixed 1-unit position regardless of the spread level, the capital available, or the signal strength. In reality, as prices change, maintaining 1 unit of spread requires different dollar amounts.

2. **No compounding.** The cumulative PnL is a simple sum (np.cumsum), not a compounded return. A strategy that makes $10 on a $100 spread is equivalent to one that makes $10 on a $1000 spread, but the latter uses 10× more capital.

3. **Sharpe ratio interpretation.** The Sharpe ratio computed on these PnL numbers (line 98–99) is not a standard return-based Sharpe. It is in units of dollars/(dollars·√year), which is not directly comparable to standard Sharpe ratios quoted on returns. To be comparable, you'd need to normalize by the capital deployed.

4. **Not comparable across pairs.** Different pairs have different spread levels and different β values. A PnL of +$50 on UNH–ELV (where the spread might be ~$100–$200) means something very different from +$50 on SNPS–CDNS (where the spread might be $20–$50).

5. **The `simulate_capital()` method addresses some of these issues** by tracking actual share quantities, capital, and mark-to-market portfolio value. This provides a more realistic picture of the strategy's performance.

**When spread-level PnL is useful:** Despite its limitations, this measure is useful for:
- Comparing entry/exit parameters on the *same* pair (same spread scale).
- Verifying that the signal logic produces sensible results before adding the complexity of capital allocation.
- Quick prototyping and debugging.

**Key takeaway:** The spread-level PnL measures dollar profit per unit of spread traded. It is useful for internal comparisons but not a realistic measure of strategy performance because it ignores position sizing, capital requirements, and compounding. The capital simulation method `simulate_capital()` provides a more realistic alternative.

---

## 6. Capital Simulation

---

### Q034 — Variable Scoping Bug

**Question:** In `Pair_trading_strat.py`, the `simulate_capital()` method references variable `t` in lines 153–154 (inside the `if op == 1` block at the first time step), but `t` is only defined as the loop variable starting at line 168. What happens when this code executes? Under what conditions would this bug trigger?

**Answer:**

**The problematic code (lines 148–166):**
```python
# premier cran :
spread = prixA[0] - hedge*prixB[0]
op, entry_day = self.signal(spread, 0, 0, 0)
ops.append((op, entry_day))

if op == 1:
    n_A = f*liquidité/prixA[t]      # ← t is not defined
    n_B = hedge*f*liquidité / prixB[t]  # ← t is not defined
    ...
elif op == -1:
    n_A = f*liquidité/prixA[t]      # ← t is not defined
    n_B = hedge*f*liquidité / prixB[t]  # ← t is not defined
    ...
```

The variable `t` is the loop variable from `for t in range(1, n)` at line 168. At the time the first-step code executes (before the loop), `t` has not been assigned.

**What happens at runtime:**

In Python, referencing an undefined local variable raises a `NameError: name 't' is not defined`. The code would crash immediately.

**Under what conditions does this bug trigger?**

The bug triggers only if `op != 0` at the first time step — i.e., if the very first spread value produces an entry signal. This requires the initial z-score to be outside the ±k_entry band:

$$|z_0| = \frac{|S(0) - \mu|}{\sigma_\infty} > k_{\text{entry}} = 2$$

In practice, for most pairs, the out-of-sample spread starts near its historical mean, so z₀ is likely within ±2 and `op = 0`. The first-step code falls through to `cumulative_capital[0] = patrimoine = capital`, which is correct.

**However**, this is a latent bug: it depends entirely on the initial spread value. If the spread happens to start in an extreme position (e.g., after a market event between the end of in-sample and the start of out-of-sample), the method would crash. The notebook happens to avoid it because the initial z-score for UNH–ELV is within the entry band.

**The intended code should use index 0 instead of `t`:**
```python
if op == 1:
    n_A = f*liquidité/prixA[0]
    n_B = hedge*f*liquidité / prixB[0]
```

**Additional issue in the first-step logic:** Even if `t` were replaced by `0`, the liquidity update formulas on lines 156–157 and 163–164 have questionable accounting (see Q035 for analysis). The first-step code is essentially duplicated from the loop body but with the scoping error, suggesting it was written separately rather than factored.

**Key takeaway:** `t` is referenced before it is defined as a loop variable. The bug causes a `NameError` crash whenever the first spread observation triggers an entry signal. It is latent for the pairs tested in the notebook (initial z-score is within ±2) but would surface for different data or parameters.

---

### Q035 — Long Spread Mechanics

**Question:** When the strategy goes long the spread (buy A, short B), explain line by line how the capital allocation works in `simulate_capital()`. Specifically, explain what `n_A`, `n_B`, and the liquidity update represent.

**Answer:**

**The entry block for long spread (lines 173–180):**
```python
if op == 1:  # long spread: buy A, short B
    if ops[t-1][0] != 1:  # this is the entry day (wasn't long yesterday)
        n_A = f*liquidité/prixA[t]
        n_B = hedge*f*liquidité / prixB[t]

        liquidité = liquidité - f*liquidité + n_B * prixB[t]
        patrimoine = liquidité + n_A * prixA[t] - n_B * prixB[t]
```

**Line by line:**

**`n_A = f*liquidité/prixA[t]`** — Number of shares of A to buy. The strategy allocates f × liquidité dollars to the long leg. Dividing by prixA[t] converts to shares. For example, if f = 0.5, liquidité = $10,000, prixA = $500: n_A = 0.5 × 10,000 / 500 = 10 shares.

**`n_B = hedge*f*liquidité / prixB[t]`** — Number of shares of B to short sell. The short leg is scaled by the hedge ratio β. This allocates β × f × liquidité dollars to the short side. For hedge = 1.2, f = 0.5, liquidité = $10,000, prixB = $100: n_B = 1.2 × 0.5 × 10,000 / 100 = 60 shares.

**`liquidité = liquidité - f*liquidité + n_B * prixB[t]`** — Update available cash after the trade.
- `liquidité - f*liquidité`: subtract the cash spent buying A (f × liquidité dollars).
- `+ n_B * prixB[t]`: add the cash received from short selling B. When you short sell n_B shares at price prixB[t], you receive n_B × prixB[t] in cash.
- Substituting: n_B × prixB[t] = hedge × f × liquidité. So: liquidité_new = liquidité(1 − f) + hedge × f × liquidité = liquidité(1 − f + hedge·f) = liquidité(1 + f(hedge − 1)).

**`patrimoine = liquidité + n_A * prixA[t] - n_B * prixB[t]`** — Total portfolio value (mark-to-market).
- `liquidité`: cash on hand.
- `+ n_A * prixA[t]`: market value of the long position in A.
- `- n_B * prixB[t]`: liability from the short position in B (you owe n_B shares, currently worth n_B × prixB[t]).

On the entry day, substituting back: patrimoine = liquidité_new + f × liquidité − hedge × f × liquidité. The short proceeds cancel with the short liability, and the A purchase cost cancels with the A value. So patrimoine = liquidité (unchanged from before the trade). This is correct — entering a self-financing position doesn't change total wealth, only the composition.

**The holding block (lines 181–183):**
```python
else:  # already long, not entry day
    patrimoine = liquidité + n_A*prixA[t] - n_B*prixB[t]
```

Liquidity doesn't change (no new trades). Only patrimoine is updated to reflect current market prices. If A rises or B falls, the patrimoine increases (the long spread position profits). If A falls or B rises, patrimoine decreases.

**The closing block (lines 196–199):**
```python
if op == 0:
    if ops[t-1][0] == 1:  # closing a long spread
        liquidité = liquidité + n_A*prixA[t] - n_B*prixB[t]
        patrimoine = liquidité  # fully liquid
```
- `+ n_A*prixA[t]`: sell n_A shares of A at current price (cash inflow).
- `- n_B*prixB[t]`: buy back n_B shares of B to cover the short (cash outflow).
- After closing, patrimoine = liquidité (fully in cash).

**Key observations:**

1. **The position is not dollar-neutral.** The long leg uses f × liquidité and the short leg uses hedge × f × liquidité. If hedge ≠ 1, the dollar exposure is asymmetric. Dollar-neutrality would require the same dollar amount on both legs.
2. **The position IS spread-neutral by construction:** you hold 1 unit of the spread (n_A shares of A minus β equivalent shares of B), scaled by f × liquidité.
3. **No margin requirements are modeled.** Short selling requires margin deposits (typically 50–150% of the short position value). The simulation assumes you can short freely with no margin haircut.
4. **Transaction costs (`self.tc`) are not applied.** Unlike `backtest()`, this method never deducts transaction costs.

**Key takeaway:** The capital allocation buys f × liquidité worth of A and shorts hedge × f × liquidité worth of B. The position is self-financing on entry (patrimoine unchanged), profits from spread convergence during holding, and returns to full cash on exit. The main simplifications are no margin modeling and no transaction costs.

---

### Q036 — Risk Fraction f=0.5

**Question:** The notebook backtests with `f=0.5` (50% risk per trade). Is this a reasonable risk fraction for a pair trading strategy? What does a Kelly criterion analysis suggest about optimal sizing for an OU-based strategy?

**Answer:**

**Is f = 0.5 reasonable?**

No — f = 0.5 is extremely aggressive. Allocating 50% of available capital to a single trade means:
- Two simultaneous losing trades can wipe out the entire account.
- A single trade experiencing a stop-loss (at z = 3, i.e., 1σ_∞ beyond entry) would lose approximately 50% × (1σ_∞ / entry_spread_level) of capital — potentially 10–25% of total capital in one trade.
- There is no diversification: the portfolio is fully concentrated in a single pair's risk during active periods.

Typical risk fractions in professional pair trading are 2–10% of capital per trade, depending on the strategy's Sharpe ratio and the trader's risk tolerance. The 50% used in the notebook is likely chosen for demonstration purposes (to make the P&L curves more visually dramatic) rather than as a realistic allocation.

**Kelly criterion analysis:**

The Kelly criterion determines the fraction of capital to bet to maximize the long-run growth rate of wealth. For a strategy with discrete outcomes:

$$f^* = \frac{p}{l} - \frac{q}{g}$$

where p = probability of winning, q = 1 − p, g = gain per dollar risked (win), l = loss per dollar risked (loss).

For a continuous-distribution strategy (more appropriate for OU-based trading), the Kelly fraction is:

$$f^* = \frac{\mu_r}{\sigma_r^2}$$

where μ_r is the expected return per trade and σ²_r is the variance of returns per trade.

**Estimating Kelly for an OU strategy:**

For a mean-reversion trade with entry at z = k_entry and exit at z = k_exit:
- Expected profit per trade (if reversion occurs): approximately (k_entry − k_exit) × σ_∞ = 1.8σ_∞ in spread units.
- Expected loss per trade (if stop-loss triggers): approximately (stop_loss − k_entry) × σ_∞ = 1.0σ_∞.
- The probability of profit vs stop-loss depends on the OU dynamics and can be computed via the first-passage-time distribution of the OU process.

For a well-calibrated OU pair with realistic parameters (half-life ~50 days, σ_∞ reasonable), typical estimates suggest:
- Win rate: 60–70% (mean-reversion makes profit more likely than stop-loss).
- Average win/loss ratio: ~1.8 (favorable due to the asymmetric distance to take-profit vs stop-loss).
- Kelly fraction: typically f* ≈ 15–30% of capital.

**However**, the Kelly fraction is notoriously sensitive to estimation error. The standard practice is to use a fraction of Kelly (e.g., half-Kelly or quarter-Kelly) to account for:
- Parameter uncertainty (θ, μ, σ are estimates, not known values).
- Fat tails in actual returns (the OU model underestimates extreme events).
- Regime change risk (the model may be wrong during the trade).
- Correlation between trades (successive trades on the same pair are not independent).

A reasonable practical range for this strategy would be f ≈ 5–15%, which is 0.25–0.5× the theoretical Kelly. The default parameter `f=0.05` in the method signature is much more sensible than the `f=0.5` used in the notebook.

**Key takeaway:** f = 0.5 is far too aggressive for any production strategy. The Kelly criterion for a typical OU pair trade suggests f* ≈ 15–30%, and risk management best practices recommend using half-Kelly or less, yielding f ≈ 5–15%. The default `f=0.05` in the code is actually a reasonable starting point.

---

### Q037 — Mark-to-Market Accounting

**Question:** In the `simulate_capital()` method, when a long spread position is held (lines 181–183), the patrimoine is updated as `liquidité + n_A*prixA[t] - n_B*prixB[t]`. Explain why the short position in B appears as a subtraction. What implicit assumptions are made about short selling?

**Answer:**

**Why the subtraction:**

The patrimoine (portfolio value) represents the net asset value if all positions were liquidated immediately at current prices.

When you short sell n_B shares of B:
1. At entry: you borrow n_B shares from a broker and sell them on the market, receiving n_B × prixB[entry] in cash. This cash is reflected in the `liquidité` variable.
2. At any point during the holding period: you *owe* n_B shares to the broker. To close the position, you must buy back n_B shares at the current price prixB[t]. This is a *liability*.

Therefore:
- `liquidité`: includes the cash from the short sale proceeds.
- `+ n_A * prixA[t]`: the market value of the long position (an asset).
- `- n_B * prixB[t]`: the cost of covering the short position at current prices (a liability).

The formula patrimoine = assets − liabilities + cash, which is the standard accounting identity:

$$\text{patrimoine} = \underbrace{\text{liquidité}}_{\text{cash}} + \underbrace{n_A \cdot P_A(t)}_{\text{long asset value}} - \underbrace{n_B \cdot P_B(t)}_{\text{short liability}}$$

**How it generates profit from mean-reversion:**

If the spread S = A − β·B decreases toward μ (from above, in a short spread trade) or increases toward μ (from below, in a long spread trade), the position profits. For the long spread case:
- Profit if A rises: n_A × ΔP_A > 0 (long asset appreciates).
- Profit if B falls: −n_B × ΔP_B > 0 when ΔP_B < 0 (liability shrinks).
- Both contribute when the spread increases.

**Implicit assumptions about short selling:**

1. **Unlimited borrowing of shares.** The simulation assumes you can always borrow n_B shares of B to sell short. In practice, some stocks are hard to borrow (high short interest, small float), and the broker may recall the loan.

2. **No borrowing cost.** Short selling incurs a borrow fee (the "short rebate" rate), typically 0.25–3% annualized for liquid stocks but potentially 10–50%+ for hard-to-borrow stocks. The simulation ignores this entirely. Over a 55-day holding period with a 1% annualized borrow cost, this adds ~0.15% of the short position value — small but not negligible.

3. **No margin requirements.** In reality, the broker requires margin (typically 50% initial margin for equities under Reg T, and 25–30% maintenance margin). If the short position moves against you (B rises), you may face a margin call requiring additional cash. The simulation does not model this constraint.

4. **No uptick rule or short-sale restrictions.** Some markets have restrictions on when short sales can be executed (e.g., the alternative uptick rule in the US). The simulation assumes shorts can be placed at any time.

5. **Execution at the close price.** The simulation uses daily close prices, assuming you can execute at exactly that price. In practice, short sales may face wider spreads or partial fills.

**Key takeaway:** The short position appears as a subtraction because it is a liability — you must eventually buy back the shares at the current market price. The simulation assumes frictionless short selling (no borrow costs, no margin, unlimited availability), which overstates the profitability of the strategy.

---

### Q038 — Missing Transaction Costs

**Question:** The `simulate_capital()` method does not apply the `self.tc` transaction costs. Why is this a problem for comparing results between the two backtest modes? How would you add transaction costs to this method?

**Answer:**

**The problem:**

The `Strategie` class stores `self.tc = transaction_cost_bps / 10000` (default: 30 bps = 0.003), but `simulate_capital()` never uses it. Meanwhile, `backtest()` attempts to apply transaction costs (albeit with the `trades[:1]` bug discussed in Q032). This means:

1. **The two methods are not comparable.** Even if both methods were bug-free, `backtest()` would show lower P&L (after costs) while `simulate_capital()` would show the gross P&L. A user comparing the two might incorrectly attribute the difference to position sizing effects when it is actually due to inconsistent cost modeling.

2. **Overstated profitability.** The capital simulation is the more "realistic" of the two methods (explicit shares, capital tracking). Omitting transaction costs from it defeats the purpose of realism. For a pair trading strategy with dozens of round trips, 30 bps per trade can significantly erode profits.

**Quantitative impact:**

Each trade has two legs: buy/sell A and sell/buy B. The transaction cost for a round trip (entry + exit) at 30 bps per leg is:

$$\text{Cost per round trip} \approx 2 \times 0.003 \times (n_A \times P_A + n_B \times P_B)$$

If n_A × P_A ≈ f × liquidité and n_B × P_B ≈ hedge × f × liquidité, the cost per round trip is approximately 2 × 0.003 × (1 + hedge) × f × liquidité. For f = 0.5, hedge ≈ 1.0, liquidité = $10,000: cost ≈ 2 × 0.003 × 2 × 5,000 = $60 per round trip. Over 10–20 round trips, this is $600–$1,200, which is 6–12% of the initial capital — very material.

**How to add transaction costs:**

Transaction costs should be deducted from liquidity at each trade (entry and exit). The natural place is wherever `n_A` and `n_B` are computed (entry) or wherever positions are closed (exit):

**At entry (long spread example, after line 179):**
```python
# After computing n_A, n_B and updating liquidité:
cost_entry = self.tc * (n_A * prixA[t] + n_B * prixB[t])
liquidité -= cost_entry
patrimoine -= cost_entry
```

**At exit (closing long spread, after line 198):**
```python
# After updating liquidité from closing:
cost_exit = self.tc * (n_A * prixA[t] + n_B * prixB[t])
liquidité -= cost_exit
patrimoine = liquidité  # position closed, patrimoine = cash
```

The same logic applies symmetrically for short spread entry and exit.

**Alternative: proportional bid-ask spread model.** Instead of a flat bps cost on notional, model the cost as half the bid-ask spread times the number of shares: cost = 0.5 × spread_ba × (n_A + n_B). This is more realistic for equity markets but requires bid-ask spread data.

**Key takeaway:** The missing transaction costs in `simulate_capital()` make its results unrealistically optimistic and non-comparable with `backtest()`. Costs should be deducted from liquidity at each entry and exit, proportional to the notional of both legs.

---

## 7. Backtest Methodology and Results

---

### Q039 — Sharpe Ratio Computation

**Question:** The Sharpe ratio in `Pair_trading_strat.py` line 98–99 is computed only on active days. Is this the correct approach? What bias does this introduce compared to computing it on all calendar days?

**Answer:**

**The implementation (lines 96–101):**
```python
active_days = pos_for_returns != 0
if active_days.sum() > 0:
    sharpe = (np.mean(pnl_net[active_days]) /
             np.std(pnl_net[active_days]) * np.sqrt(252))
else:
    sharpe = 0
```

This computes the mean and standard deviation of daily P&L *only on days when a position is active* (state ≠ 0), then annualizes by √252.

**Is this the correct approach?**

It depends on what question you're answering:

- **If measuring the strategy's edge per unit of active risk:** Computing on active days only is appropriate. It answers: "When the strategy is deployed, what is its risk-adjusted return?"
- **If measuring the strategy's overall performance as a capital allocation:** Computing on ALL calendar days is more appropriate. It answers: "What return does my capital earn over the full period, including the days it sits idle?"

For a capital allocator or portfolio manager, the second interpretation is standard. The capital is committed to this strategy whether or not a position is active — it cannot be deployed elsewhere (opportunity cost).

**The bias introduced by active-days-only computation:**

1. **Upward bias on the mean.** Inactive days have PnL = 0. Including them would lower the mean: mean_all = mean_active × (active_days/total_days). If the strategy is active 40% of the time, mean_all = 0.4 × mean_active.

2. **Downward bias on the standard deviation.** Adding many zero-PnL days to the sample reduces the standard deviation (the zeros pull it toward the mean). However, the reduction is less than proportional, so the net effect on the ratio depends on the fraction of active days.

3. **The Sharpe ratio is inflated.** For a strategy that is inactive most of the time, the active-days-only Sharpe can be dramatically higher than the all-days Sharpe. This is misleading: a strategy that earns a great Sharpe on 20 active days out of 500 is not as attractive as it appears, because the capital is idle 96% of the time.

**Quantitative example:** Suppose the strategy is active 100 days out of 500, with mean daily PnL = $2 and std = $5 on active days.
- Active-only Sharpe: (2/5) × √252 = 6.35.
- All-days Sharpe: mean = 2 × (100/500) = 0.4, std ≈ √((100/500) × 25 + (400/500) × 0.16) ≈ √(5.128) ≈ 2.26. Sharpe = (0.4/2.26) × √252 ≈ 2.81.

The active-only Sharpe (6.35) is more than double the all-days Sharpe (2.81).

**Additional issue: operator precedence.** The code has a subtle bug in the Sharpe computation:
```python
sharpe = (np.mean(pnl_net[active_days]) /
         np.std(pnl_net[active_days]) * np.sqrt(252))
```
Due to Python operator precedence, this evaluates as `(mean / std) * sqrt(252)`, which is correct. But the parentheses are misleading — they only group the numerator, not the denominator. A clearer version would be:
```python
sharpe = np.mean(pnl_net[active_days]) / np.std(pnl_net[active_days]) * np.sqrt(252)
```
In this case the result is the same, but it's fragile — if someone adds to the denominator later, the precedence could produce a wrong result.

**Standard practice:** In professional quant finance, the Sharpe ratio is almost always computed on all calendar days (or all trading days), treating inactive days as zero-return days. This gives a fair comparison across strategies with different activity levels.

**Key takeaway:** The active-days-only Sharpe inflates the reported risk-adjusted return by excluding idle periods. The standard approach is to compute on all trading days, which fairly accounts for the opportunity cost of committed capital.

---

### Q040 — Backtest Loop Bug

**Question:** In the orchestration notebook `test_pair.ipynb`, the loop that backtests all four pairs contains `df_bt = pd.concat([data_bt["UNH"], data_bt["ELV"]], axis=1).dropna()` inside the loop body. What is the bug? What are its consequences for the reported results?

**Answer:**

**The buggy code (from `test_pair.ipynb`):**
```python
paires = [('TMO', 'DHR'), ('UNH', 'ELV'), ('DE', 'AGCO'), ('SNPS', 'CDNS')]

for tik1, tik2 in paires:
    df = pd.concat([data[tik1], data[tik2]], axis=1).dropna()
    prixA = df.iloc[:, 0]
    prixB = df.iloc[:, 1]
    spread, hedge = Coint_verif.spread_n_hedge_ratio_static(prixA, prixB)

    # BUG: hardcoded UNH/ELV instead of tik1/tik2
    df_bt = pd.concat([data_bt["UNH"], data_bt["ELV"]], axis=1).dropna()
    prixA_bt = df_bt.iloc[:, 0]
    prixB_bt = df_bt.iloc[:, 1]
    spread_bt = prixA_bt - hedge * prixB_bt
    ...
```

**The bug:** The out-of-sample data is always loaded for UNH and ELV, regardless of which pair is being backtested. The variables `tik1` and `tik2` are correctly used for the in-sample data (hedge ratio and OU estimation), but the backtest prices are hardcoded to UNH/ELV.

The line should be:
```python
df_bt = pd.concat([data_bt[tik1], data_bt[tik2]], axis=1).dropna()
```

**Consequences for reported results:**

1. **The OU parameters and hedge ratio are pair-specific.** For TMO–DHR, the hedge ratio β is computed from TMO and DHR in-sample prices. But the out-of-sample spread is computed as: spread_bt = UNH_price − β_{TMO-DHR} × ELV_price. This is nonsensical — it applies TMO–DHR's hedge ratio to UNH–ELV's prices.

2. **The backtest results for all pairs except UNH–ELV are meaningless.** The reported P&L for "TMO–DHR" is actually the result of trading UNH–ELV prices with TMO–DHR parameters. Since the hedge ratio is wrong for UNH–ELV, the constructed spread is not stationary, and the z-score signals are arbitrary.

3. **The UNH–ELV result happens to be correct** (when the loop iterates with tik1="UNH", tik2="ELV"), because the hardcoded tickers match the loop variable by coincidence.

4. **The conclusion that "only UNH–ELV is profitable" may be an artifact.** The other pairs were never actually backtested on their own out-of-sample data. They might be profitable with the correct prices, or they might not — we cannot tell from the current results.

5. **This is a copy-paste error.** The single-pair backtest cell (which correctly uses hardcoded UNH/ELV for a single test) was likely copied into the loop without updating the ticker references.

**Key takeaway:** All backtest results except UNH–ELV are invalid due to hardcoded tickers. The comparative analysis across pairs cannot be trusted. Fixing the one line (`data_bt[tik1]`, `data_bt[tik2]` instead of `data_bt["UNH"]`, `data_bt["ELV"]`) would produce the correct results.

---

### Q041 — Look-Ahead Bias

**Question:** Does this backtest suffer from look-ahead bias? Analyze each step of the pipeline (pair selection, hedge ratio, OU estimation, signal parameters) for potential information leakage.

**Answer:**

**Definition:** Look-ahead bias occurs when the backtest uses information that would not have been available at the time a trading decision is made. It causes the backtest to overstate performance because it implicitly benefits from future knowledge.

**Step-by-step analysis:**

**1. Pair selection — LOW RISK but not zero.**
The pairs are selected based on cointegration tests on 2010–2024 data. At the start of the out-of-sample period (Jan 2024), you would have had access to all this data, so the pair selection itself is not forward-looking.

However, there is a subtle survivorship concern: the candidate universe in `pairs_universe.csv` was curated by the author, who may have been influenced by knowledge of which pairs "worked" during the backtest period. If the universe was constructed after seeing the 2024–2026 data, the economic pre-filter itself becomes a source of look-ahead bias. Assuming the universe was genuinely constructed based on economic reasoning alone, this is not an issue.

**2. Hedge ratio β — NO LOOK-AHEAD.**
The hedge ratio is estimated on 2010–2024 data via Johansen and held fixed during the 2024–2026 backtest. The backtest does not re-estimate β using future data. This is correct.

**3. OU parameters (θ, μ, σ) — NO LOOK-AHEAD.**
Similarly, the OU parameters are estimated on the in-sample spread and frozen. The z-score during the backtest uses the in-sample μ and σ_stationary. No future data leaks into these estimates.

**4. Signal parameters (k_entry, k_exit, stop_loss) — NO LOOK-AHEAD but also NO OPTIMIZATION.**
The strategy parameters are fixed defaults (k_entry=2, k_exit=0.2, stop_loss=3), not optimized on any data. This eliminates the risk of in-sample overfitting of the signal thresholds. However, it also means the parameters may be suboptimal for the specific pairs traded.

**5. The backtest loop itself — NO LOOK-AHEAD.**
The `backtest()` method processes the spread sequentially. The `signal()` function at time t only sees spread[t] and the current state — it does not access future spread values. Positions are determined one step at a time.

**6. The spread construction during backtest — POTENTIAL SUBTLE ISSUE.**
The out-of-sample spread is computed as:
```python
spread_bt = prixA_bt - hedge * prixB_bt
```
This uses the full out-of-sample price arrays. If this array were used for any estimation (e.g., re-computing μ or σ on the entire out-of-sample period), that would be look-ahead. But it is not — the arrays are only accessed element by element through the signal loop. So this is clean.

**Overall verdict:** The backtest does NOT suffer from look-ahead bias in its current implementation. The temporal separation between in-sample estimation (2010–2024) and out-of-sample evaluation (2024–2026) is clean. Parameters are frozen and never updated using future information.

**What WOULD introduce look-ahead bias:**
- Optimizing k_entry, k_exit, stop_loss on the backtest period and then reporting performance on the same period.
- Re-estimating β or μ using the full out-of-sample spread (rather than a rolling window that only looks backward).
- Selecting which pairs to trade based on out-of-sample performance.

**Key takeaway:** The backtest is clean with respect to look-ahead bias. The strict separation between training (2010–2024) and testing (2024–2026) periods, combined with frozen parameters and sequential signal processing, ensures no future information leaks into trading decisions.

---

### Q042 — Win Rate as a Metric

**Question:** The win rate is computed as the proportion of positive daily PnL on active days. Why is this a poor standalone metric for evaluating a pair trading strategy? What metric would be more informative?

**Answer:**

**The implementation (line 116):**
```python
'win_rate': np.mean(pnl_net[active_days] > 0) if active_days.sum() > 0 else 0,
```

This counts the fraction of active days where the net PnL is positive.

**Why win rate is a poor standalone metric:**

1. **It ignores the magnitude of wins and losses.** A strategy with 90% win rate but where the average loss is 20× the average win is catastrophic. Conversely, a strategy with 30% win rate but where the average win is 5× the average loss is highly profitable. For pair trading, this is especially relevant: the stop-loss triggers infrequently but incurs a large loss when it does, while take-profit trades capture smaller but more frequent gains.

2. **Daily win rate ≠ trade win rate.** The metric counts daily PnL, not trade-level outcomes. A single profitable trade lasting 50 days contributes 50 "wins" to the numerator. A single losing day contributes 1 "loss." This conflates trade frequency with trade quality. A strategy that holds one long winning trade is indistinguishable from a strategy that enters and exits 50 times, each time profiting for one day.

3. **No risk adjustment.** A 60% win rate with $1 average P&L and $10 standard deviation is very different from a 60% win rate with $1 average P&L and $0.50 standard deviation. The win rate captures nothing about risk.

4. **Sensitive to position frequency.** A strategy that enters and exits frequently (many small active periods) has more "votes" in the win rate than a strategy that enters once and holds. The metric is biased toward high-frequency strategies.

5. **Benchmark-free.** A 55% daily win rate sounds good, but what would a random strategy achieve? If the spread has a slight upward drift and you're long most of the time, you might see >50% positive days without any skill.

**More informative metrics:**

| Metric | What it captures |
|--------|-----------------|
| **Profit factor** (gross profit / gross loss) | The ratio of total winnings to total losses. Directly captures the asymmetry between wins and losses. A profitable strategy has PF > 1. |
| **Average profit per trade** (total PnL / n_trades) | The expected value of a round-trip trade. Directly answers: "Is the strategy worth trading after costs?" |
| **Calmar ratio** (annualized return / max drawdown) | Risk-adjusted performance that penalizes large drawdowns — particularly relevant for pair trading where regime changes cause sharp losses. |
| **Trade-level win rate** | Proportion of round-trip trades that are profitable. More meaningful than daily win rate because it aggregates by economic event (a complete trade) rather than by calendar day. |
| **Recovery factor** (net profit / max drawdown) | How much profit the strategy generates per unit of peak loss. A measure of resilience. |
| **Expectancy** = win_rate × avg_win − (1 − win_rate) × avg_loss | Combines win rate with magnitude to give the expected PnL per trade. This is the single number that integrates all the information the win rate alone misses. |

**Key takeaway:** Win rate counts frequency of positive days, ignoring magnitude of wins/losses, trade structure, and risk. It is particularly misleading for pair trading where a few large stop-losses can dominate the P&L despite many small winning days. Profit factor, average profit per trade, and expectancy are far more informative.

---

### Q043 — Regime Change Detection

**Question:** Only UNH–ELV shows positive out-of-sample PnL. The other pairs lose money. How could you distinguish before entering a trade whether the cointegration relationship is still intact? Propose a concrete statistical test or monitoring approach.

**Answer:**

**The problem:**

The strategy enters positions based on the assumption that the spread is mean-reverting. If the cointegration relationship has broken down (structural break), the spread is no longer stationary — it may trend indefinitely, and every mean-reversion entry becomes a losing trade. The strategy has no mechanism to detect this, relying solely on the stop-loss for protection.

**Concrete approaches for real-time cointegration monitoring:**

**Approach 1 — Rolling ADF test on the spread.**

Before each entry signal, run an ADF test on the most recent W observations of the spread (e.g., W = 250 days ≈ 1 year):

```python
from statsmodels.tsa.stattools import adfuller

def is_cointegration_intact(spread_history, window=250, pvalue_threshold=0.10):
    recent = spread_history[-window:]
    adf_stat, adf_pval, *_ = adfuller(recent)
    return adf_pval < pvalue_threshold
```

If the rolling ADF fails to reject the unit root hypothesis, the strategy suspends trading on that pair. Use a more lenient threshold (10% instead of 5%) because the rolling window is shorter and the test has less power.

**Pros:** Simple, directly tests the stationarity assumption. **Cons:** Lagging indicator — by the time the ADF detects the break, you may already be in a losing trade. Also, short windows reduce test power.

**Approach 2 — CUSUM (Cumulative Sum) test on spread residuals.**

Monitor the cumulative sum of the spread's deviations from the estimated μ:

$$C(t) = \sum_{i=t_0}^{t} (S(i) - \hat{\mu})$$

Under stationarity, C(t) fluctuates around zero. Under a structural break (mean shift), C(t) trends upward or downward. Detect a break when |C(t)| exceeds a threshold calibrated from the OU parameters:

$$|C(t)| > h \cdot \hat{\sigma}_\infty \cdot \sqrt{t - t_0}$$

where h is a sensitivity parameter (typically 4–5).

**Pros:** Detects mean shifts faster than the rolling ADF because it accumulates evidence. **Cons:** Sensitive to the choice of h; doesn't detect changes in θ or σ.

**Approach 3 — Rolling Johansen hedge ratio stability.**

Re-estimate the hedge ratio β on a rolling window and track its evolution. If β drifts significantly from the value used in the strategy, the spread construction is no longer valid:

$$|\hat{\beta}_{\text{rolling}} - \hat{\beta}_{\text{fixed}}| > \delta \cdot \text{se}(\hat{\beta}_{\text{rolling}})$$

A β shift of more than 2–3 standard errors suggests the cointegration relationship has changed.

**Pros:** Directly monitors the quantity that defines the spread. **Cons:** Requires enough data in each window for a reliable Johansen estimate.

**Approach 4 — Kalman filter on the hedge ratio.**

Model β as a time-varying state:
- State equation: β(t) = β(t−1) + η(t), η ~ N(0, Q)
- Observation equation: A(t) = β(t)·B(t) + ε(t), ε ~ N(0, R)

The Kalman filter continuously updates β(t) and provides a filtered estimate with uncertainty. If the innovation sequence (prediction errors) becomes systematically large or non-stationary, the relationship has broken down.

**Pros:** Optimal real-time tracking, provides uncertainty estimates, naturally detects both gradual drift and sudden breaks. **Cons:** Requires specifying the state noise variance Q, which controls the trade-off between responsiveness and stability.

**Approach 5 — Half-life monitoring.**

Re-estimate θ on a rolling window. If the half-life increases dramatically (e.g., from 55 days to 200+ days), the spread is reverting so slowly that the strategy is unlikely to profit within a reasonable holding period. Suspend trading when t½ exceeds a threshold (e.g., 2× the in-sample half-life).

**Recommended hybrid approach:**

Combine approaches for robustness:
1. **Primary trigger:** Rolling ADF p-value on the most recent 250 days of spread. If p > 0.10, suspend trading.
2. **Secondary trigger:** CUSUM on the spread residuals to detect mean shifts faster than the rolling ADF.
3. **Calibration monitor:** Track the rolling half-life. If it exceeds 2× the in-sample estimate, flag a warning.

Re-enable trading only when all monitors return to acceptable levels for at least 20 consecutive days (to avoid whipsawing).

**Key takeaway:** The most practical approach is a rolling ADF test combined with CUSUM monitoring. Before each entry, verify that the most recent spread data still supports stationarity. This adds a "cointegration gate" before the z-score signal gate, preventing entries when the relationship has broken down.

---

## 8. Performance and Optimization

---

### Q044 — Computational Bottleneck

**Question:** Which part of the pipeline is the most computationally expensive? How does it scale with the number of candidate pairs and the length of the time series?

**Answer:**

**Breakdown of computational cost by stage:**

| Stage | Operation | Complexity per pair | Dominant cost |
|-------|-----------|-------------------|---------------|
| Data loading | CSV read or yfinance download | O(T) per ticker | I/O-bound, not CPU |
| Integration order (ADF × 4) | ADF test | O(T · p) per test, p = lag order | ADF runs an OLS regression of size T with p lags, repeated for each of ~20 candidate lag lengths (AIC selection). Four tests per pair. |
| Johansen decomposition | Generalized eigenvalue problem on the VECM | O(T · k² + k³) where k = 2 (bivariate) | Matrix operations on T × 2 data. Fast for k = 2. |
| Spread stationarity (ADF + KPSS + PP) | Three unit root tests | O(T · p) each | Similar to step 2, three additional tests. |
| Cointegration tests (EG + Johansen trace) | Engle-Granger uses `coint()`, Johansen already computed | O(T · p) for EG | EG runs an ADF on regression residuals. |
| Hurst exponent (R/S method) | R/S analysis | O(T · log T) | Computes R/S statistic at multiple window sizes. |
| OU estimation (OLS) | Linear regression | O(T) | Trivial — one OLS solve on T observations. |
| Backtest | Sequential signal loop | O(T_oos) | Python for-loop over ~630 observations. |

**The bottleneck is the cointegration testing battery**, specifically the multiple ADF tests (steps 2 and 3). Each ADF test involves:
1. Selecting the lag order p by testing multiple candidates (typically p = 1 to ~20) via AIC.
2. For each candidate p, running an OLS regression with T − p observations and p + 2 regressors.
3. The `adfuller` function from statsmodels does this automatically with `autolag='AIC'`.

With 4 ADF tests per pair (step 2) plus 1 ADF on the spread (step 3), plus KPSS and PP, the total testing cost per pair is approximately 6–7 unit root tests. For ~40 candidate pairs, that's ~280 unit root tests, each involving multiple OLS regressions on ~3500 observations.

**Scaling:**

- **With N pairs:** Total cost scales as O(N) — linear in the number of candidate pairs. Each pair is tested independently.
- **With time series length T:** Each ADF test is O(T · p_max), so total cost is O(N · T · p_max). Since p_max is typically O(T^(1/3)) by default (the Schwert rule), the effective scaling is O(N · T^(4/3)).
- **The backtest is cheap** by comparison — O(T_oos) with a small constant. The signal loop is a simple Python for-loop with no expensive computations inside.

**Practical timing:** For 40 pairs and T ≈ 3500, the full pipeline runs in seconds to low minutes on a modern machine. The computational cost is not a practical bottleneck at this scale. It would become relevant if:
- The universe grew to thousands of pairs (all-pairs testing on 500 stocks = 125,000 pairs).
- Higher-frequency data were used (T = 1M+ for tick data).
- Rolling re-estimation required running the full test battery at each time step.

**Key takeaway:** The cointegration test battery (multiple ADF tests per pair) dominates computation. It scales as O(N · T^(4/3)) where N is the number of pairs and T is the series length. At the current scale (~40 pairs, T ≈ 3500), this is not a practical concern.

---

### Q045 — Vectorization Opportunities

**Question:** The `backtest()` method uses a Python for-loop to generate signals. Could the signal generation be vectorized? What makes this non-trivial?

**Answer:**

**The current implementation (lines 70–76):**
```python
positions = np.zeros(n)
state, entry_day = self.signal(spread=spread[0], today=0)
positions[0] = state
for t, spread_t in enumerate(spread[1:]):
    state, entry_day = self.signal(spread=spread_t, today=t+1, state=state, entry_day=entry_day)
    positions[t+1] = state
```

This is a sequential loop where each step depends on the previous state.

**Why vectorization is non-trivial:**

The core difficulty is that the state machine has **sequential dependencies**: the signal at time t depends on the state at time t−1, which depends on the signal at t−1, and so on. This creates a chain of dependencies that prevents straightforward parallelization.

Specifically, the transition rules are *state-dependent*:
- From state 0: entry conditions (z > k_entry or z < −k_entry).
- From state +1: exit conditions (z > −k_exit, z < −stop_loss, time stop).
- From state −1: symmetric exit conditions.

You cannot precompute all positions simultaneously because whether position[t] is +1 or 0 depends on whether position[t−1] was +1 (holding) or 0 (potential new entry), which in turn depends on position[t−2], etc.

**What CAN be vectorized:**

1. **The z-score computation:**
```python
z_scores = (spread - self.mean) / self.std
```
This is fully vectorizable — one array operation.

2. **Entry signal detection (from flat state only):**
```python
entry_long = z_scores < -self.k_entry
entry_short = z_scores > self.k_entry
```
These boolean arrays can be precomputed. However, they only determine *potential* entries — whether an entry actually occurs depends on whether the state is flat at that time.

3. **The PnL computation after positions are determined** is already vectorized (lines 78–93).

**Partial vectorization approach:**

One could adopt a semi-vectorized approach:
- Precompute z-scores as a vector.
- Use `numba.jit` or Cython to compile the state machine loop, eliminating Python interpreter overhead while keeping the sequential logic.
- For the specific case of no `max_holding` and no time stop, the state transitions depend only on the z-score crossing thresholds, which could be formulated as a scan operation.

**Numba example:**
```python
from numba import njit

@njit
def generate_positions(z_scores, k_entry, k_exit, stop_loss):
    n = len(z_scores)
    positions = np.zeros(n)
    state = 0
    for t in range(n):
        z = z_scores[t]
        if state == 0:
            if z > k_entry:
                state = -1
            elif z < -k_entry:
                state = 1
        elif state == 1:
            if z > -k_exit or z < -stop_loss:
                state = 0
        elif state == -1:
            if z < k_exit or z > stop_loss:
                state = 0
        positions[t] = state
    return positions
```

This keeps the sequential logic but runs at compiled speed — typically 50–100× faster than pure Python. For T ≈ 630 (the out-of-sample length), the Python loop takes microseconds, so optimization is unnecessary. But for intraday data (T = 1M+) or parameter grid search (running the loop thousands of times), Numba would provide meaningful speedup.

**Key takeaway:** The state machine's sequential dependencies prevent pure vectorization. The z-score and PnL computations are vectorizable, but the position generation loop must remain sequential. Numba/Cython compilation is the practical solution for performance-critical scenarios.

---

### Q046 — Parameter Optimization

**Question:** How would you optimize the strategy parameters (k_entry, k_exit, stop_loss) per pair? Describe a walk-forward optimization approach and explain how to avoid overfitting.

**Answer:**

**The problem:**

The current strategy uses fixed defaults (k_entry=2, k_exit=0.2, stop_loss=3) for all pairs. Different pairs have different OU dynamics (different θ, σ, half-lives), so the optimal thresholds likely differ per pair. However, naively optimizing parameters on the backtest period and then reporting performance on the same period leads to overfitting — the parameters are tuned to historical noise rather than a persistent signal.

**Walk-forward optimization:**

Walk-forward optimization is a rolling out-of-sample validation framework. The idea: at each step, optimize parameters on a training window and evaluate on a subsequent validation window, then roll forward.

**Procedure:**

1. **Define the parameter grid.** For example:
   - k_entry ∈ {1.0, 1.5, 2.0, 2.5, 3.0}
   - k_exit ∈ {0.0, 0.1, 0.2, 0.5, 1.0}
   - stop_loss ∈ {2.5, 3.0, 3.5, 4.0, 5.0}
   - Total: 5 × 5 × 5 = 125 combinations.

2. **Define the rolling windows.** For example:
   - Training window: 3 years of daily data (~750 observations).
   - Validation window: 6 months (~125 observations).
   - Step size: 6 months (non-overlapping validation windows).

3. **At each step i:**
   a. Estimate the hedge ratio and OU parameters on the training window.
   b. For each parameter combination, run the backtest on the training window. Select the combination that maximizes the objective (e.g., Sharpe ratio, or Calmar ratio, or total PnL).
   c. Apply the selected parameters to the validation window (out-of-sample). Record the validation performance.
   d. Roll forward: move both windows by the step size.

4. **Aggregate validation performance** across all steps. The walk-forward Sharpe ratio is computed on the concatenation of all validation windows. This is a genuine out-of-sample estimate.

**How to avoid overfitting:**

1. **Restrict the parameter grid.** A finer grid (more combinations) increases the chance of overfitting to noise in the training window. Keep the grid coarse — 125 combinations is manageable; 10,000 is excessive.

2. **Use a robust objective function.** Maximize Sharpe ratio rather than total PnL (Sharpe penalizes high variance). Even better: maximize the minimum Sharpe across the training sub-periods, which penalizes parameter sets that work well in one regime but poorly in another.

3. **Impose constraints on parameters.** For example: k_entry > k_exit + 1 (ensure meaningful profit band), stop_loss > k_entry (stop-loss beyond entry), k_exit > 0 (no zero exit). These constraints encode economic priors and reduce the search space.

4. **Regularize toward the defaults.** If two parameter combinations have similar validation Sharpe, prefer the one closer to the theoretical defaults (k_entry ≈ 2, k_exit ≈ 0). This acts as a Bayesian prior toward the "standard" values.

5. **Monitor the gap between training and validation performance.** A large gap (training Sharpe = 3, validation Sharpe = 0.5) indicates overfitting. A small gap (training Sharpe = 1.5, validation Sharpe = 1.2) suggests the signal is real.

6. **Minimum trade count.** Discard parameter combinations that produce fewer than (e.g.) 5 trades in the training window. Low trade counts make the performance estimate unreliable.

**Pair-specific considerations:**

The optimal parameters should relate to the OU dynamics:
- **k_entry** should scale with the half-life: pairs with shorter half-lives (faster reversion) can use lower entry thresholds because reversion is more reliable. Pairs with longer half-lives need higher entry thresholds for a stronger signal.
- **stop_loss** should scale with the OU volatility: higher σ means wider natural fluctuations, so the stop-loss needs to be further from the entry to avoid false triggers.
- **k_exit** should be calibrated to the transaction costs: a tighter exit (closer to 0) captures more profit per trade but requires more precision. If transaction costs are significant, a slightly wider exit reduces the number of marginal trades.

**Key takeaway:** Walk-forward optimization rolls a training/validation window through time, optimizing parameters in-sample and evaluating out-of-sample. Overfitting is controlled by coarse grids, robust objectives, constraints, and monitoring the training/validation gap. Parameters should be pair-specific and relate to the OU dynamics.

---

## 9. Limitations, Robustness, and Alternative Approaches

---

### Q047 — Constant Volatility Assumption

**Question:** The OU model assumes constant σ. What evidence from the diagnostic tests would indicate this assumption is violated? What alternative model would accommodate time-varying volatility?

**Answer:**

**Evidence from diagnostic tests:**

The `diagnostic_tests()` method in `fit_ou_model.py` provides direct evidence via the **ARCH-LM test** (line 146):

```python
arch_stat, arch_pval, _, _ = het_arch(self.residuals, nlags=5)
```

The ARCH-LM test regresses squared residuals on their own lags:

$$\hat{\varepsilon}_t^2 = \alpha_0 + \alpha_1 \hat{\varepsilon}_{t-1}^2 + ... + \alpha_5 \hat{\varepsilon}_{t-5}^2 + u_t$$

H₀: α₁ = α₂ = ... = α₅ = 0 (no ARCH effects, constant variance). If the p-value is small (< 0.05), reject H₀ — the residual variance is conditionally heteroscedastic.

For financial spread data, ARCH-LM almost always rejects. This is because:
- Volatility clusters: periods of high spread volatility follow other high-volatility periods.
- Market-wide events (earnings, macro releases) create synchronized spikes in both legs.
- The OU model's constant σ cannot capture these dynamics.

**Additional indirect evidence:**
- **Jarque-Bera test:** Excess kurtosis (leptokurtic residuals) often accompanies ARCH effects. Conditional heteroscedasticity produces unconditionally fat-tailed residuals even if the conditional distribution is Gaussian.
- **Visual inspection:** Plotting the standardized residuals reveals volatility clustering — periods of large residuals followed by large residuals.

**Alternative models:**

**1. OU-GARCH (recommended first step):**

Model the spread as an OU process with GARCH(1,1) innovations:

$$S_{t+1} = a \cdot S_t + b + \sigma_t \varepsilon_t, \quad \varepsilon_t \sim N(0,1)$$
$$\sigma_t^2 = \omega + \alpha \varepsilon_{t-1}^2 \sigma_{t-1}^2 + \beta \sigma_{t-1}^2$$

The z-score is then normalized by the *current conditional volatility* rather than the unconditional σ_∞:

$$z(t) = \frac{S(t) - \mu}{\sigma_t / \sqrt{2\theta}}$$

This adapts entry/exit thresholds to the current volatility regime: wider bands during high-vol periods, tighter during low-vol.

**2. Stochastic volatility OU:**

The continuous-time version:

$$dS(t) = \theta(\mu - S(t))dt + \sigma(t)dW_1(t)$$
$$d\ln\sigma(t) = \kappa(\bar{\sigma} - \ln\sigma(t))dt + \xi dW_2(t)$$

with possible correlation between W₁ and W₂. This is more flexible but harder to estimate (requires particle filters or MCMC).

**3. Regime-switching OU:**

Two OU regimes with different (θ, μ, σ), governed by a Markov chain:
- Regime 1: low volatility, stable cointegration (σ_low, θ_high).
- Regime 2: high volatility, weaker cointegration (σ_high, θ_low).

The strategy can condition on the estimated regime: trade aggressively in regime 1, reduce exposure or stop in regime 2.

**4. Practical shortcut — EWMA volatility:**

Without fitting a full GARCH model, use an exponentially weighted moving average of squared spread changes to estimate current volatility:

$$\hat{\sigma}_t^2 = \lambda \hat{\sigma}_{t-1}^2 + (1-\lambda)(S_t - S_{t-1})^2$$

with λ ≈ 0.94 (RiskMetrics convention). Normalize the z-score by √(σ̂²_t / (2θ)). This is simple, adaptive, and often sufficiently effective.

**Key takeaway:** The ARCH-LM test directly detects violation of the constant-σ assumption. OU-GARCH or EWMA volatility normalization are the most practical fixes — they adapt the z-score bands to current market conditions without requiring a full model overhaul.

---

### Q048 — Kalman Filter Alternative

**Question:** The report mentions using a Kalman filter for a dynamic hedge ratio as a potential improvement. Explain how a Kalman filter could be applied here. What is the state-space model, and what are the advantages over a static Johansen estimate?

**Answer:**

**The state-space model:**

The key idea is to treat the hedge ratio β as a *hidden state* that evolves slowly over time, rather than a fixed parameter.

**State equation (β evolves as a random walk):**

$$\beta_t = \beta_{t-1} + \eta_t, \quad \eta_t \sim N(0, Q)$$

This says the hedge ratio drifts by a small amount each day. The variance Q controls how fast β can change: small Q → β is nearly constant (close to the static Johansen result), large Q → β adapts quickly to new data.

**Observation equation (the price relationship):**

$$P_A(t) = \beta_t \cdot P_B(t) + \alpha + \varepsilon_t, \quad \varepsilon_t \sim N(0, R)$$

or equivalently, the spread S(t) = P_A(t) − β_t · P_B(t) = α + ε_t. The observation noise R captures the spread's deviation from the equilibrium at each point.

In matrix form for the Kalman filter:
- State: x_t = [β_t, α_t]' (can include the intercept as a state too)
- Transition: x_t = F · x_{t−1} + η_t, with F = I (random walk)
- Observation: P_A(t) = H_t · x_t + ε_t, where H_t = [P_B(t), 1]

**Kalman filter recursion:**

At each time step t:

1. **Predict:** x̂_{t|t−1} = F · x̂_{t−1|t−1}, P_{t|t−1} = F · P_{t−1|t−1} · F' + Q
2. **Update:**
   - Innovation: ν_t = P_A(t) − H_t · x̂_{t|t−1}
   - Innovation variance: S_t = H_t · P_{t|t−1} · H_t' + R
   - Kalman gain: K_t = P_{t|t−1} · H_t' · S_t⁻¹
   - Updated state: x̂_{t|t} = x̂_{t|t−1} + K_t · ν_t
   - Updated covariance: P_{t|t} = (I − K_t · H_t) · P_{t|t−1}

The output is a time series of filtered hedge ratios β̂_t with associated uncertainty P_{t|t}.

**Advantages over static Johansen:**

| Aspect | Static Johansen | Kalman filter |
|--------|----------------|---------------|
| **Adaptation** | Fixed β estimated once on 14 years | β updated daily as new data arrives |
| **Responsiveness** | Cannot detect β drift | Automatically tracks gradual drift via Q parameter |
| **Uncertainty quantification** | Single point estimate (CI from asymptotics) | Full posterior P_{t|t} at every time step |
| **Data efficiency** | Uses all 3500 points equally | Recent data weighted more heavily via the recursive update |
| **Regime change** | Blind — uses stale β until re-estimated | Innovation sequence ν_t flags anomalies in real time |
| **No window choice** | N/A | Implicit exponential weighting controlled by Q/R ratio — no arbitrary window length |

**Practical considerations:**

1. **Choosing Q and R:** The ratio Q/R controls the filter's responsiveness. Q/R → 0: β barely moves (equivalent to static estimate). Q/R → ∞: β jumps to match each observation (overfitting). Typically Q/R is estimated by maximum likelihood on a training period. A common starting point is Q = 10⁻⁵ to 10⁻⁴ and R estimated from the spread variance.

2. **Using the filtered β for trading:** At each time step, construct the spread as S(t) = P_A(t) − β̂_{t|t} · P_B(t). Then fit the OU model to recent spread values (e.g., rolling 250 days) and generate z-scores as usual. This means both the hedge ratio and the OU parameters are adaptive.

3. **Detecting cointegration breakdown:** If the innovation variance S_t grows persistently (the filter's predictions are systematically wrong), it signals a structural change. This provides a natural cointegration monitoring mechanism.

4. **Implementation:** The Kalman filter for this linear Gaussian model is straightforward to implement (20–30 lines of Python) or available via `pykalman`, `filterpy`, or `statsmodels.tsa.statespace`.

**Key takeaway:** The Kalman filter models β as a time-varying state, continuously adapting to new data. It eliminates the need for choosing a rolling window, provides uncertainty quantification, and naturally detects regime changes through the innovation sequence. The trade-off is the need to specify (or estimate) the state noise variance Q.

---

### Q049 — Spread Construction Choice

**Question:** The project constructs the spread using price levels: `spread = A - β·B`. An alternative is to use log prices. What are the advantages and disadvantages of each approach? When would the choice matter?

**Answer:**

**Current approach — price levels:**

$$S(t) = P_A(t) - \beta \cdot P_B(t)$$

This is the linear cointegrating relationship estimated by Johansen on raw prices. The spread is in dollar units.

**Alternative — log prices:**

$$S_{\log}(t) = \ln P_A(t) - \beta_{\log} \cdot \ln P_B(t)$$

This is the cointegrating relationship estimated on log-transformed prices. The spread is in log-units (approximately percentage deviations).

**Advantages of price levels:**

1. **Simplicity.** The spread is in dollars, making position sizing and P&L computation straightforward. "Buy 1 share of A, sell β shares of B" gives direct dollar exposure.
2. **Consistency with Johansen.** The standard Johansen procedure tests for linear cointegration between levels. The implementation directly uses the Johansen eigenvector on prices.
3. **Matches the trading mechanics.** When you trade, you buy and sell shares at price levels, not at log-prices. The P&L is linear in price changes, not in log-price changes.

**Advantages of log prices:**

1. **Percentage-based hedge ratio.** β_log represents the *elasticity*: a 1% move in B corresponds to a β_log% move in A. This is scale-invariant — it does not depend on the absolute price level of the stocks.
2. **Better stationarity properties.** For stocks that grow over time (trending prices), the dollar spread A − β·B can become non-stationary even if the log-spread is stationary. This is because the dollar magnitude of fluctuations scales with the price level. Example: if both stocks double over 14 years, the dollar spread doubles too, but the log-spread remains bounded.
3. **Consistent with the log-normal model.** Stock prices are typically modeled as geometric Brownian motion, meaning log-prices are the natural "unit" for statistical analysis. Cointegration of log-prices is equivalent to a stable long-run price ratio P_A / P_B^β — a more interpretable economic relationship than a stable linear combination.
4. **More stable hedge ratio.** The log-price β tends to be more stable over time because it captures the percentage relationship rather than the dollar relationship. If both prices double, the dollar-β doubles too, but the log-β stays the same.

**Disadvantages of log prices:**

1. **Trading implementation is more complex.** The position sizes for the log-spread require adjustment at each time step (because the dollar exposure per unit of log-price changes with the price level).
2. **OU model on log-spread.** If the log-spread follows an OU process, the dollar-spread follows a more complex process (roughly a multiplicative OU). The P&L is no longer simply position × Δspread.
3. **Johansen on log-prices.** The standard Johansen critical values assume I(1) series. Log-prices are I(1) (like prices), so Johansen applies equally to both. However, the economic interpretation changes.

**When does the choice matter?**

The choice matters most when:
- **Price levels change significantly over the sample period.** If stock A goes from $50 to $500 over 14 years, the dollar spread's variance grows 10× while the log-spread's variance may remain constant. The dollar-spread OU model would estimate an "average" σ that is too small for the recent period and too large for the early period.
- **The hedge ratio drifts.** The dollar-β is more sensitive to price-level changes than the log-β. Over 14 years, substantial price appreciation can cause the dollar-β to drift even if the percentage relationship is stable.
- **The OU stationary distribution is used for z-score normalization.** If the spread's variance changes with the price level, the OU model's constant σ assumption is more strongly violated for dollar-spreads than for log-spreads.

**For this project specifically:** The stocks in the universe have experienced significant price growth (e.g., UNH from ~$30 in 2010 to ~$500+ in 2024). The dollar spread's variance has likely increased substantially, making the constant-σ OU assumption questionable. Log-prices would partially mitigate this by stabilizing the variance.

**Practical recommendation:** For academic/research purposes, test both and compare the stationarity of the resulting spreads. For production, log-prices are generally preferred because they produce more stable hedge ratios and better-behaved spread series.

**Key takeaway:** Price levels are simpler and match trading mechanics directly. Log-prices produce more stable hedge ratios and better-behaved spreads when prices exhibit significant growth, at the cost of more complex position sizing. For 14-year training periods with substantial price appreciation, log-prices would likely produce better OU fits.

---

### Q050 — Structural Break Impact

**Question:** Suppose a major merger announcement occurs between the two companies in a pair. How would this event propagate through each stage of the pipeline? What would happen to the OU parameters, the z-score, and the trading signal?

**Answer:**

**Scenario:** Company B in a pair (A, B) receives a takeover bid. B's stock jumps 30% overnight. The merger is expected to close in 6 months.

**Impact at each stage:**

**1. The spread immediately jumps.**

S(t) = A(t) − β·B(t). If B jumps by 30% and A is unaffected (or moves less), the spread drops sharply: ΔS ≈ −β × 0.30 × P_B. For typical values (β ≈ 1.0, P_B ≈ $200), the spread drops by ~$60 in one day.

**2. The z-score spikes.**

z(t) = (S(t) − μ) / σ_∞. With σ_∞ ≈ 5–10 (typical for the retained pairs), a $60 drop produces Δz ≈ −60/σ_∞ ≈ −6 to −12. The z-score moves far beyond the entry threshold (−2) and even beyond the stop-loss (−3).

**3. The trading signal responds — but too late.**

If the strategy was flat: the z-score crosses −k_entry, triggering a long spread entry. But the spread will not mean-revert — B's new price level reflects the acquisition premium, which is permanent. The long position will lose money as the spread stays at its new level (or diverges further as merger arbitrage closes the premium).

If the strategy was already long spread: the z-score crosses −stop_loss (−3), triggering a stop-loss exit. The strategy incurs a large loss from the gap.

If the strategy was already short spread: this is actually profitable — the short spread position profits from the spread falling. However, the strategy would quickly exit at the take-profit threshold.

**4. The OU parameters become stale.**

The static μ and σ no longer describe the spread's behavior:
- **μ is wrong:** The spread has shifted permanently to a new level. The z-score is computed relative to a stale mean.
- **θ is irrelevant:** The spread is no longer mean-reverting — the merger premium introduces a new non-stationary component (the premium may fluctuate with deal probability but not revert to the pre-announcement level).
- **β is broken:** The economic relationship between the two companies is fundamentally altered. The cointegrating vector no longer captures a stable equilibrium.

**5. The cointegration is destroyed.**

Post-announcement, B's price is driven by deal-specific factors (regulatory approval probability, deal terms, competing bids) rather than the sector-wide factors that created the cointegration. The pair is no longer cointegrated, and any attempt to trade it as mean-reverting will fail.

**6. Long-term impact:**

If the merger completes: B is delisted. The pair ceases to exist. If the merger fails: B's price drops back toward pre-announcement levels, and cointegration may re-establish over time. During the uncertainty period, the spread behavior is dominated by merger arbitrage dynamics, not OU mean-reversion.

**How the strategy should handle this:**

1. **Stop-loss provides first-order protection.** The 3σ stop-loss would fire on the gap day (if in position), limiting losses to ~1σ_∞ beyond the entry point plus the gap (which could exceed 3σ in a single day, meaning the actual loss is worse than the stop-loss level implies — the strategy cannot exit at exactly z = −3 if the spread gaps through it).
2. **Cointegration monitoring (as in Q043)** would detect the break: the rolling ADF would reject stationarity, the Kalman filter's innovation would spike. The pair would be suspended.
3. **News-based filters** could be added: exclude pairs involved in active M&A discussions. But this requires real-time news feeds, not just price data.

**Key takeaway:** A merger announcement instantly destroys cointegration. The spread gaps permanently, the OU parameters become meaningless, and the z-score enters extreme territory. The stop-loss provides partial protection but cannot prevent gap risk. This is the fundamental tail risk of pair trading that no OU model can capture.

---

### Q051 — Heavy Tails

**Question:** If the spread exhibits heavy tails (excess kurtosis), which components of the pipeline would be most affected? How would you modify the z-score signal generation to be robust to heavy tails?

**Answer:**

**Which components are affected:**

**1. OU model estimation — moderately affected.**
OLS estimation of the AR(1) parameters (â, b̂) remains consistent even under non-Gaussian errors (OLS does not require normality for consistency). However, it is no longer efficient — the standard errors are wrong, and confidence intervals are unreliable. The σ estimate captures the unconditional standard deviation, which is dominated by the tails.

**2. Diagnostic tests — directly affected.**
- Jarque-Bera will reject normality (by design — it detects excess kurtosis).
- The ARCH-LM test may also reject, because heavy tails often co-occur with volatility clustering.
- Ljung-Box may be affected if the heavy tails are associated with non-linear serial dependence.

**3. Z-score signal generation — most critically affected.**
The z-score z = (S − μ)/σ_∞ implicitly assumes the spread follows the OU stationary distribution N(μ, σ²/(2θ)). Under this Gaussian assumption:
- P(|z| > 2) ≈ 4.6%
- P(|z| > 3) ≈ 0.27%

With heavy tails (e.g., Student-t with ν = 5 degrees of freedom):
- P(|z| > 2) ≈ 9%
- P(|z| > 3) ≈ 2.5%

This means entries (at z = ±2) occur much more frequently than the Gaussian model predicts, and stop-losses (at z = ±3) are triggered far more often. The strategy enters too many positions and gets stopped out too frequently — both reducing profitability.

**4. Stationarity tests — mildly affected.**
The ADF and Phillips-Perron tests are somewhat robust to non-Gaussian errors (their asymptotics allow for non-normality). KPSS is also designed to be robust. However, extreme outliers can inflate the test statistic variance, reducing power.

**5. Hurst exponent — affected.**
The R/S method is sensitive to outliers because the range R is dominated by extreme values. Heavy tails cause R to grow faster, which can bias H upward (toward 0.5 or above), potentially causing a genuinely mean-reverting spread to fail the Hurst test.

**Modifications for robust z-score signal generation:**

**Approach 1 — Use a robust scale estimator.**
Replace σ_∞ with a robust measure of spread dispersion that is less sensitive to outliers:

- **Median Absolute Deviation (MAD):** σ_robust = 1.4826 × MAD(S − median(S)). The factor 1.4826 makes it consistent with σ for Gaussian data.
- **Interquartile Range (IQR):** σ_robust = IQR / 1.349.
- **Winsorized standard deviation:** Clip extreme values at the 1st and 99th percentiles before computing σ.

The z-score becomes z = (S − μ_robust) / σ_robust, where μ_robust could be the median instead of the mean.

**Approach 2 — Use quantile-based thresholds.**
Instead of z-score thresholds (which assume Gaussian percentiles), use empirical quantile thresholds:
- Entry when the spread exceeds its empirical 97.5th percentile (short) or falls below its 2.5th percentile (long).
- Exit when the spread returns to the 45th–55th percentile range.

This is distribution-free — it automatically adapts to the actual tail behavior.

**Approach 3 — Student-t z-scores.**
Fit a Student-t distribution to the spread (estimating ν, μ, σ) and compute the z-score using the Student-t CDF:

$$z_t = \Phi^{-1}(F_\nu((S(t) - \mu) / \sigma))$$

where F_ν is the Student-t CDF and Φ⁻¹ is the Gaussian inverse CDF. This "Gaussianizes" the spread, making z-score thresholds meaningful regardless of tail behavior.

**Approach 4 — Adjust thresholds upward.**
If you keep the Gaussian z-score but know the tails are heavy, simply increase k_entry (e.g., from 2 to 2.5 or 3) and stop_loss (e.g., from 3 to 4 or 5). This compensates for the higher probability of extreme z-scores under heavy tails, at the cost of fewer trading signals.

**Key takeaway:** Heavy tails most critically affect the z-score signal generation, causing excessive entries and stop-losses. The most practical fix is to use robust scale estimators (MAD) or empirical quantile thresholds instead of Gaussian z-scores. This requires no model change — only the normalization step is modified.

---

### Q052 — Multi-Pair Portfolio

**Question:** If you were to trade all four pairs simultaneously, how would you allocate capital across them? What correlation structure between pairs would you need to account for, and how does this relate to the diversification benefit?

**Answer:**

**Why capital allocation matters:**

Trading four pairs simultaneously means capital must be split across them. Equal allocation (25% each) is the simplest approach but ignores differences in:
- Signal quality (some pairs may have stronger cointegration).
- Risk per pair (different σ, different half-life).
- Correlation between pairs (if two pairs move together, diversification benefit is reduced).

**Capital allocation approaches:**

**1. Equal risk allocation (Risk Parity).**
Allocate capital so that each pair contributes equally to portfolio variance:

$$w_i \propto \frac{1}{\sigma_i}$$

where σ_i is the expected volatility of pair i's PnL. Pairs with lower volatility get more capital. This equalizes risk contribution but ignores expected returns.

**2. Mean-variance optimization.**
Maximize the portfolio Sharpe ratio:

$$w^* = \Sigma^{-1} \mu / \mathbf{1}' \Sigma^{-1} \mu$$

where μ is the vector of expected returns per pair and Σ is the covariance matrix of pair PnLs. This is optimal in theory but highly sensitive to estimation errors in μ and Σ.

**3. Inverse half-life weighting.**
Allocate more capital to pairs with shorter half-lives (faster reversion, more confident mean-reversion):

$$w_i \propto \frac{1}{t_{1/2,i}}$$

For the four pairs: SNPS–CDNS (25d) gets the most, DE–AGCO (49d) and UNH–ELV (55d) get moderate, TMO–DHR (69d) gets the least. This reflects the intuition that faster mean-reversion is more reliable.

**4. Kelly-based allocation.**
Compute the Kelly fraction for each pair (based on its estimated win rate, average win/loss ratio, and OU parameters) and scale by a conservatism factor. Pairs with higher Kelly fractions get more capital.

**Correlation structure between pairs:**

The four pairs share common risk factors:
- **Market risk (β to SPY):** All four pairs involve large-cap US equities. A market-wide sell-off can cause all four spreads to move simultaneously, especially if the sell-off affects sectors differently.
- **Sector overlap:** UNH–ELV and TMO–DHR are both healthcare. A healthcare-specific shock (e.g., regulatory change) would affect both spreads simultaneously.
- **Common factor exposure:** If interest rates rise sharply, all four pairs may experience increased spread volatility (higher discount rate affects relative valuations).

**Measuring the correlation:**

Compute the pairwise correlation of the four spread return series:

$$\rho_{ij} = \text{Corr}(\Delta S_i, \Delta S_j)$$

If correlations are high (e.g., ρ > 0.3), the diversification benefit is limited — the four pairs behave partially like one bet. If correlations are low (ρ ≈ 0), the portfolio benefits from genuine diversification.

**Diversification benefit:**

For a portfolio of N pairs with equal weight and pairwise correlation ρ:

$$\sigma_{\text{portfolio}} = \sigma_{\text{pair}} \sqrt{\frac{1 + (N-1)\rho}{N}}$$

For N = 4, ρ = 0: σ_port = σ_pair / 2 (full diversification).
For N = 4, ρ = 0.5: σ_port = σ_pair × √(0.625) ≈ 0.79 σ_pair (limited benefit).

**Practical recommendation:**

1. Compute the correlation matrix of spread returns for the four pairs on the training data.
2. Use risk parity (inverse volatility weighting) as the baseline allocation.
3. Apply a correlation adjustment: if two pairs are highly correlated (ρ > 0.5), treat them as one "cluster" and allocate the cluster's weight as if it were a single pair.
4. Cap the maximum allocation to any single pair at 40% of capital (concentration limit).
5. Reserve 20–30% of capital as cash buffer (for margin calls, rebalancing, and new opportunities).

**Key takeaway:** Multi-pair allocation should account for differences in signal quality (half-life), risk (spread volatility), and inter-pair correlation. Risk parity is a sensible baseline. Healthcare pairs (UNH–ELV, TMO–DHR) likely have positive correlation, limiting diversification within that sector. Capital should be over-weighted toward faster-reverting pairs with lower cross-correlation.

---

## 10. Challenging Follow-Up Questions

---

### Q053 — Derive the OU Transition Density

**Question:** Starting from the OU SDE dX = θ(μ − X)dt + σ dW, derive the conditional distribution X(t+Δt) | X(t). Show that it is Gaussian and compute its mean and variance.

**Answer:**

**Step 1 — Solve the SDE using an integrating factor.**

Define Y(t) = e^(θt) X(t). Apply Itô's lemma (or direct product rule, since e^(θt) is deterministic):

$$dY(t) = \theta e^{\theta t} X(t) dt + e^{\theta t} dX(t)$$

Substituting dX = θ(μ − X)dt + σ dW:

$$dY = \theta e^{\theta t} X\,dt + e^{\theta t}[\theta(\mu - X)dt + \sigma\,dW]$$
$$= \theta e^{\theta t} X\,dt + \theta\mu e^{\theta t} dt - \theta e^{\theta t} X\,dt + \sigma e^{\theta t} dW$$
$$= \theta\mu e^{\theta t} dt + \sigma e^{\theta t} dW$$

The X terms cancel. Integrating from t to t + Δt:

$$Y(t+\Delta t) - Y(t) = \theta\mu \int_t^{t+\Delta t} e^{\theta s}\,ds + \sigma \int_t^{t+\Delta t} e^{\theta s}\,dW(s)$$

The deterministic integral:

$$\theta\mu \int_t^{t+\Delta t} e^{\theta s}\,ds = \theta\mu \cdot \frac{e^{\theta(t+\Delta t)} - e^{\theta t}}{\theta} = \mu(e^{\theta(t+\Delta t)} - e^{\theta t})$$

**Step 2 — Recover X(t+Δt).**

Since Y(t+Δt) = e^(θ(t+Δt)) X(t+Δt) and Y(t) = e^(θt) X(t):

$$e^{\theta(t+\Delta t)} X(t+\Delta t) = e^{\theta t} X(t) + \mu(e^{\theta(t+\Delta t)} - e^{\theta t}) + \sigma \int_t^{t+\Delta t} e^{\theta s}\,dW(s)$$

Dividing by e^(θ(t+Δt)):

$$X(t+\Delta t) = e^{-\theta\Delta t} X(t) + \mu(1 - e^{-\theta\Delta t}) + \sigma \int_t^{t+\Delta t} e^{-\theta(t+\Delta t - s)}\,dW(s)$$

**Step 3 — Show the distribution is Gaussian.**

The first two terms are deterministic (given X(t)). The third term is a stochastic integral of a deterministic integrand against Brownian motion. By the fundamental property of Itô integrals, any integral ∫f(s) dW(s) with deterministic f is Gaussian with mean 0 and variance ∫f(s)² ds.

Therefore X(t+Δt) | X(t) is Gaussian (a constant plus a Gaussian random variable is Gaussian).

**Step 4 — Compute the conditional mean.**

$$E[X(t+\Delta t) | X(t)] = e^{-\theta\Delta t} X(t) + \mu(1 - e^{-\theta\Delta t})$$

This is a weighted average of X(t) and μ, with the weight on X(t) decaying exponentially as Δt grows. As Δt → ∞, the mean converges to μ.

**Step 5 — Compute the conditional variance.**

$$\text{Var}[X(t+\Delta t) | X(t)] = \sigma^2 \int_t^{t+\Delta t} e^{-2\theta(t+\Delta t - s)}\,ds$$

Substituting u = t + Δt − s, du = −ds:

$$= \sigma^2 \int_0^{\Delta t} e^{-2\theta u}\,du = \sigma^2 \left[\frac{-1}{2\theta}e^{-2\theta u}\right]_0^{\Delta t} = \frac{\sigma^2}{2\theta}(1 - e^{-2\theta\Delta t})$$

**Summary — the transition density:**

$$\boxed{X(t+\Delta t) | X(t) \sim \mathcal{N}\left(e^{-\theta\Delta t} X(t) + \mu(1-e^{-\theta\Delta t}),\; \frac{\sigma^2}{2\theta}(1 - e^{-2\theta\Delta t})\right)}$$

**Verification:** As Δt → 0: mean → X(t) (continuity), variance → σ²Δt (matches the SDE's instantaneous variance). As Δt → ∞: mean → μ, variance → σ²/(2θ) (the stationary distribution). Both limits are consistent.

**Key takeaway:** The OU transition density is Gaussian because the integrating factor technique reduces the SDE to a stochastic integral with a deterministic integrand. The conditional mean interpolates between the current value X(t) and the long-run mean μ, while the conditional variance grows from 0 toward the stationary variance σ²/(2θ).

---

### Q054 — Why Not Log-Likelihood Directly?

**Question:** Write the exact log-likelihood function for the discretized OU model. Show that maximizing it is equivalent to the OLS procedure implemented in `fit_ols()`. Under what conditions does this equivalence hold?

**Answer:**

**The conditional log-likelihood:**

Given observations z₀, z₁, ..., z_n at intervals Δt, and conditioning on z₀, the log-likelihood is:

$$\ell(a, b, \sigma_\varepsilon^2) = \sum_{i=0}^{n-1} \ln p(z_{i+1} | z_i)$$

where p(z_{i+1} | z_i) is the Gaussian transition density:

$$z_{i+1} | z_i \sim \mathcal{N}(a z_i + b, \sigma_\varepsilon^2)$$

Expanding:

$$\ell = -\frac{n}{2}\ln(2\pi) - \frac{n}{2}\ln(\sigma_\varepsilon^2) - \frac{1}{2\sigma_\varepsilon^2}\sum_{i=0}^{n-1}(z_{i+1} - a z_i - b)^2$$

**Maximizing with respect to (a, b):**

For fixed σ²_ε, the terms that depend on (a, b) are only in the last sum. Maximizing ℓ with respect to (a, b) is equivalent to minimizing:

$$Q(a, b) = \sum_{i=0}^{n-1}(z_{i+1} - a z_i - b)^2$$

This is exactly the OLS criterion for the regression z_{i+1} = a·z_i + b + ε_i. The MLE of (a, b) is identical to the OLS estimator.

**Maximizing with respect to σ²_ε:**

Taking the derivative of ℓ with respect to σ²_ε and setting to zero:

$$\frac{\partial \ell}{\partial \sigma_\varepsilon^2} = -\frac{n}{2\sigma_\varepsilon^2} + \frac{1}{2(\sigma_\varepsilon^2)^2}\sum_{i=0}^{n-1}\hat{\varepsilon}_i^2 = 0$$

$$\hat{\sigma}_{\varepsilon,\text{MLE}}^2 = \frac{1}{n}\sum_{i=0}^{n-1}\hat{\varepsilon}_i^2$$

The MLE uses denominator n, while the OLS estimator in the code uses n − 2 (unbiased). This is the only difference between the two approaches.

**When is the equivalence exact?**

The OLS estimates of (a, b) equal the MLE estimates of (a, b) when:

1. **The errors are Gaussian.** The transition density is N(az + b, σ²_ε), which holds exactly for the OU process with Brownian noise. If the noise is non-Gaussian, OLS still gives unbiased (a, b) but no longer maximizes the likelihood.

2. **The errors are homoscedastic.** σ²_ε is constant across all transitions. If σ varies with time or with the level of z (ARCH effects, stochastic volatility), the likelihood is no longer a simple sum of identical Gaussians. The MLE would weight observations differently (GLS-like), while OLS weights them equally.

3. **The errors are independent.** ε_i ⊥ ε_j for i ≠ j. This holds by the Markov property of the OU process. If there were serial correlation in the errors (model misspecification), the likelihood would not factorize, and OLS on the simple AR(1) would not maximize it.

4. **Conditioning on z₀.** The full (unconditional) likelihood includes p(z₀), the marginal density of the first observation. If z₀ is drawn from the stationary distribution: p(z₀) = N(μ, σ²/(2θ)), adding one term to the log-likelihood. This term depends on (a, b, σ²_ε) through the OU parameters. Including it slightly changes the MLE. For n ≈ 3500, this one extra term is negligible.

**The implementation's relationship to the MLE:**

`fit_ols()` computes:
- â, b̂: identical to the conditional MLE for (a, b).
- σ̂²_ε = RSS/(n − 2): differs from MLE by a factor of n/(n−2) ≈ 1.0006 for n ≈ 3500.
- θ, μ, σ are derived from (â, b̂, σ̂²_ε) via the exact inverse mapping — same mapping whether you start from OLS or MLE.

So the procedure in `fit_ols()` is *essentially* MLE, with the only difference being the bias correction in the variance estimator.

**Key takeaway:** The log-likelihood for the discretized OU model factors into a sum of Gaussian log-densities. Maximizing over (a, b) gives the OLS normal equations exactly. The equivalence holds when the transition density is Gaussian, homoscedastic, and has independent errors — all guaranteed by the OU model with Brownian noise. The code's n − 2 denominator is the only deviation from pure MLE.

---

### Q055 — Cointegration Rank

**Question:** The Johansen procedure can detect multiple cointegration relationships in a system with more than two variables. In the bivariate case used here, what are the possible cointegration ranks and what does each imply? How does the implementation extract the hedge ratio when rank = 1?

**Answer:**

**Cointegration rank in the bivariate case:**

For a bivariate system Z(t) = (X(t), Y(t))' where both components are I(1), the possible cointegration ranks are r = 0, 1, or 2:

**r = 0 — No cointegration.**
There is no stationary linear combination of X and Y. Both series wander independently (they may be correlated in returns but have no long-run equilibrium). The Π matrix in the VECM has rank 0 (Π = 0), meaning there is no error correction mechanism. The system is a VAR in first differences.

Implication: the pair is not suitable for pair trading. The spread A − β·B is non-stationary for any choice of β.

**r = 1 — One cointegrating relationship.**
There exists exactly one stationary linear combination β'Z(t) = X(t) − β·Y(t) that is I(0). The Π matrix has rank 1: Π = αβ', where β is the cointegrating vector and α is the adjustment (loading) vector. The system has an error correction representation: deviations from the long-run equilibrium β'Z are corrected over time.

Implication: the pair is cointegrated. There is a unique (up to normalization) hedge ratio β, and the spread is stationary and mean-reverting. This is the case the project targets.

**r = 2 — Both series are stationary.**
If both X and Y are individually I(0), then any linear combination is also I(0), and the cointegration rank equals the dimension of the system (2). The Π matrix has full rank. This contradicts the I(1) assumption verified in step 1 of the test battery.

Implication: both series are stationary — they should not have passed the ADF test in `auto_integration()`. If r = 2 is found, it suggests either a test inconsistency or a misspecification of the Johansen model (e.g., wrong `det_order` or `k_ar_diff`).

**How the implementation extracts the hedge ratio when r = 1:**

From `test_coint.py`, lines 56–62:

```python
result = coint_johansen(data, det_order=0, k_ar_diff=1)
v = np.real(result.evec[:, 0])   # eigenvector for largest eigenvalue
v = v / v[0]                      # normalize so v[0] = 1
spread = np.column_stack((self.x, self.y)) @ v
return spread, -v[1]
```

The `coint_johansen` function returns:
- `result.evec`: a 2×2 matrix of eigenvectors. Each column is a cointegrating vector candidate.
- `result.lr1`: trace statistics for testing rank = 0, 1.
- `result.cvt`: critical values.

The eigenvectors are ordered by eigenvalue magnitude. Column 0 corresponds to the *largest* eigenvalue — this is the most significant cointegrating relationship.

When r = 1, only the first eigenvector is meaningful. The code:
1. Takes `result.evec[:, 0]` = [v₀, v₁] — the first eigenvector.
2. Normalizes by v₀: v = [1, v₁/v₀]. This sets the coefficient on X to 1.
3. Computes spread = X·1 + Y·(v₁/v₀). Since v₁/v₀ is typically negative (say, −β), the spread is X − β·Y.
4. Returns −v[1] as the hedge ratio (since v[1] = v₁/v₀ ≈ −β, negating gives +β).

**Why `np.real()` is used:** The Johansen procedure solves a generalized eigenvalue problem that can produce complex eigenvalues/eigenvectors (depending on the numerical method). For a well-specified bivariate system, the eigenvalues should be real, but floating-point arithmetic can introduce small imaginary components. `np.real()` discards these artifacts.

**The trace test for rank selection (lines 107–110):**

```python
stat = self.Johansen_obj.lr1[0]      # trace statistic for r=0
critique = self.Johansen_obj.cvt[0,:][1]  # 95% critical value for r=0
if stat < critique:
    raise CointError(...)
```

The trace test at r = 0 tests H₀: rank ≤ 0 vs H₁: rank ≥ 1. Rejecting means at least one cointegrating relationship exists. The implementation only tests r = 0 and does not explicitly test r = 1 (H₀: rank ≤ 1 vs H₁: rank = 2). In the bivariate case, if we've confirmed both series are I(1) and the trace test rejects r = 0, we can reasonably conclude r = 1 without testing further.

**Key takeaway:** In the bivariate case, rank 0 = no cointegration, rank 1 = one cointegrating relationship (the target for pair trading), rank 2 = both series stationary (contradicts I(1) assumption). The hedge ratio is extracted from the eigenvector associated with the largest eigenvalue, normalized so the first asset has coefficient 1.

---

### Q056 — Asymptotic vs Finite-Sample Critical Values

**Question:** The ADF, KPSS, and Engle-Granger tests all use tabulated critical values. Are these exact or asymptotic? How reliable are they for the sample sizes in this project (~3500 daily observations)?

**Answer:**

**ADF critical values:**

The ADF test statistic does not follow a standard distribution under H₀ — it follows the Dickey-Fuller distribution, which depends on:
- The number of deterministic components (constant, trend).
- The sample size T.

The `adfuller` function from statsmodels uses tabulated critical values from MacKinnon (1994, 2010), which provides *response surface regressions* — parametric approximations of the finite-sample critical values as a function of T. These are:

$$c_\alpha(T) = c_\infty + c_1/T + c_2/T^2$$

where c_∞, c₁, c₂ are regression coefficients specific to each significance level α and the deterministic specification.

For T = 3500, the finite-sample adjustment is very small: c₁/3500 ≈ 0.01 in absolute terms, compared to c_∞ ≈ −2.86 for the 5% level. **The critical values are very reliable at T = 3500.**

**KPSS critical values:**

The KPSS test statistic converges to a functional of Brownian motion under H₀. The critical values are from Kwiatkowski, Phillips, Schmidt, and Shin (1992) and are **asymptotic only** — they do not have a finite-sample correction in the standard `statsmodels` implementation.

The KPSS asymptotic approximation converges relatively slowly compared to ADF. For T = 3500, the asymptotic critical values are a reasonable approximation, but there can be size distortion (the actual Type I error rate may differ from the nominal 5%). The KPSS test is known to over-reject (liberal) in moderate samples when the bandwidth parameter (number of lags in the HAC estimator) is small.

The implementation uses `regression='c'` (level stationarity), which is the standard specification. **Reliability at T = 3500: good but not exact.**

**Engle-Granger critical values:**

The `coint()` function from statsmodels uses critical values from MacKinnon (2010), similar to the ADF test but with a different distribution because the test is applied to *estimated* residuals (not raw data). The critical values account for the number of variables in the cointegrating regression and use response surface regressions with finite-sample corrections.

For the bivariate case with T = 3500, the critical values are well-approximated. **Reliability: very good.**

**Johansen trace test critical values:**

The trace statistic converges to a functional of multivariate Brownian motion. Critical values are from Osterwald-Lenum (1992) tables, which are **asymptotic**. The `coint_johansen` implementation in `statsmodels` uses tabulated values without finite-sample correction.

Johansen critical values are known to have size distortion in small samples (T < 100), where the test tends to over-reject. For T = 3500, the asymptotic approximation is excellent. The bivariate case (2 variables) is the simplest, with the least size distortion. **Reliability at T = 3500: excellent.**

**Phillips-Perron critical values:**

As discussed in Q017, the implementation incorrectly uses ADF critical values. If the correct PP critical values were used, they would come from the same Dickey-Fuller distribution family as ADF (asymptotically equivalent under the null). The `arch` library provides its own critical values via the Phillips-Perron object. **Reliability at T = 3500: excellent (if using the correct values).**

**Summary table:**

| Test | Critical values | Finite-sample correction? | Reliability at T ≈ 3500 |
|------|----------------|--------------------------|------------------------|
| ADF | MacKinnon response surface | Yes (1/T, 1/T² terms) | Excellent |
| KPSS | Asymptotic tables | No | Good (possible mild size distortion) |
| Engle-Granger | MacKinnon response surface | Yes | Very good |
| Johansen trace | Osterwald-Lenum tables | No | Excellent |
| Phillips-Perron | ADF values used (BUG) | N/A | Invalid (see Q017) |

**General assessment:** For T ≈ 3500, all tests are well within the regime where asymptotic approximations are reliable. The primary concern is not the critical values themselves but rather:
- The power of the tests (ability to detect near-unit-root alternatives).
- The sensitivity to lag selection (ADF, PP) and bandwidth selection (KPSS).
- The multiple-testing issue across pairs (Q019).

Finite-sample corrections matter primarily for T < 100. At T = 3500, the distinction between exact and asymptotic critical values is negligible — the real challenge is model specification, not distribution theory.

**Key takeaway:** The critical values are asymptotic (with finite-sample corrections for ADF and Engle-Granger). At T ≈ 3500, they are highly reliable — the error from using asymptotic instead of exact critical values is negligible. The practical concerns at this sample size are test power and specification choices, not critical value accuracy.

# Strategy and Interview Master Guide

## What the project does

**30-second explanation:** I built a modular Python research platform that downloads OHLCV data, computes RSI, Bollinger Bands, and moving-average features, generates configurable long-only signals, and backtests them with next-bar execution, costs, drawdown, Sharpe estimates, and a buy-and-hold benchmark. Streamlit exposes the parameters and Plotly displays the resulting evidence.

**Two-minute explanation:** The data layer validates dates, symbols, columns, duplicates, and missing values before returning a clean frame. The indicator layer computes Wilder RSI, rolling Bollinger statistics, and SMA/EMA features without TA-Lib. The strategy layer turns those features into explicit entry and exit events and maintains a deterministic 0/1 position state. The engine shifts that state by one bar so a closing signal cannot earn the same bar's return, applies proportional trading costs, constructs equity and trade-ledger series, and compares the result with buy-and-hold. Metrics are calculated from those series, not from display code. Tests use synthetic data so unit validation is offline and repeatable.

## Component defense

1. **Why RSI?** It summarizes recent directional momentum on a 0-100 scale and can identify unusually weak or strong moves. Fourteen periods is a common convention, not a universal optimum. RSI can stay extreme in a strong trend, so it should not be treated as an automatic reversal oracle.
2. **Why Bollinger Bands?** They express distance from a rolling mean in volatility-adjusted units. A price touching a band is context, not proof of reversal.
3. **Why moving averages?** They smooth noise and provide a simple trend filter. A short average above a long average indicates recent prices are stronger than the longer baseline.
4. **Why combine them?** RSI and bands describe potential mean-reversion context; the MA filter avoids taking every counter-trend signal. Combining rules is still a hypothesis and requires out-of-sample testing.
5. **What is mean reversion?** The hypothesis that unusually displaced prices may move back toward a reference level. It fails when the reference level or regime changes.
6. **What is a crossover?** A state transition where the short MA moves from below to above, or above to below, the long MA.

## Mathematics and implementation

For price change $\Delta P_t$, gain is $\max(\Delta P_t,0)$ and loss is $\max(-\Delta P_t,0)$. Wilder smoothing uses an exponential weighting with $\alpha = 1/n$. Then $RS = \overline{gain}/\overline{loss}$ and $RSI = 100 - 100/(1+RS)$. Initial observations remain unavailable until enough history exists; division-by-zero cases are bounded at 0 or 100.

For period $n$ and multiplier $k$, $M_t$ is the rolling mean and $\sigma_t$ is rolling standard deviation. The bands are $U_t=M_t+k\sigma_t$ and $L_t=M_t-k\sigma_t$. The implementation also exposes band width and percent-B.

For each bar, the engine calculates close-to-close market return $r_t=P_t/P_{t-1}-1$. The strategy return is held position times $r_t$ minus turnover times the combined transaction-cost/slippage rate. Portfolio value is the cumulative product of one plus those net returns.

Drawdown is $D_t=E_t/\max_{s\le t}(E_s)-1$. Maximum drawdown is $\min(D_t)$. The annualized Sharpe estimate is $\sqrt{252}\,\bar{x}/s_x$, where $x$ is the daily return less the daily risk-free rate. It is an estimate, not a guarantee of risk-adjusted future performance.

Win rate is winning closed trades divided by closed trades. Open trades are not counted in the win rate. Buy-and-hold uses the same initial capital and period so active performance has a meaningful baseline.

## Biases and assumptions

- **Look-ahead bias:** prevented by shifting desired position one bar before returns are applied.
- **Data leakage:** can occur if parameters are selected using the test period; this application does not perform parameter optimization.
- **Survivorship bias:** occurs when only today's surviving assets are studied; the user must construct a historical universe separately.
- **Overfitting:** too many tuned parameters can describe noise rather than signal. Use walk-forward and out-of-sample tests.
- **Slippage:** the difference between modeled and executable price; the UI has a proportional approximation.
- **Costs:** charged on entry and exit turnover, so gross returns are not presented as net performance.
- **Execution:** the reference implementation uses the next bar's close as the first held-return bar. It is intentionally explicit and conservative about signal timing, but not a full order-book simulator.

## 30 technical questions and answers

1. **What is RSI?** A smoothed ratio of recent gains to losses mapped to 0-100.
2. **Why Wilder smoothing?** It reduces noise and matches the standard RSI convention.
3. **What happens when average loss is zero?** RSI is set to 100 when gains exist.
4. **What do bands measure?** A rolling mean plus or minus a volatility-scaled distance.
5. **Why use `ddof=0`?** It treats the rolling window as the observed population for a stable descriptive band.
6. **What is an SMA?** The arithmetic mean of the last `n` closes.
7. **What is an EMA?** A weighted average that emphasizes recent observations.
8. **Why a trend filter?** To reduce counter-trend entries, at the cost of fewer trades.
9. **What is a signal?** An observation at a timestamp, distinct from the held position.
10. **How is re-entry prevented?** The state machine only enters when flat and exits when long.
11. **How is look-ahead avoided?** Position state is shifted one bar before strategy returns.
12. **How are costs modeled?** Turnover times a configurable proportional rate.
13. **What is exposure?** Average held-position value, expressed here as a fraction of bars.
14. **What is drawdown?** Percentage decline from the running equity peak.
15. **What is Sharpe?** Return per unit of return volatility after a risk-free adjustment.
16. **Why annualize by 252?** It approximates US equity trading days for daily data.
17. **What is a benchmark?** A passive reference series, here buy-and-hold.
18. **Why test synthetic data?** It makes expected behavior deterministic and offline.
19. **Why cache downloads?** To reduce repeated network calls during UI reruns.
20. **What is a zero-trade result?** A valid result with zero win rate and no trade-derived statistics.
21. **What is a zero-volatility Sharpe?** Undefined, so the implementation returns zero.
22. **Why validate missing volume?** OHLCV is the declared contract even if this strategy does not use volume.
23. **Why can RSI fail in trends?** Momentum can stay extreme while price continues in one direction.
24. **Why compare buy-and-hold?** Absolute profit alone does not establish incremental value.
25. **What is CAGR?** The constant annual rate producing the observed total return over elapsed time.
26. **What is profit factor?** Gross winning trade return divided by gross losing trade magnitude.
27. **What is slippage?** Execution friction between intended and realized price.
28. **What would validate robustness?** Walk-forward splits, parameter sensitivity, and multiple regimes.
29. **What is not implemented?** Live orders, leverage, broker credentials, and portfolio optimization.
30. **What is the most important caveat?** Historical simulation is conditional evidence, not a forecast.

## Follow-ups and strong responses

- **Why close execution?** It makes the timing rule easy to audit; I would add an explicit next-open model for production research.
- **How would you improve risk?** Add volatility targeting, stop policy research, and portfolio-level constraints, then test those choices out of sample.
- **How would you handle multiple assets?** Allocate from a shared portfolio rather than independently resetting capital per ticker.
- **How would you prevent overfitting?** Freeze a validation period, limit degrees of freedom, and report sensitivity rather than one chosen parameter set.
- **Would you trade this live?** No. I would first validate data quality, corporate actions, execution assumptions, operational monitoring, and independent out-of-sample evidence.

## Common mistakes to avoid

Do not say RSI predicts reversals, that a positive backtest proves profitability, that Sharpe is a guarantee, or that a high win rate alone means a strategy is good. Do not hide costs, select parameters on the same period used for evaluation, or claim the dashboard executes trades.
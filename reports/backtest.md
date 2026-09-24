# Backtest Report

Status: backtest and risk engine implemented, not yet populated with live strategy outputs.

Implemented scope:
- Point-in-time safe signal entry after `known_at`.
- Long-only trade generation.
- Horizon-based exit at close.
- Configured trading cost and slippage deduction.
- Signal count and tradable trade count summary.
- XU100 benchmark return hook.
- Sector benchmark return hook.
- Buy-and-hold comparison hook.
- Cumulative return, Sharpe ratio, maximum drawdown, win rate and benchmark difference.

Current output note:
- No measured backtest result is reported here yet.
- Use `run_backtest` with verified signal records and cached market data to generate trade-level outputs.

Limitations:
- Sharpe ratio is calculated on trade-level cost-adjusted returns, not daily portfolio returns.
- Live/cache market data and verified strategy signal records are still required before measured results can be reported.
- This report is historical research infrastructure, not investment advice.

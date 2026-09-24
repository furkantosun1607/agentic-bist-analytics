# Backtest Report

Status: backtest engine implemented, not yet populated with live strategy outputs.

Implemented scope:
- Point-in-time safe signal entry after `known_at`.
- Long-only trade generation.
- Horizon-based exit at close.
- Signal count and tradable trade count summary.
- XU100 benchmark return hook.
- Sector benchmark return hook.
- Buy-and-hold comparison hook.

Current output note:
- No measured backtest result is reported here yet.
- Use `run_backtest` with verified signal records and cached market data to generate trade-level outputs.

Limitations:
- P13 does not calculate transaction costs, slippage, Sharpe ratio, maximum drawdown or win rate.
- P14 adds realistic costs and risk metrics.
- This report is historical research infrastructure, not investment advice.

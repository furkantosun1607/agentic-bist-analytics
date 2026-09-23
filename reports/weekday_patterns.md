# Weekday And Multi-Day Pattern Report

Status: implemented, not yet run on a live cached market dataset.

Method:
- Predefined weekday tests use one-trading-day forward returns from each weekday.
- Multi-day tests use two-to-five-trading-day forward returns.
- Unconditional returns are calculated for the same holding period as the baseline.
- Trading cost and slippage are deducted from gross returns.
- Market regime labels are based on benchmark return when benchmark data is supplied.
- Selection versus unseen split support is implemented through `unseen_start_date`.

Current output note:
- No measured result is reported here yet because live/cache market data has not been generated in the repository.
- Use `run_weekday_patterns` and `write_weekday_patterns_report` after market cache generation to produce measured observations.

Limitations:
- Calendar effects are vulnerable to multiple testing.
- This report is historical research infrastructure, not investment advice.

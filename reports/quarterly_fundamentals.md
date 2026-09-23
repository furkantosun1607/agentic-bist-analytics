# Quarterly Fundamentals Report

Status: implemented, not yet run on a live or manually verified fundamentals dataset.

Method:
- `period_end` is the accounting observation period.
- `disclosure_timestamp` is the signal timestamp and must be public before any post-disclosure return is measured.
- Entry is no earlier than the next available trading day after disclosure.
- Forward horizons are 1, 5 and 20 trading days.
- Industrial records use revenue, profit, margin, debt and cash-flow metrics.
- Bank records use bank-appropriate metrics such as net interest income, net income, assets/equity and liabilities/assets.
- Returns are compared against benchmark return and same-sector peer median return when available.

Current output note:
- No measured result is reported here yet because verified fundamentals and market cache data have not been generated in the repository.
- Use `normalize_fundamentals`, `run_quarterly_fundamentals` and `write_quarterly_fundamentals_report` after source verification to produce measured observations.

Limitations:
- Fintables access and licensing must be verified before source data is imported.
- This report is historical research infrastructure, not investment advice.

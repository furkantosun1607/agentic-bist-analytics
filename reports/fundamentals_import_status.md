# Fundamentals Import Status

Status: `ready`

Expected local CSV: `data\fundamentals\fundamentals.csv`
Schema template: `config\fundamentals_template.csv`
Valid rows: 160
Import errors: 0
Universe ticker coverage: 30
Point-in-time gate: `ANALYSIS_SAFE`

## Current Source Decision

- Local source is the instructor-approved yfinance fallback, written to `data/fundamentals/fundamentals.csv`.
- Treat synthetic disclosure timestamps as conservative project assumptions, not exact KAP publication times.
- If no valid CSV is available in a future run, quarterly fundamentals must remain `inconclusive`.

## Coverage

| Ticker | Profile | Records | First period | Latest period | Latest disclosure | Populated numeric fields |
| --- | --- | ---: | --- | --- | --- | --- |
| AKBNK | bank | 6 | 2025-03-31 | 2026-06-30 | 2026-08-09T15:30:00+00:00 | revenue, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, operating_cash_flow, free_cash_flow |
| AKSEN | industrial | 5 | 2025-06-30 | 2026-06-30 | 2026-08-09T15:30:00+00:00 | revenue, gross_profit, operating_profit, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, operating_cash_flow, free_cash_flow |
| ARCLK | industrial | 6 | 2025-03-31 | 2026-06-30 | 2026-08-09T15:30:00+00:00 | revenue, gross_profit, operating_profit, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, operating_cash_flow, free_cash_flow |
| ASELS | industrial | 6 | 2025-03-31 | 2026-06-30 | 2026-08-09T15:30:00+00:00 | revenue, gross_profit, operating_profit, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, operating_cash_flow, free_cash_flow |
| BIMAS | industrial | 5 | 2025-06-30 | 2026-06-30 | 2026-08-09T15:30:00+00:00 | revenue, gross_profit, operating_profit, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, operating_cash_flow, free_cash_flow |
| CCOLA | industrial | 5 | 2025-06-30 | 2026-06-30 | 2026-08-09T15:30:00+00:00 | revenue, gross_profit, operating_profit, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, operating_cash_flow, free_cash_flow |
| ECILC | industrial | 5 | 2025-06-30 | 2026-06-30 | 2026-08-09T15:30:00+00:00 | revenue, gross_profit, operating_profit, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, operating_cash_flow, free_cash_flow |
| EKGYO | industrial | 5 | 2025-06-30 | 2026-06-30 | 2026-08-09T15:30:00+00:00 | revenue, gross_profit, operating_profit, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, operating_cash_flow, free_cash_flow |
| ENJSA | industrial | 7 | 2024-12-31 | 2026-06-30 | 2026-08-09T15:30:00+00:00 | revenue, gross_profit, operating_profit, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, operating_cash_flow, free_cash_flow |
| ENKAI | industrial | 5 | 2025-06-30 | 2026-06-30 | 2026-08-09T15:30:00+00:00 | revenue, gross_profit, operating_profit, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, operating_cash_flow, free_cash_flow |
| EREGL | industrial | 6 | 2025-03-31 | 2026-06-30 | 2026-08-09T15:30:00+00:00 | revenue, gross_profit, operating_profit, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, operating_cash_flow, free_cash_flow |
| FROTO | industrial | 6 | 2025-03-31 | 2026-06-30 | 2026-08-09T15:30:00+00:00 | revenue, gross_profit, operating_profit, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, operating_cash_flow, free_cash_flow |
| GUBRF | industrial | 5 | 2025-03-31 | 2026-03-31 | 2026-05-10T15:30:00+00:00 | revenue, gross_profit, operating_profit, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, operating_cash_flow, free_cash_flow |
| ISMEN | industrial | 5 | 2025-06-30 | 2026-06-30 | 2026-08-09T15:30:00+00:00 | revenue, gross_profit, operating_profit, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, operating_cash_flow, free_cash_flow |
| KCHOL | industrial | 5 | 2025-06-30 | 2026-06-30 | 2026-08-09T15:30:00+00:00 | revenue, gross_profit, operating_profit, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, operating_cash_flow, free_cash_flow |
| KRDMD | industrial | 5 | 2025-06-30 | 2026-06-30 | 2026-08-09T15:30:00+00:00 | revenue, gross_profit, operating_profit, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, operating_cash_flow, free_cash_flow |
| MAVI | industrial | 5 | 2025-07-31 | 2026-07-31 | 2026-09-09T15:30:00+00:00 | revenue, gross_profit, operating_profit, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, operating_cash_flow, free_cash_flow |
| MGROS | industrial | 5 | 2025-06-30 | 2026-06-30 | 2026-08-09T15:30:00+00:00 | revenue, gross_profit, operating_profit, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, operating_cash_flow, free_cash_flow |
| MPARK | industrial | 6 | 2025-03-31 | 2026-06-30 | 2026-08-09T15:30:00+00:00 | revenue, gross_profit, operating_profit, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, operating_cash_flow, free_cash_flow |
| OYAKC | industrial | 5 | 2025-06-30 | 2026-06-30 | 2026-08-09T15:30:00+00:00 | revenue, gross_profit, operating_profit, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, operating_cash_flow, free_cash_flow |
| PETKM | industrial | 5 | 2025-06-30 | 2026-06-30 | 2026-08-09T15:30:00+00:00 | revenue, gross_profit, operating_profit, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, operating_cash_flow, free_cash_flow |
| PGSUS | industrial | 5 | 2025-06-30 | 2026-06-30 | 2026-08-09T15:30:00+00:00 | revenue, gross_profit, operating_profit, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, operating_cash_flow, free_cash_flow |
| SASA | industrial | 6 | 2025-03-31 | 2026-06-30 | 2026-08-09T15:30:00+00:00 | revenue, gross_profit, operating_profit, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, operating_cash_flow, free_cash_flow |
| TCELL | industrial | 5 | 2025-03-31 | 2026-06-30 | 2026-08-09T15:30:00+00:00 | revenue, gross_profit, operating_profit, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, operating_cash_flow, free_cash_flow |
| THYAO | industrial | 5 | 2025-06-30 | 2026-06-30 | 2026-08-09T15:30:00+00:00 | revenue, gross_profit, operating_profit, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, operating_cash_flow, free_cash_flow |
| TOASO | industrial | 5 | 2025-06-30 | 2026-06-30 | 2026-08-09T15:30:00+00:00 | revenue, gross_profit, operating_profit, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, operating_cash_flow, free_cash_flow |
| TRALT | industrial | 5 | 2025-06-30 | 2026-06-30 | 2026-08-09T15:30:00+00:00 | revenue, gross_profit, operating_profit, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, operating_cash_flow, free_cash_flow |
| TTKOM | industrial | 6 | 2025-03-31 | 2026-06-30 | 2026-08-09T15:30:00+00:00 | revenue, gross_profit, operating_profit, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, operating_cash_flow, free_cash_flow |
| TUPRS | industrial | 5 | 2025-06-30 | 2026-06-30 | 2026-08-09T15:30:00+00:00 | revenue, gross_profit, operating_profit, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, operating_cash_flow, free_cash_flow |
| TURSG | industrial | 5 | 2025-06-30 | 2026-06-30 | 2026-08-09T15:30:00+00:00 | revenue, net_income, net_interest_income, total_assets, total_liabilities, total_equity, total_debt, cash_and_equivalents, free_cash_flow |

Limitations:
- Fundamentals data is an external source artifact and is not committed.
- Current yfinance fallback uses synthetic disclosure timestamps: period_end plus the configured conservative lag.
- This report does not create measured quarterly findings by itself.

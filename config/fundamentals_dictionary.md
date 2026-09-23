# Fundamentals Data Dictionary

`src.fundamentals` normalizes manually prepared or source-exported quarterly/annual records into a point-in-time schema.

Required columns:
- `ticker`: fixed-universe ticker.
- `period_end`: accounting observation period end date.
- `period_type`: `quarterly` or `annual`.
- `disclosure_timestamp`: public disclosure timestamp. A quarter-end date is not enough.
- `download_timestamp`: timestamp when the record was collected.
- `source`: data source name or URL label.

Generated columns:
- `yahoo_symbol`: fixed-universe Yahoo symbol.
- `sector`: fixed-universe simplified sector.
- `metric_profile`: `bank` for banking names, otherwise `industrial`.

Optional numeric columns:
- `revenue`
- `gross_profit`
- `operating_profit`
- `net_income`
- `net_interest_income`
- `total_assets`
- `total_liabilities`
- `total_equity`
- `total_debt`
- `cash_and_equivalents`
- `operating_cash_flow`
- `free_cash_flow`

Rules:
- Keep `period_end`, `disclosure_timestamp`, and `download_timestamp` separate.
- Missing disclosure timestamps are rejected by import helpers because they cannot support point-in-time analysis.
- Bank records should use bank-appropriate metrics such as `net_interest_income`; industrial records should not be blindly evaluated with banking metrics.

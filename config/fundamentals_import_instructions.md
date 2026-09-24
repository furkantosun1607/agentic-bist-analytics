# Fundamentals Import Instructions

Status: external fundamentals data is not committed. Fintables Pro access is not assumed; the current project decision is to use the instructor-approved Yahoo Finance / yfinance fallback and run the status command before using quarterly fundamentals in measured reports.

## Source Decision

Current decision before P34 quarterly fundamentals can produce measured findings:

1. Use `python -m scripts.fetch_yfinance_fundamentals` to fetch quarterly statement fields from yfinance.
2. Use synthetic disclosure timestamps: `period_end + 40 days at 18:30 Europe/Istanbul`.
3. If yfinance returns no usable rows for a symbol, the status report keeps that gap visible.

Manual CSV preparation remains allowed only if it uses the same schema and source/timestamp assumptions are documented. If no valid local CSV is available, quarterly fundamentals must remain explicit `inconclusive`.

## Local File Path

Place the prepared CSV here:

```text
data/fundamentals/fundamentals.csv
```

This directory is ignored by git because the data may be licensed or too large for the repository.

Generate it with:

```powershell
python -m scripts.fetch_yfinance_fundamentals
```

## Required Columns

Use the schema in `config/fundamentals_template.csv`:

```text
ticker,yahoo_symbol,sector,metric_profile,period_end,period_type,disclosure_timestamp,download_timestamp,source,currency,revenue,gross_profit,operating_profit,net_income,net_interest_income,total_assets,total_liabilities,total_equity,total_debt,cash_and_equivalents,operating_cash_flow,free_cash_flow
```

Required fields:
- `ticker`
- `period_end`
- `period_type`
- `disclosure_timestamp`
- `download_timestamp`
- `source`

`yahoo_symbol`, `sector` and `metric_profile` are normalized from `config/universe.csv`; they do not need to be manually trusted from the export.

## Timestamp Rules

- `period_end` is the accounting period end.
- `disclosure_timestamp` is synthetic in the yfinance fallback: `period_end + 40 days at 18:30 Europe/Istanbul`.
- `download_timestamp` is when the record was collected.
- Do not use quarter-end date as the signal date.
- Do not present the synthetic timestamp as an exact KAP publication timestamp.

## Metric Notes

- Banking rows should include bank-appropriate metrics such as `net_interest_income`, assets, liabilities and equity.
- Industrial rows should include revenue/profit/margin/debt/cash-flow fields when available.
- Missing optional metrics are allowed, but coverage will be reported.

## Validation Command

```powershell
python -m scripts.audit_fundamentals_import
```

The command writes:

```text
reports/fundamentals_import_status.md
```

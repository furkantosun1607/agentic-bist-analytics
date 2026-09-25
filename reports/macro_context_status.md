# Macro Context Status

Status: `ready`

Expected local CSV: `data\macro\macro_context.csv`
Schema template: `config\context_template.csv`
Valid macro rows: 1421
Import errors: 0
Required indicators: usd_try, eur_try, tcmb_policy_rate, tuik_inflation, fed_policy_rate
Missing indicators: none
Point-in-time gate: `ANALYSIS_SAFE`

## Current Source Decision

- Local source is `data/macro/macro_context.csv`, generated from yfinance FX plus static curated TCMB/TUIK/FED records.
- Include publication timestamps; observed period dates alone are not enough for point-in-time analysis.
- If an indicator cannot be sourced, keep it visible as a source gap instead of inventing values.

## Coverage

| Indicator | Records | First observed | Latest observed | Latest publication | Sources | Access |
| --- | ---: | --- | --- | --- | --- | --- |
| eur_try | 709 | 2024-01-01 | 2026-09-24 | 2026-09-25T06:00:00+00:00 | yahoo_finance_fx | public |
| fed_policy_rate | 1 | 2026-09-16 | 2026-09-16 | 2026-09-16T18:00:00+00:00 | federal_reserve_fomc_statement | public |
| tcmb_policy_rate | 1 | 2026-09-10 | 2026-09-10 | 2026-09-10T11:00:00+00:00 | tcmb_press_release | public |
| tuik_inflation | 1 | 2026-08-31 | 2026-08-31 | 2026-09-03T07:00:00+00:00 | tuik_cpi_release | public |
| usd_try | 709 | 2024-01-01 | 2026-09-24 | 2026-09-25T06:00:00+00:00 | yahoo_finance_fx | public |

Limitations:
- Macro source exports are local artifacts and are not committed.
- TCMB/TUIK/FED records are static curated project inputs, not live API pulls.
- RSS macro alias context does not replace numeric macro records.
- This report does not create measured macro findings by itself.

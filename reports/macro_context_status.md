# Macro Context Status

Status: `blocked_missing_macro_context_csv`

Expected local CSV: `data\macro\macro_context.csv`
Schema template: `config\context_template.csv`
Valid macro rows: 0
Import errors: 0
Required indicators: usd_try, eur_try, tcmb_policy_rate, tuik_inflation, fed_policy_rate
Missing indicators: usd_try, eur_try, tcmb_policy_rate, tuik_inflation, fed_policy_rate
Point-in-time gate: `not_run`

## User Action

- Provide `data/macro/macro_context.csv` in the shared context schema, or approve automated fetching where source access allows it.
- Include publication timestamps; observed period dates alone are not enough for point-in-time analysis.
- If an indicator cannot be sourced, keep it visible as a source gap instead of inventing values.

## Coverage

| Indicator | Records | First observed | Latest observed | Latest publication | Sources | Access |
| --- | ---: | --- | --- | --- | --- | --- |
| n/a | 0 | n/a | n/a | n/a | none | none |

Limitations:
- Macro source exports are local artifacts and are not committed.
- RSS macro alias context does not replace numeric macro records.
- This report does not create measured macro findings by itself.

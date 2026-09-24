# Macro Context Import Instructions

Status: external macro data is not committed. Prepare a local CSV export and run the status command before macro context is used in measured reports.

## Required Indicators

P33 tracks these macro indicators:

- `usd_try`
- `eur_try`
- `tcmb_policy_rate`
- `tuik_inflation`
- `fed_policy_rate`

## Local File Path

Place the prepared CSV here:

```text
data/macro/macro_context.csv
```

This directory is ignored by git because macro source exports are local artifacts.

## Required Schema

Use the shared context schema in `config/context_template.csv`:

```text
context_id,context_type,scope,ticker,sector,indicator,value,unit,observed_period_start,observed_period_end,publication_timestamp,download_timestamp,source,source_url,source_access,title,claim,video_timestamp,notes
```

Required macro fields:

- `context_id`
- `context_type`: `macro`
- `scope`: usually `macro` or `global`
- `indicator`: one of the required indicator ids above
- `value`: numeric value
- `unit`: `TRY`, `%`, or another explicit unit
- `observed_period_start`
- `observed_period_end`
- `publication_timestamp`
- `download_timestamp`
- `source`
- `source_url`
- `source_access`: `public`, `licensed`, or `instructor_approved`

## Source Notes

- `usd_try`, `eur_try`, `tcmb_policy_rate`: TCMB/EVDS or another public TCMB source.
- `tuik_inflation`: TUIK publication.
- `fed_policy_rate`: Federal Reserve/FRED or another public Fed source.

If automated access fails or requires credentials, keep the CSV workflow and document the source gap in `reports/macro_context_status.md`.

## Timestamp Rules

- `observed_period_end` is the period the macro value describes.
- `publication_timestamp` is when the value became public.
- `download_timestamp` is when the row was collected.
- Do not use a macro value before `publication_timestamp`.

## Validation Command

```powershell
python -m scripts.audit_macro_context
```

The command writes:

```text
reports/macro_context_status.md
```

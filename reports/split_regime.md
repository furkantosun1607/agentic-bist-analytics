# Unseen Period And Regime Split Report

Status: split/regime helpers implemented, not yet populated with live strategy outputs.

Implemented scope:
- Selection vs unseen period labels.
- Full-sample label when no unseen start date is configured.
- Rising/falling/unknown market-regime labels from benchmark history.
- Stability comparison outputs for predefined strategy or signal groups.

Current output note:
- No measured stability comparison is reported here yet.
- `experiment.unseen_start_date` is intentionally unset until verified data coverage is known.

Limitations:
- Unseen period start date must be fixed before strategy selection.
- Regime labels depend on benchmark availability and configured lookback.
- This report is historical research infrastructure, not investment advice.

# Harness State Machine

Status: state order and permitted tool enforcement implemented.

State order:
1. `select_universe`
2. `load_validate`
3. `run_analyses`
4. `add_context`
5. `build_evidence`
6. `compare_variants`
7. `backtest`
8. `risk_gate`
9. `explain`
10. `human_review`
11. `save_decision`

Educational output labels:
- `WATCH`
- `INVESTIGATE`
- `POTENTIAL_CATCH_UP_CANDIDATE`
- `REJECT_SIGNAL`
- `ANALYSIS_UNSAFE`

Implemented behavior:
- Tools are callable only in explicitly permitted states.
- Out-of-order state completion is blocked with structured errors.
- Output labels are restricted to the educational label set.
- Decisions cannot be saved before output labeling and human review.
- Harness events are recorded in a replay-friendly event log.

Limitations:
- P18 will add stricter evidence and quality gate semantics.
- P19 will add persistent replayable decision logs.
- This report is historical research infrastructure, not investment advice.

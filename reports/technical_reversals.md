# Technical Reversal Report

Status: implemented, not yet run on a live cached market dataset.

Method:
- Technical events come from deterministic event detectors.
- Each event becomes tradable no earlier than the next available trading day.
- Forward returns are measured over 1, 3, 5 and 10 trading days.
- Bounce means the forward return is positive.
- Multiple same-symbol same-date events are also evaluated as a separate `combined` signal.
- Market regime labels are based on benchmark return when benchmark data is supplied.

Current output note:
- No measured result is reported here yet because live/cache market data has not been generated in the repository.
- Use `detect_all_events`, `run_technical_reversals` and `write_technical_reversals_report` after market cache generation to produce measured observations.

Limitations:
- Event definitions are intentionally simple and are not optimized.
- This report is historical research infrastructure, not investment advice.

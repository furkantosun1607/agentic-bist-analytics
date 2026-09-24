# Report Index

This index tracks report readiness and prevents unverified data from being presented as measured output.

| Report | Status | Data period | Source | Sample size | Assumptions | Limitations |
| --- | --- | --- | --- | --- | --- | --- |
| Sector catch-up | infrastructure_ready_no_measured_result | not available until market cache is generated | Yahoo Finance/yfinance cache planned | not measured | 20-day lookback, 5/10/20-day horizons, same-sector self-excluding peers | live/cache market data is not committed |
| Weekday and multi-day patterns | infrastructure_ready_no_measured_result | not available until market cache is generated | Yahoo Finance/yfinance cache planned | not measured | 1-5 trading-day holds, configured costs/slippage, optional regime split | multiple-testing risk and no live/cache market data yet |
| Technical reversals | infrastructure_ready_no_measured_result | not available until market cache is generated | deterministic indicators/events from cached OHLCV planned | not measured | 1/3/5/10-day post-event returns, combined same-day signals | event rules are simple and no live/cache market data yet |
| Quarterly fundamentals | infrastructure_ready_no_measured_result | not available until verified disclosures and market cache are generated | Fintables source planned, access/licensing pending verification | not measured | post-disclosure entry, bank/industrial metric separation | verified fundamentals data is not committed |
| Macro/news/video context | schema_ready_no_live_context | not populated | TCMB/EVDS, TUIK, Federal Reserve, legal news, instructor-approved video planned | 0 verified live context records committed | source_access and publication/download timestamps required | source access and licensing still need verification |
| Backtest and risk | engine_ready_no_measured_result | not available until verified signals and market cache are generated | verified signal records and cached OHLCV planned | not measured | next-trading-day entry, horizon close exit, 10 bps cost, 5 bps slippage | trade-level Sharpe only; no live strategy outputs yet |
| Unseen period and regime split | helpers_ready_no_measured_result | unseen_start_date not fixed | benchmark price history planned | not measured | benchmark-based rising/falling regime labels | unseen date waits for verified data coverage |
| Strategy variants A-E | engine_ready_no_measured_result | not available until verified strategy signals are generated | technical, sector, fundamentals, macro and verified context signals planned | not measured | same data period and costs across A-E | missing-source variants are unavailable, not inferred |
| Harness variants A-E | engine_ready_no_live_llm_run | fixed question set not finalized | deterministic capability comparison | synthetic unit-test questions only | compares harness capabilities, not financial returns | no live LLM run is reported |
| Decision log | schema_ready_no_live_decision | not applicable | harness snapshot, tool outputs and quality gate payloads | 0 live reviewed decisions committed | JSONL records require output label, review and evidence hash | unit tests use synthetic records only |

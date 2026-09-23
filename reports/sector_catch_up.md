# Sector Catch-Up Report

Status: implemented, not yet run on a live cached market dataset.

Method:
- Lookback window: 20 trading days.
- Signal: stock return minus same-sector peer median return.
- Peer rule: same simplified sector, excluding the stock itself.
- Forward horizons: 5, 10 and 20 trading days.
- Single-stock sectors are marked as `insufficient_peers`.

Current output note:
- No measured result is reported here yet because live/cache market data has not been generated in the repository.
- Use `run_sector_catch_up` and `write_sector_catch_up_report` after market cache generation to produce measured observations.

Limitations:
- This report is historical research infrastructure, not investment advice.
- Fundamental, macro, news and video context are added in later phases.

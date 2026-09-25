# Sector Catch-Up Report

Lookback window: 20 trading days.
Signals: laggards are rows where stock lookback return is below eligible peer median.
Peer rule: same simplified sector, excluding the stock itself.

Data period: 2021-01-04 to 2026-09-24.
Observation rows: 129192.
Symbols: 30.

## Status Counts

| status                            |   count |
|:----------------------------------|--------:|
| insufficient_peers                |   75822 |
| ok                                |   50520 |
| insufficient_history              |    1800 |
| insufficient_forward_history      |     630 |
| insufficient_peer_forward_history |     420 |

## Laggard Outcomes

|   horizon |   observations |   average_future_relative_return |   median_future_relative_return |   false_positives |
|----------:|---------------:|---------------------------------:|--------------------------------:|------------------:|
|         5 |           8459 |                     -0.00126684  |                     -0.00131529 |              4319 |
|        10 |           8429 |                     -0.0024266   |                     -0.00271938 |              4368 |
|        20 |           8369 |                     -0.000977136 |                     -0.0023652  |              4277 |

Limitations:
- This report is historical research output, not investment advice.
- Results depend on cached price histories and fixed universe sector labels.
- Fundamental, macro, news and video context are added in later phases.

## Run Metadata

- Data source: local Yahoo Finance/yfinance market cache.
- Assumptions: 20-day lookback; 5/10/20-day horizons; same-sector self-excluding peers.
- Context note: Fundamentals, macro and RSS context are available as separate evidence metadata and are not used to compute this signal.

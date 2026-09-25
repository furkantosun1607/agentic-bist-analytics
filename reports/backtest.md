# Backtest Report

Timing: signals are entered on the first trading day after `known_at` and exited at the configured horizon close.
Scope: trade generation, configured costs, benchmark hooks and risk metrics.

Signal rows: 25819.
Tradable rows: 25813.
Symbols: 30.

## Status Counts

| status                       |   count |
|:-----------------------------|--------:|
| ok                           |   25813 |
| insufficient_forward_history |       6 |

## Summary

| status   |   signal_count |   trade_count |   symbol_count |   average_gross_return |   median_gross_return |   average_cost_adjusted_return |   median_cost_adjusted_return |   cumulative_return |   sharpe_ratio |   maximum_drawdown |   win_rate |   cumulative_benchmark_return |   benchmark_difference |   average_benchmark_relative_return |   average_sector_relative_return |
|:---------|---------------:|--------------:|---------------:|-----------------------:|----------------------:|-------------------------------:|------------------------------:|--------------------:|---------------:|-------------------:|-----------:|------------------------------:|-----------------------:|------------------------------------:|---------------------------------:|
| ok       |          25819 |         25813 |             30 |             0.00695121 |            0.00402145 |                     0.00545121 |                    0.00252145 |         3.74944e+34 |        12.7844 |                 -1 |   0.517375 |                   1.97493e+80 |           -1.97493e+80 |                         -0.00101193 |                              nan |

Limitations:
- This report is historical research output, not investment advice.
- Sharpe ratio is calculated on trade-level cost-adjusted returns, not daily portfolio returns.
- Benchmark and sector benchmark returns are reported only when matching benchmark histories are provided.

## Measured Backtest Run

Status: measured.
Signal policy: fixed long-only signals assembled from P34 research observations without selecting on future returns.
Benchmark: `XU100.IS` local price cache.
Costs: 10.0 bps trading cost plus 5.0 bps slippage.
Primary signal horizon: 5 trading days.
Fundamentals signal horizon: 20 trading days.

## Signal Counts

| source                       |   count |
|:-----------------------------|--------:|
| technical_reversal_fixed     |    8523 |
| weekday_monday_fixed         |    8460 |
| sector_catch_up_laggard      |    8459 |
| fundamentals_positive_change |     377 |

Backtest limitations:
- Signals are educational research candidates, not recommendations.
- Overlapping trades are summarized trade-by-trade; this is not a capital-constrained portfolio simulation.
- Strategy selection, unseen-period validation and A-E strategy comparison are handled in later phases.

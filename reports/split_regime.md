# Unseen Period And Regime Split Report

Status: measured.
Unseen start date: `2025-10-01`.
Regime benchmark: `XU100.IS` with 20-trading-day lookback.
Split policy: `known_at` decision dates before the unseen start are selection rows; later dates are unseen rows.

Trade rows: 25813.
Signal date period: 2021-01-29 to 2026-09-16.

## Split Counts

| period_split   |   count |
|:---------------|--------:|
| selection      |   20909 |
| unseen         |    4904 |

## Regime Counts

| period_split   | market_regime   |   trade_count |   average_return |
|:---------------|:----------------|--------------:|-----------------:|
| selection      | falling         |          8112 |      0.00900411  |
| selection      | rising          |         12726 |      0.00534879  |
| selection      | unknown         |            71 |     -0.0168922   |
| unseen         | falling         |          1710 |      0.00152806  |
| unseen         | rising          |          2893 |      0.000815057 |
| unseen         | unknown         |           301 |     -0.0138523   |

## Stability Summary

| source                       |   horizon |   selection_count |   unseen_count |   selection_average_return |   unseen_average_return |   stability_delta | stability_label   |
|:-----------------------------|----------:|------------------:|---------------:|---------------------------:|------------------------:|------------------:|:------------------|
| fundamentals_positive_change |        20 |                34 |            343 |                -0.0287028  |            -0.0182409   |        0.0104619  | stable_negative   |
| sector_catch_up_laggard      |         5 |              6989 |           1464 |                 0.00780704 |             0.000380325 |       -0.00742671 | stable_positive   |
| technical_reversal_fixed     |         5 |              6926 |           1597 |                 0.00569066 |             0.00373213  |       -0.00195853 | stable_positive   |
| weekday_monday_fixed         |         5 |              6960 |           1500 |                 0.00673989 |             0.000360689 |       -0.0063792  | stable_positive   |

Limitations:
- This report is historical research output, not investment advice.
- Selection/unseen stability is measured on fixed P35 trade-level signals, not on optimized portfolio rules.
- Regime labels depend on local benchmark cache availability and the configured lookback.
- Strategy variant comparison remains a separate later phase.

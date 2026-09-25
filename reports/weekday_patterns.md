# Weekday And Multi-Day Pattern Report

Patterns: weekday entry tests and two-to-five-trading-day holding tests.
Costs: reported with configured trading cost and slippage deducted from gross returns.
Multiple-testing note: calendar effects are exploratory and must be treated as fragile until unseen-period stability is checked.

Data period: 2021-01-04 to 2026-09-24.
Observation rows: 215320.
Symbols: 30.

## Status Counts

| status                       |   count |
|:-----------------------------|--------:|
| ok                           |  210735 |
| insufficient_regime_history  |    4225 |
| insufficient_forward_history |     360 |

## Summary

| pattern_type   | pattern_name      |   holding_days | market_regime   | period_split   |   occurrence_count |   average_return |   median_return |   average_cost_adjusted_return |   median_cost_adjusted_return |   unconditional_mean_return |
|:---------------|:------------------|---------------:|:----------------|:---------------|-------------------:|-----------------:|----------------:|-------------------------------:|------------------------------:|----------------------------:|
| multi_day      | Friday_2d_hold    |              2 | falling         | full_sample    |               3120 |      0.00153229  |     0           |                    3.22868e-05 |                  -0.0015      |                  0.00393172 |
| multi_day      | Friday_2d_hold    |              2 | rising          | full_sample    |               5220 |      0.00304988  |     0.000945098 |                    0.00154988  |                  -0.000554902 |                  0.00393172 |
| multi_day      | Friday_3d_hold    |              3 | falling         | full_sample    |               3120 |      0.00249286  |     0           |                    0.000992858 |                  -0.0015      |                  0.00590652 |
| multi_day      | Friday_3d_hold    |              3 | rising          | full_sample    |               5220 |      0.00126616  |     0           |                   -0.000233835 |                  -0.0015      |                  0.00590652 |
| multi_day      | Friday_4d_hold    |              4 | falling         | full_sample    |               3120 |      0.00918931  |     0.00499277  |                    0.00768931  |                   0.00349277  |                  0.00787458 |
| multi_day      | Friday_4d_hold    |              4 | rising          | full_sample    |               5220 |      0.00668711  |     0.0044814   |                    0.00518711  |                   0.0029814   |                  0.00787458 |
| multi_day      | Friday_5d_hold    |              5 | falling         | full_sample    |               3090 |      0.0118856   |     0.0058925   |                    0.0103856   |                   0.0043925   |                  0.00985614 |
| multi_day      | Friday_5d_hold    |              5 | rising          | full_sample    |               5220 |      0.00986555  |     0.00666539  |                    0.00836555  |                   0.00516539  |                  0.00985614 |
| multi_day      | Monday_2d_hold    |              2 | falling         | full_sample    |               3420 |     -0.000301945 |     0           |                   -0.00180195  |                  -0.0015      |                  0.00393172 |
| multi_day      | Monday_2d_hold    |              2 | rising          | full_sample    |               5070 |     -0.00174705  |    -0.00285718  |                   -0.00324705  |                  -0.00435718  |                  0.00393172 |
| multi_day      | Monday_3d_hold    |              3 | falling         | full_sample    |               3420 |      0.00587398  |     0.00409663  |                    0.00437398  |                   0.00259663  |                  0.00590652 |
| multi_day      | Monday_3d_hold    |              3 | rising          | full_sample    |               5070 |      0.00383507  |     0.00230642  |                    0.00233507  |                   0.000806424 |                  0.00590652 |
| multi_day      | Monday_4d_hold    |              4 | falling         | full_sample    |               3390 |      0.0062229   |     0.00423659  |                    0.0047229   |                   0.00273659  |                  0.00787458 |
| multi_day      | Monday_4d_hold    |              4 | rising          | full_sample    |               5070 |      0.00807276  |     0.00669355  |                    0.00657276  |                   0.00519355  |                  0.00787458 |
| multi_day      | Monday_5d_hold    |              5 | falling         | full_sample    |               3390 |      0.00735846  |     0.00565996  |                    0.00585846  |                   0.00415996  |                  0.00985614 |
| multi_day      | Monday_5d_hold    |              5 | rising          | full_sample    |               5070 |      0.0108672   |     0.0088902   |                    0.00936715  |                   0.0073902   |                  0.00985614 |
| multi_day      | Thursday_2d_hold  |              2 | falling         | full_sample    |               3090 |      0.0032803   |     0           |                    0.0017803   |                  -0.0015      |                  0.00393172 |
| multi_day      | Thursday_2d_hold  |              2 | rising          | full_sample    |               5370 |      0.00705009  |     0.00602925  |                    0.00555009  |                   0.00452925  |                  0.00393172 |
| multi_day      | Thursday_3d_hold  |              3 | falling         | full_sample    |               3090 |      0.00256218  |    -0.000553571 |                    0.00106218  |                  -0.00205357  |                  0.00590652 |
| multi_day      | Thursday_3d_hold  |              3 | rising          | full_sample    |               5370 |      0.00645322  |     0.00456102  |                    0.00495322  |                   0.00306102  |                  0.00590652 |
| multi_day      | Thursday_4d_hold  |              4 | falling         | full_sample    |               3090 |      0.00284768  |     0           |                    0.00134768  |                  -0.0015      |                  0.00787458 |
| multi_day      | Thursday_4d_hold  |              4 | rising          | full_sample    |               5370 |      0.00497886  |     0.00370439  |                    0.00347886  |                   0.00220439  |                  0.00787458 |
| multi_day      | Thursday_5d_hold  |              5 | falling         | full_sample    |               3090 |      0.00785397  |     0.00504245  |                    0.00635397  |                   0.00354245  |                  0.00985614 |
| multi_day      | Thursday_5d_hold  |              5 | rising          | full_sample    |               5370 |      0.0110576   |     0.00784891  |                    0.00955757  |                   0.00634891  |                  0.00985614 |
| multi_day      | Tuesday_2d_hold   |              2 | falling         | full_sample    |               3060 |      0.00535716  |     0.00303355  |                    0.00385716  |                   0.00153355  |                  0.00393172 |
| multi_day      | Tuesday_2d_hold   |              2 | rising          | full_sample    |               5409 |      0.00441248  |     0.00353984  |                    0.00291248  |                   0.00203984  |                  0.00393134 |
| multi_day      | Tuesday_3d_hold   |              3 | falling         | full_sample    |               3060 |      0.00562506  |     0.00276878  |                    0.00412506  |                   0.00126878  |                  0.00590652 |
| multi_day      | Tuesday_3d_hold   |              3 | rising          | full_sample    |               5409 |      0.00783697  |     0.00580265  |                    0.00633697  |                   0.00430265  |                  0.00590598 |
| multi_day      | Tuesday_4d_hold   |              4 | falling         | full_sample    |               3060 |      0.00803525  |     0.00548662  |                    0.00653525  |                   0.00398662  |                  0.00787458 |
| multi_day      | Tuesday_4d_hold   |              4 | rising          | full_sample    |               5409 |      0.0102341   |     0.00822735  |                    0.00873407  |                   0.00672735  |                  0.00787386 |
| multi_day      | Tuesday_5d_hold   |              5 | falling         | full_sample    |               3060 |      0.00825662  |     0.00455136  |                    0.00675662  |                   0.00305136  |                  0.00985614 |
| multi_day      | Tuesday_5d_hold   |              5 | rising          | full_sample    |               5409 |      0.0096311   |     0.00692519  |                    0.0081311   |                   0.00542519  |                  0.00985522 |
| multi_day      | Wednesday_2d_hold |              2 | falling         | full_sample    |               3180 |      0.00889478  |     0.00495399  |                    0.00739478  |                   0.00345399  |                  0.00393172 |
| multi_day      | Wednesday_2d_hold |              2 | rising          | full_sample    |               5220 |      0.00744553  |     0.00508388  |                    0.00594553  |                   0.00358388  |                  0.00393172 |
| multi_day      | Wednesday_3d_hold |              3 | falling         | full_sample    |               3180 |      0.0102662   |     0.00614821  |                    0.00876619  |                   0.00464821  |                  0.00590652 |
| multi_day      | Wednesday_3d_hold |              3 | rising          | full_sample    |               5220 |      0.0114758   |     0.00900243  |                    0.00997576  |                   0.00750243  |                  0.00590652 |
| multi_day      | Wednesday_4d_hold |              4 | falling         | full_sample    |               3180 |      0.010355    |     0.0048789   |                    0.00885496  |                   0.0033789   |                  0.00787458 |
| multi_day      | Wednesday_4d_hold |              4 | rising          | full_sample    |               5220 |      0.0109236   |     0.00904594  |                    0.00942356  |                   0.00754594  |                  0.00787458 |
| multi_day      | Wednesday_5d_hold |              5 | falling         | full_sample    |               3180 |      0.0113723   |     0.00573305  |                    0.00987228  |                   0.00423305  |                  0.00985614 |
| multi_day      | Wednesday_5d_hold |              5 | rising          | full_sample    |               5220 |      0.00964646  |     0.00703552  |                    0.00814646  |                   0.00553552  |                  0.00985614 |
| weekday        | Friday            |              1 | falling         | full_sample    |               3120 |      0.000403774 |    -0.000935443 |                   -0.00109623  |                  -0.00243544  |                  0.00194909 |
| weekday        | Friday            |              1 | rising          | full_sample    |               5220 |      0.00449433  |     0.00287566  |                    0.00299433  |                   0.00137566  |                  0.00194909 |
| weekday        | Monday            |              1 | falling         | full_sample    |               3420 |      0.000952104 |     0           |                   -0.000547896 |                  -0.0015      |                  0.00194909 |
| weekday        | Monday            |              1 | rising          | full_sample    |               5070 |     -0.00108665  |    -0.0017922   |                   -0.00258665  |                  -0.0032922   |                  0.00194909 |
| weekday        | Thursday          |              1 | falling         | full_sample    |               3090 |      0.00133123  |    -0.00073076  |                   -0.000168767 |                  -0.00223076  |                  0.00194909 |
| weekday        | Thursday          |              1 | rising          | full_sample    |               5370 |      0.0032913   |     0.00199506  |                    0.0017913   |                   0.000495059 |                  0.00194909 |
| weekday        | Tuesday           |              1 | falling         | full_sample    |               3060 |     -0.00309805  |    -0.00191026  |                   -0.00459805  |                  -0.00341026  |                  0.00194909 |
| weekday        | Tuesday           |              1 | rising          | full_sample    |               5409 |      0.000260355 |    -0.000701775 |                   -0.00123964  |                  -0.00220178  |                  0.00194888 |
| weekday        | Wednesday         |              1 | falling         | full_sample    |               3210 |      0.00734492  |     0.00444447  |                    0.00584492  |                   0.00294447  |                  0.00194909 |
| weekday        | Wednesday         |              1 | rising          | full_sample    |               5220 |      0.00427951  |     0.00321806  |                    0.00277951  |                   0.00171806  |                  0.00194909 |

Limitations:
- This report is historical research output, not investment advice.
- Calendar effects are vulnerable to multiple testing and regime instability.
- Fundamental, macro, news and video context are added in later phases.

## Run Metadata

- Data source: local Yahoo Finance/yfinance market cache.
- Assumptions: 1-5 day holds; cost 10.0 bps; slippage 5.0 bps; benchmark regime from XU100.IS.
- Context note: Multiple-testing risk remains; unseen period is only reported when configured.

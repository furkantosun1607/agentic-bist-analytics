# Quarterly Fundamentals Report

Timing: disclosure timestamp is the signal time; quarter-end is only the observation period.
Metrics: bank records use bank-appropriate metrics, while industrial records use revenue/profit/margin/debt/cash-flow metrics.

Disclosure period: 2025-02-09T15:30:00+00:00 to 2026-09-09T15:30:00+00:00.
Observation rows: 3057.
Symbols: 30.

## Status Counts

| status                       |   count |
|:-----------------------------|--------:|
| ok                           |    3050 |
| insufficient_forward_history |       7 |

## Summary

| metric_profile   | metric_name           |   horizon | status   |   observation_count |   average_qoq_change |   median_qoq_change |   average_yoy_change |   median_yoy_change |   average_post_disclosure_return |   median_post_disclosure_return |   average_benchmark_relative_return |   average_sector_relative_return |
|:-----------------|:----------------------|----------:|:---------|--------------------:|---------------------:|--------------------:|---------------------:|--------------------:|---------------------------------:|--------------------------------:|------------------------------------:|---------------------------------:|
| bank             | assets_to_equity      |         1 | ok       |                   5 |           0.0191833  |          0.026026   |           0.0491012  |          0.0491012  |                      -0.0078139  |                      0          |                         0.00102407  |                    nan           |
| bank             | assets_to_equity      |         5 | ok       |                   5 |           0.0191833  |          0.026026   |           0.0491012  |          0.0491012  |                      -0.0013854  |                      0.012524   |                         0.00907498  |                    nan           |
| bank             | assets_to_equity      |        20 | ok       |                   5 |           0.0191833  |          0.026026   |           0.0491012  |          0.0491012  |                      -0.01117    |                     -0.0771993  |                         0.0240315   |                    nan           |
| bank             | liabilities_to_assets |         1 | ok       |                   5 |           0.00169707 |          0.00228904 |           0.00438669 |          0.00438669 |                      -0.0078139  |                      0          |                         0.00102407  |                    nan           |
| bank             | liabilities_to_assets |         5 | ok       |                   5 |           0.00169707 |          0.00228904 |           0.00438669 |          0.00438669 |                      -0.0013854  |                      0.012524   |                         0.00907498  |                    nan           |
| bank             | liabilities_to_assets |        20 | ok       |                   5 |           0.00169707 |          0.00228904 |           0.00438669 |          0.00438669 |                      -0.01117    |                     -0.0771993  |                         0.0240315   |                    nan           |
| bank             | net_income            |         1 | ok       |                   5 |          -0.11723    |         -0.189974   |           0.380287   |          0.380287   |                      -0.0078139  |                      0          |                         0.00102407  |                    nan           |
| bank             | net_income            |         5 | ok       |                   5 |          -0.11723    |         -0.189974   |           0.380287   |          0.380287   |                      -0.0013854  |                      0.012524   |                         0.00907498  |                    nan           |
| bank             | net_income            |        20 | ok       |                   5 |          -0.11723    |         -0.189974   |           0.380287   |          0.380287   |                      -0.01117    |                     -0.0771993  |                         0.0240315   |                    nan           |
| bank             | net_interest_income   |         1 | ok       |                   5 |           0.0696069  |          0.0430281  |           1.20899    |          1.20899    |                      -0.0078139  |                      0          |                         0.00102407  |                    nan           |
| bank             | net_interest_income   |         5 | ok       |                   5 |           0.0696069  |          0.0430281  |           1.20899    |          1.20899    |                      -0.0013854  |                      0.012524   |                         0.00907498  |                    nan           |
| bank             | net_interest_income   |        20 | ok       |                   5 |           0.0696069  |          0.0430281  |           1.20899    |          1.20899    |                      -0.01117    |                     -0.0771993  |                         0.0240315   |                    nan           |
| industrial       | debt_to_assets        |         1 | ok       |                 145 |           0.210498   |         -0.0018123  |           0.687488   |          0.0369819  |                      -0.0105755  |                     -0.00897664 |                         6.27935e-05 |                     -0.00112541  |
| industrial       | debt_to_assets        |         5 | ok       |                 145 |           0.210498   |         -0.0018123  |           0.687488   |          0.0369819  |                      -0.00361281 |                     -0.00286533 |                         0.00459876  |                     -0.000964587 |
| industrial       | debt_to_assets        |        20 | ok       |                 144 |           0.21144    |         -0.00207934 |           0.697308   |          0.0326675  |                      -0.0303518  |                     -0.036219   |                        -0.00659232  |                      0.00428264  |
| industrial       | free_cash_flow        |         1 | ok       |                 145 |          -0.808394   |         -0.790643   |          -0.31531    |         -0.491649   |                      -0.0113455  |                     -0.0105751  |                         0.000192258 |                     -0.000409098 |
| industrial       | free_cash_flow        |         5 | ok       |                 145 |          -0.808394   |         -0.790643   |          -0.31531    |         -0.491649   |                      -0.00231972 |                     -0.00268528 |                         0.00509846  |                      0.00048136  |
| industrial       | free_cash_flow        |        20 | ok       |                 144 |          -0.823456   |         -0.798569   |          -0.997873   |         -0.559356   |                      -0.0270192  |                     -0.0347277  |                        -0.00583829  |                     -3.16035e-05 |
| industrial       | gross_margin          |         1 | ok       |                 140 |           4.9926     |         -0.0124271  |          -0.102708   |          0.0233451  |                      -0.0103944  |                     -0.00894537 |                         0.000282859 |                     -0.00142235  |
| industrial       | gross_margin          |         5 | ok       |                 140 |           4.9926     |         -0.0124271  |          -0.102708   |          0.0233451  |                      -0.00220481 |                     -0.00233274 |                         0.00610048  |                     -0.00148257  |
| industrial       | gross_margin          |        20 | ok       |                 139 |           5.04116    |         -0.0128154  |          -0.107039   |          0.0208591  |                      -0.0288818  |                     -0.0356623  |                        -0.00429442  |                      0.00422269  |
| industrial       | net_income            |         1 | ok       |                 145 |           9.61891    |         -0.0513752  |          -0.0571275  |         -0.0739828  |                      -0.0105362  |                     -0.00897664 |                         0.000180303 |                     -0.00142235  |
| industrial       | net_income            |         5 | ok       |                 145 |           9.61891    |         -0.0513752  |          -0.0571275  |         -0.0739828  |                      -0.00307958 |                     -0.00286533 |                         0.0051932   |                     -0.00148257  |
| industrial       | net_income            |        20 | ok       |                 144 |           9.71457    |         -0.0490475  |          -0.0549343  |         -0.0733739  |                      -0.030626   |                     -0.036219   |                        -0.00608951  |                      0.00422269  |
| industrial       | operating_cash_flow   |         1 | ok       |                 140 |           0.357959   |         -0.4073     |          -0.853455   |         -0.223116   |                      -0.0112326  |                     -0.0104346  |                         0.000295241 |                     -0.000409098 |
| industrial       | operating_cash_flow   |         5 | ok       |                 140 |           0.357959   |         -0.4073     |          -0.853455   |         -0.223116   |                      -0.00141782 |                     -0.00164583 |                         0.00600236  |                      0.00048136  |
| industrial       | operating_cash_flow   |        20 | ok       |                 139 |           0.356255   |         -0.415283   |          -0.932851   |         -0.223348   |                      -0.0251453  |                     -0.0346295  |                        -0.00403415  |                     -3.16035e-05 |
| industrial       | operating_margin      |         1 | ok       |                 139 |           0.0874544  |         -0.037461   |           0.0949508  |          0.0608653  |                      -0.0104545  |                     -0.00897664 |                         0.000264967 |                     -0.00118292  |
| industrial       | operating_margin      |         5 | ok       |                 139 |           0.0874544  |         -0.037461   |           0.0949508  |          0.0608653  |                      -0.00177998 |                     -0.0019802  |                         0.00641301  |                     -0.00122732  |
| industrial       | operating_margin      |        20 | ok       |                 138 |           0.0916088  |         -0.0299252  |           0.0985807  |          0.0742664  |                      -0.0280183  |                     -0.0352441  |                        -0.00342151  |                      0.00475869  |
| industrial       | revenue               |         1 | ok       |                 145 |           0.0756265  |          0.0504299  |           0.133037   |          0.0928739  |                      -0.0105362  |                     -0.00897664 |                         0.000180303 |                     -0.00142235  |
| industrial       | revenue               |         5 | ok       |                 145 |           0.0756265  |          0.0504299  |           0.133037   |          0.0928739  |                      -0.00307958 |                     -0.00286533 |                         0.0051932   |                     -0.00148257  |
| industrial       | revenue               |        20 | ok       |                 144 |           0.0764424  |          0.0511634  |           0.136834   |          0.0945453  |                      -0.030626   |                     -0.036219   |                        -0.00608951  |                      0.00422269  |

Limitations:
- This report is historical research output, not investment advice.
- Source access, disclosure timestamps and licensing must be verified before measured reporting.
- Macro, news and video context are added in later phases.

## Run Metadata

- Data source: local yfinance fundamentals CSV with synthetic disclosure lag and local market cache.
- Assumptions: disclosure timestamp is period_end plus configured conservative lag; entry is first trading day after disclosure.
- Context note: Macro and RSS context are available as evidence metadata but are not used to calculate returns.

Scenario 2 - Weekday / Multi-Day Pattern: THYAO.IS

1-DAY WEEKDAY PATTERN
| Weekday | Occurrences | Average return | Median return | Win rate | Avg cost-adjusted |
| --- | ---: | ---: | ---: | ---: | ---: |
| Monday | 283 | +0.02% | -0.25% | +45.58% | -0.13% |
| Tuesday | 282 | -0.13% | -0.15% | +46.81% | -0.28% |
| Wednesday | 281 | +0.70% | +0.53% | +58.72% | +0.55% |
| Thursday | 282 | +0.24% | +0.04% | +50.00% | +0.09% |
| Friday | 278 | +0.48% | +0.17% | +52.52% | +0.33% |

MULTI-DAY HOLDING SUMMARY
| Holding days | Occurrences | Average return | Median return | Win rate | Avg cost-adjusted |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 1406 | +0.26% | +0.08% | +50.71% | +0.11% |
| 2 | 1405 | +0.53% | +0.24% | +52.60% | +0.38% |
| 3 | 1405 | +0.79% | +0.47% | +55.52% | +0.64% |
| 4 | 1404 | +1.05% | +0.57% | +54.77% | +0.90% |
| 5 | 1403 | +1.31% | +0.87% | +56.52% | +1.16% |

MARKET REGIME RESULTS
| Market regime | Occurrences | Average return | Win rate |
| --- | ---: | ---: | ---: |
| falling | 2643 | +1.06% | +57.89% |
| rising | 4380 | +0.62% | +51.69% |

OUT-OF-SAMPLE RESULTS
| Period split | Occurrences | Average return | Median return | Win rate |
| --- | ---: | ---: | ---: | ---: |
| selection | 5810 | +0.95% | +0.50% | +55.54% |
| unseen | 1213 | -0.01% | -0.17% | +46.74% |

TRANSACTION COST
Returns include configured trading cost and slippage through cost_adjusted_return.

MULTIPLE-TESTING RISK
Weekday effects are exploratory. Testing many weekdays, holding periods and regimes can produce apparently successful patterns by chance; selection/unseen split and regime tables are included so the result is not judged only on the full sample.

Sources:
- data/cache/<symbol>.csv local market cache
- data/cache/XU100_IS.csv benchmark regime cache when available
- config/settings.yaml cost, slippage and unseen split
- src/research.py::run_weekday_patterns
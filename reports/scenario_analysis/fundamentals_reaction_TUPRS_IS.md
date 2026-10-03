Scenario 4 - Quarterly Fundamentals + Price Reaction: TUPRS.IS

DISCLOSURE EVENT
Latest period: 2026-06-30
Disclosure timestamp used as signal time: 2026-08-09T15:30:00+00:00
Metric profile: industrial

FUNDAMENTAL METRIC CHANGES
| Metric | QoQ change | YoY change | Current value |
| --- | ---: | ---: | ---: |
| revenue | +49.63% | +59.69% | 386,420,235,000.00 |
| operating_margin | +192.44% | +81.63% | 0.14 |
| operating_cash_flow | +1904.93% | +203.99% | 126,077,980,000.00 |
| free_cash_flow | +5434.93% | +244.27% | 118,369,725,000.00 |
| debt_to_assets | +1.26% | +4.59% | 0.08 |
| net_income | +1136.68% | +290.91% | 45,877,721,000.00 |

PRICE REACTION AFTER DISCLOSURE
Primary metric for return table: revenue
| Horizon | Stock return | Stock - XU100 | Stock - sector median | Sector peer count | Entry -> Exit |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1D | -1.03% | -0.25% | n/a | 0 | 2026-08-10 -> 2026-08-11 |
| 5D | +8.46% | +6.14% | n/a | 0 | 2026-08-10 -> 2026-08-17 |
| 20D | +15.96% | +13.49% | n/a | 0 | 2026-08-10 -> 2026-09-07 |

Unavailable with current yfinance fallback:
- EBITDA
- EBITDA margin
- Net debt / EBITDA
These metrics are not invented; available operating profit/margin and cash-flow fields are reported instead.

Sources:
- data/fundamentals/fundamentals.csv yfinance fallback with synthetic disclosure timestamps
- data/cache/<symbol>.csv local market cache
- data/cache/XU100_IS.csv benchmark cache
- src/research.py::run_quarterly_fundamentals

Warning: quarter-end is not used as signal time; disclosure_timestamp controls the entry date.
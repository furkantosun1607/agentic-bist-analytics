Analyze MGROS.IS

MARKET DATA
2021-01-04 - 2026-09-24 loaded successfully.
Rows: 1435
Latest close: 534.00
Source: data/cache/<symbol>.csv via local yfinance market cache.

SECTOR ANALYSIS
Sector: Retail Trade
MGROS 20D return: -5.15%
Sector median: +3.44%
Lag score: -8.60%
Peer count: 1
Status: pass
Source: local price cache and config/universe.csv same-sector peers.

TECHNICAL
RSI: 45.31
KAMA: weakening
Supertrend: bearish
Lower Bollinger event detected: yes
Latest event: bollinger/middle_cross_up on 2026-09-21
Source: src/indicators.py and src/events.py deterministic calculations.

HISTORICAL TEST
Similar events: 63
Positive after 5 days: 41
Median 5D return: +1.70%
Event group: bollinger / middle_cross_up
Source: technical reversal replay from local event history.

FUNDAMENTALS
Metric profile: industrial
Latest period: 2026-06-30
Primary metric (revenue) YoY: improving (+2.69%)
Primary metric QoQ: improving (+13.88%)
Operating margin: -0.57%
Operating margin change: weakening (-0.73%)
Source: data/fundamentals/fundamentals.csv with synthetic disclosure timestamps.

MACRO
Hard-risk flag: no
USD/TRY: 48.85 TRY per USD
EUR/TRY: 55.68 TRY per EUR
TCMB policy rate: 37.00 %
TUIK inflation: 31.51 % yoy
FED policy rate: 3.88 % target midpoint
Source: data/macro/macro_context.csv and reports/macro_context_status.md.

BACKTEST
Signal count: 25,819
Trade count: 25,813
Cumulative return: +259.95%
Sharpe: 3.95
Max drawdown: -33.55%
Benchmark difference: -524.36%
Source: reports/backtest.md.

DATA QUALITY
PASS
Warnings: 0

AI ANALYSIS
POTENTIAL_CATCH_UP_CANDIDATE
POTENTIAL_CATCH_UP_CANDIDATE: MGROS is lagging its same-sector peer set by -8.60%; the latest technical context shows RSI 45.31, bearish Supertrend, and 63 comparable events with median 5D return +1.70%. fundamentals show revenue YoY improving (+2.69%) and operating margin change weakening (-0.73%). macro context has no hard-risk flag, while the measured backtest contributes 25,813 tradable rows, Sharpe 3.95, max drawdown -33.55%, and benchmark difference -524.36%. Data quality gate result is PASS. The label is therefore an educational investigation signal tied to the cited evidence files, not a buy/sell instruction.

Evidence:
E1 reports/research_run_status.md - measured scenario report status.
E2 reports/backtest.md - cost-adjusted backtest and risk summary.
E3 reports/strategy_variants.md - A-E strategy comparison and unavailable component notes.
E4 reports/llm_agent_harness.md - constrained LLM explanation/replay status.
E5 reports/pdf_requirement_coverage.md - PDF requirement coverage and limitations.

Warning:
Historical evidence does not guarantee future returns. This is educational research output, not investment advice.

Run context:
Cache dir: C:\Users\Furkan\Desktop\econ\data\cache
Report generated from local artifacts under: C:\Users\Furkan\Desktop\econ\reports
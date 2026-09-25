# CSE-481 Engineering Economics: BIST 100 Research Harness

A small, reproducible **educational research project** for 30 selected BIST 100 stocks. It studies sector catch-up, calendar patterns, technical reversals, and reactions to quarterly financial disclosures. Python performs calculations; a controlled AI assistant summarizes evidence. Results are historical observations, not investment advice. The project has no broker connection or real trading.

This README is a practical implementation guide based on the course project PDF. The proposed file names and thresholds are implementation choices, not extra course requirements. **Project status: implementation infrastructure is ready; measured financial findings still require verified live/cache datasets.**

## What must be delivered

1. A fixed and documented 30-stock universe with sector labels and a data dictionary.
2. Four research reports: sector catch-up, weekday/multi-day patterns, technical reversals, and quarterly financial changes versus post-disclosure returns.
3. Market, fundamental, macro, news, and selected public-video context, each with its source and relevant timestamp.
4. Backtests with costs, benchmarks, risk measures, and an unseen test period.
5. A small MCP tool set and a stateful AI workflow with an evidence record, data-quality gate, human review, and replayable decision log.
6. A short comparison of strategy variants A-E and harness versions A-E, followed by a final report and classroom demo.

Optional machine learning is **not** needed to complete this plan. A web dashboard is not required by the PDF.

## Study universe

Use the PDF's exact 30 tickers and simplified sector labels. Store them in `config/universe.csv` with at least `ticker,yahoo_symbol,sector`. Do not silently change the list between experiments. Recheck ticker availability and BIST 100 membership for the selected study period and record any discrepancy.

```csv
ticker,yahoo_symbol,sector
ASELS,ASELS.IS,Technology / Defense
TUPRS,TUPRS.IS,Petroleum / Refining
BIMAS,BIMAS.IS,Retail Trade
THYAO,THYAO.IS,Transportation / Airlines
AKBNK,AKBNK.IS,Banking
KCHOL,KCHOL.IS,Holding / Investment
EREGL,EREGL.IS,Basic Metals / Steel
TCELL,TCELL.IS,Telecommunications
CCOLA,CCOLA.IS,Food & Beverage
MGROS,MGROS.IS,Retail Trade
SASA,SASA.IS,Chemicals / Plastics
TRALT,TRALT.IS,Mining
FROTO,FROTO.IS,Automotive
ENKAI,ENKAI.IS,Construction
PGSUS,PGSUS.IS,Transportation / Airlines
MPARK,MPARK.IS,Healthcare
EKGYO,EKGYO.IS,Real Estate Investment Trust
GUBRF,GUBRF.IS,Chemicals / Fertilizer
TURSG,TURSG.IS,Insurance
ENJSA,ENJSA.IS,Electric Utilities
TTKOM,TTKOM.IS,Telecommunications
OYAKC,OYAKC.IS,Cement
AKSEN,AKSEN.IS,Electric Utilities
ISMEN,ISMEN.IS,Brokerage / Capital Markets
ARCLK,ARCLK.IS,Durables / Machinery
ECILC,ECILC.IS,Healthcare / Pharmaceuticals
MAVI,MAVI.IS,Retail / Apparel
PETKM,PETKM.IS,Petrochemicals
TOASO,TOASO.IS,Automotive
KRDMD,KRDMD.IS,Basic Metals / Steel
```

Some simplified sectors contain only one stock. Mark a sector comparison as **insufficient peers** when it cannot be calculated; do not compare a stock with itself. The banking peer example in the PDF includes tickers outside the fixed 30-stock list and is illustrative only.

## Keep the implementation small

```text
README.md
requirements.txt
config/universe.csv
config/settings.yaml
src/data.py              # source adapters and timestamp checks
src/indicators.py        # deterministic technical indicators
src/research.py          # four scenario analyses
src/backtest.py          # historical evaluation and benchmarks
src/mcp_server.py        # selected deterministic tools
src/harness.py           # state transitions, evidence and review
notebooks/               # exploration and demo
reports/                 # four scenario reports and final report
tests/                   # calculation, timing and workflow checks
```

CSV/Parquet files and SQLite are sufficient. Cache a small, dated dataset so the classroom demo does not depend on live source availability. Document installation and one working demo command after implementation; do not commit API keys.

## Install, Cache, and Demo

Use Python 3.11+ in a clean virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -s tests
```

Populate local market and RSS caches when live source access is available:

```powershell
python -m scripts.fetch_market_data
python -m scripts.fetch_rss_news
python -m scripts.normalize_rss_news
python -m scripts.match_news_aliases
python -m scripts.build_news_context
python -m scripts.audit_market_cache
```

Prepare fundamentals data only from a permitted source. Fintables access is not assumed; the current workflow uses the instructor-approved `yfinance` fallback and generates conservative synthetic disclosure timestamps as `period_end + 40 days at 18:30 Europe/Istanbul`. This prevents quarter-end data from being used as if it were known immediately, but it is not an exact KAP publication time. Generate the local CSV and audit it with:

```powershell
python -m scripts.fetch_yfinance_fundamentals
python -m scripts.audit_fundamentals_import
```

The CSV is written to `data/fundamentals/fundamentals.csv` and ignored by git. If the CSV is missing, has no mapped rows, or fails point-in-time validation, `reports/fundamentals_import_status.md` blocks measured fundamentals and the quarterly report remains inconclusive. Detailed field rules are in `config/fundamentals_import_instructions.md`.

Prepare numeric macro context through the local CSV workflow in `config/macro_context_import_instructions.md`. USD/TRY and EUR/TRY are fetched with yfinance; TCMB policy rate, TUIK inflation, and Fed policy rate are embedded as static curated point-in-time records so the demo does not require API keys. Generate and audit macro readiness with:

```powershell
python -m scripts.fetch_macro_context
python -m scripts.audit_macro_context
```

If `data/macro/macro_context.csv` is missing or incomplete, `reports/macro_context_status.md` records the source gap. RSS macro news aliases do not replace numeric macro records.

Run the four required research reports from local cache artifacts:

```powershell
python -m scripts.run_research_reports
```

This writes `reports/research_run_status.md` plus refreshed sector catch-up, weekday pattern, technical reversal, and quarterly fundamentals reports.

Run the measured backtest/risk report from the fixed research signal policy:

```powershell
python -m scripts.run_backtests
```

This refreshes `reports/backtest.md` with signal counts, trade counts, configured costs, benchmark-relative return, cumulative trade-level return, Sharpe, maximum drawdown and win rate. It is an educational trade-level backtest, not a capital-constrained portfolio simulation.

Run the measured unseen-period and regime split report:

```powershell
python -m scripts.run_split_regime
```

This uses the configured `experiment.unseen_start_date` and XU100 benchmark regime labels to refresh `reports/split_regime.md`.

Then run the offline demo:

```powershell
python -m scripts.demo --offline
```

The market audit writes `reports/market_cache_audit.md`. The offline demo performs no network calls. It validates settings and the fixed universe, regenerates `reports/report_index.md` and `reports/final_technical_report.md`, checks market cache, checks RSS raw/normalized/matched/context artifacts, and writes `reports/demo_summary.md`.

Cache files under `data/cache/` and `data/rss/` are local artifacts and are not committed. If a cache is missing, the demo reports a warning and does not invent measured returns or news context.

## Data sources and one essential rule

| Data | Source named in the PDF | Minimum use |
| --- | --- | --- |
| Stock and XU100 prices | Yahoo Finance / yfinance | Dated OHLCV, adjusted-price policy, benchmark history |
| Company finances | Fintables in the PDF; current fallback is Yahoo Finance / yfinance with synthetic disclosure lag | Quarterly growth, profitability, leverage, liquidity and cash flow |
| Turkish macro | TCMB/EVDS and TÜİK | USD/TRY, EUR/TRY, policy rate and inflation |
| Global rates | Federal Reserve | Policy-rate changes |
| Financial news | Legally accessible RSS/news source | Dated company, sector and macro RSS context records |
| Public commentary | Instructor-approved public videos | Optional; not used in the current RSS-only context flow |

For every historical decision at time `t`, use only information **publicly available by `t`**. Store the observation period separately from the publication time and the download time. A quarter-end date alone is not enough for a financial signal. Apply the same publication-time rule to macro, RSS news, and optional video context. If essential release times cannot be established, report the gap instead of guessing. Use sources within their access and licensing terms.

Current RSS policy: feeds are not streamed in real time. They are fetched by polling, cached locally with `published_timestamp` and `fetched_timestamp`, normalized, deduplicated, alias-matched to ticker/sector/macro entities, and then filtered by decision time. RSS context is evidence metadata; it is not a standalone trading signal.

## Four required research scenarios

| Scenario | Simple first experiment | Report at least |
| --- | --- | --- |
| **1. Sector catch-up** | Rank stocks by 20-day return minus the median return of eligible sector peers; check whether laggards outperform peers over the next 5/10/20 trading days. | Peer count, leaders/laggards, later relative returns, false positives, fundamental/macro context. |
| **2. Weekday patterns** | Test a few predefined weekday and two-to-five-day patterns; compare with unconditional returns. | Occurrence count, average/median return, costs, market-regime split and unseen-period stability. Mention multiple-testing risk. |
| **3. Technical reversals** | Detect timestamped indicator events and compare next 1/3/5/10-day returns for individual versus combined signals. | Event and failure counts, bounce rate, return distribution, different market regimes. |
| **4. Quarterly fundamentals** | Compare quarterly and annual changes with 1/5/20-day returns after the public disclosure. | Disclosure timestamp, revenue/profit/margin/debt/cash-flow changes, return relative to XU100 and sector peers. |

The technical module covers **SMA, EMA, KAMA, RSI, MACD, Bollinger Bands, ATR, Supertrend, Ichimoku, support/resistance, and volume**. For scenario 3, include lower/middle/upper Bollinger tests, RSI peaks/troughs, Supertrend flips, KAMA changes, Ichimoku interactions, and support/resistance touches. One small event detector per family is enough; avoid tuning hundreds of rules. Use sector-appropriate fundamental ratios: bank statements should not be evaluated blindly with industrial-company metrics.

## Backtesting rules

- Record when a signal becomes knowable and execute it no earlier than the next feasible trading point. Future returns are outcomes, never inputs to the signal.
- Document the assumed entry/exit price, trading costs and slippage. Compare each candidate with Buy-and-Hold, XU100 and a sector benchmark when a valid peer group exists.
- Report cumulative return, Sharpe ratio, maximum drawdown, win rate, benchmark difference and number of signals.
- Keep a later period unseen while choosing rules; test it only after the choices are fixed. Include at least a basic rising/falling-market comparison.
- Preview five strategy combinations on the same data: **A** technical, **B** + sector, **C** + fundamentals, **D** + macro, **E** + verified news/video context. If a source is missing, mark that variant unavailable; do not invent values.

A pattern can be reported as inconclusive. The PDF's example percentages are hypothetical and must never appear as measured results.

## Small MCP and agent harness

Implement a few deterministic MCP tools that cover the PDF's tool categories: market/index history, indicators and events, sector ranking, weekday test, point-in-time fundamentals, macro/news/speech context, backtest, data-quality check and evidence bundle. A tool returns structured values with source and time metadata. It never asks the LLM to calculate prices or financial ratios.

A single orchestrator can coordinate the work with small analysis/review roles; separate reasoning services are unnecessary for a classroom prototype. Enforce this sequence in code:

```text
select universe -> load and validate data -> run four analyses ->
add available context -> build evidence -> compare strategy variants ->
backtest -> risk gate -> explain -> human review -> save decision
```

Only permitted tools are callable in each state. Keep an observed-feature list and a smaller **committed evidence set** used in the explanation. Link every numerical statement to a tool output. A missing source or small sample produces a warning; future-information leakage, broken history or critical date mismatch blocks a conclusion. The output uses the PDF's limited educational states such as `WATCH`, `INVESTIGATE`, `POTENTIAL_CATCH_UP_CANDIDATE`, `REJECT_SIGNAL`, or `ANALYSIS_UNSAFE`, with a gate status and reason. A person accepts, modifies, or rejects the result; save the decision and enough inputs to replay it.

For the required harness comparison, run the **same small set of fixed questions** with: **A** raw LLM, **B** LLM + tools, **C** tools + enforced states, **D** C + evidence/quality gate, **E** D + memory/human review. Compare unsupported numbers, invalid tool calls, evidence completeness and replayability. This A-E list measures the **agent harness**; the A-E strategy combinations above measure **financial rules**.

## Build order and acceptance checklist

1. **Data:** freeze the 30-stock CSV, fetch/cache prices and XU100, document missing symbols, then add point-in-time financial and macro records.
2. **Research:** calculate indicators and produce the four scenario reports with counts, benchmarks and failed cases.
3. **Verification:** add realistic nonzero cost/slippage assumptions, the unseen test period and data-leakage checks.
4. **Harness:** expose deterministic MCP tools, enforce state order, attach evidence, block unsafe cases and save a human-reviewed replay.
5. **Submission:** add selected legally accessible news/video examples, compare both A-E groups, write limitations and demonstrate one full analysis.

The project is ready to submit when the repository contains working Python code/notebooks and environment instructions, a data dictionary and fixed universe, all four scenario reports, a macro/context report, benchmarked backtests, MCP/state definitions, a decision-log replay, the harness experiment comparison and a final technical report/demo. Every report must identify its data period, source, sample size, assumptions and limitations.

**Source:** *CSE-481 Engineering Economics - Integrated BIST 100 Agentic Financial Analytics Harness*, course project specification supplied by the instructor (2026). This README is a shortened implementation guide; the PDF remains authoritative if an interpretation differs.

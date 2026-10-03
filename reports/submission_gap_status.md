# Submission Gap Status

Status: final local submission package is ready; remaining items are documented limitations, not blocking local workflow gaps.

## Ready Now

| Area | Status | Notes |
| --- | --- | --- |
| Fixed universe | ready | 30 tickers and data dictionary are committed. |
| Market fetch pipeline | ready local workflow | `python -m scripts.fetch_market_data` populates ignored `data/cache/`. |
| Fundamentals import pipeline | ready local workflow | `python -m scripts.fetch_yfinance_fundamentals` produced 160 local rows and audit is ready. |
| Macro import workflow | ready local workflow | `python -m scripts.fetch_macro_context` produced 1421 rows and audit is ready with 2026 TCMB/TUIK/FED records. |
| Four scenario reports | measured local workflow | `python -m scripts.run_research_reports` generated all four required reports from local cache artifacts. |
| Backtest/risk report | measured local workflow | `python -m scripts.run_backtests` generated 25,819 signal rows and 25,813 tradable rows with configured costs and benchmark comparison. |
| Unseen/regime comparison | measured local workflow | `python -m scripts.run_split_regime` used `2025-10-01` unseen start and generated 4 stability rows plus 6 regime rows. |
| Strategy variants A-E | measured partial local workflow | `python -m scripts.run_strategy_variants` measured A-C and marks D-E unavailable until executable macro/news-video signals exist. |
| Harness variants A-E | measured deterministic workflow | `python -m scripts.run_harness_variants` scored 5 fixed questions across 5 harness variants without live LLM calls. |
| Optional LLM agent harness | ready live/offline workflow | `python -m scripts.run_llm_agent_harness --provider auto` uses live Gemini or OpenAI-compatible LLM when configured and deterministic fallback otherwise. |
| Rich LLM explanation schema | ready | LLM harness output includes summary, methodology, evidence links, quality-gate interpretation, limitations, risk notes and next steps. |
| PDF requirement coverage | ready | `reports/pdf_requirement_coverage.md` maps the course PDF requirements to project evidence, status and limitations. |
| Classroom demo notebook | ready | `notebooks/01_classroom_demo.ipynb` provides the classroom walkthrough, command sequence, report links, Gemini output reader and limitations. |
| Static dashboard UI | ready | `python -m scripts.build_dashboard` writes `ui/dashboard.html` with report inventory, LLM status and demo commands. |
| Human-reviewed decision log | reviewed replay workflow | `python -m scripts.run_decision_log` wrote one reviewed educational record with replay status `ok`. |
| RSS context pipeline | ready local workflow | Fetch, normalize, alias match and context builder commands are available. |
| Offline demo | ready | `python -m scripts.demo --offline` reads local artifacts without live network calls. |
| Harness/evidence/decision-log infrastructure | ready | Schemas and deterministic tests exist. |

## Remaining Limitations

| Limitation | Type | Status |
| --- | --- | --- |
| Strategy variants D-E | unavailable component signals | Macro and news/video context are metadata/evidence only; no executable trade signals are invented. |
| Harness A-E comparison prose quality | deterministic experiment limitation | Harness A-E comparison remains fixture-only; optional LLM agent harness exists separately for constrained explanation runs. |
| Live LLM availability | optional external dependency | Gemini calls require `GEMINI_API_KEY` or `GOOGLE_API_KEY`; OpenAI-compatible calls require `LLM_API_KEY` or `OPENAI_API_KEY`; offline fallback remains replayable. |
| Video/STT context | documented limitation | Instructor-approved video/speech pipeline is not implemented in the current RSS-only flow. |
| Raw cache artifacts | local only | `data/cache`, `data/rss`, `data/fundamentals`, and `data/macro` stay ignored by git. |

## Current External Inputs Needed From User

- None for the current local deterministic workflow.

## Non-Negotiable Reporting Rules

- Missing data is reported as missing, blocked or inconclusive.
- RSS/news context is evidence metadata, not an investment recommendation.
- Measured returns, risk metrics and strategy comparisons must cite data period, source, sample size, assumptions and limitations.

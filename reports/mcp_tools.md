# Deterministic MCP Tool Surface

Status: deterministic tool registry implemented, transport wrapper not yet required.

Implemented tools:
- `market_history`: normalized market/index history metadata from frames or cache.
- `indicators_events`: technical indicators and event detector output.
- `sector_ranking`: fixed-universe sector catch-up observations.
- `weekday_test`: weekday and multi-day calendar pattern tests.
- `point_in_time_fundamentals`: fundamentals point-in-time validation and optional research summary.
- `context`: macro/news/video normalization, decision-time filtering and point-in-time gate.
- `backtest`: point-in-time safe backtest with cost and risk summary.
- `data_quality`: market-data quality and future-outcome feature checks.
- `evidence_bundle`: source-linked observed feature bundle.

Interface:
- `list_tools()` returns tool metadata.
- `call_tool(name, args)` returns `ToolResponse(status, data, warnings, errors)`.
- Tool calculations are deterministic Python calls; LLMs do not compute prices, returns or risk metrics.

Limitations:
- This is the testable tool surface; stdio/SSE MCP transport can be layered on top later if required.
- Tool outputs depend on verified/cached input data.
- This report is historical research infrastructure, not investment advice.

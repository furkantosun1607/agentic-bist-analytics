# Human Review And Replayable Decision Log

Status: decision log schema and replay checks implemented.

Implemented scope:
- JSONL decision log schema.
- Required output label, human review and evidence hash.
- Harness snapshot capture.
- Inputs and deterministic tool outputs capture.
- Stable record hash for tamper detection.
- Replay check for record integrity and evidence-hash consistency.
- Markdown decision-log report writer.

Current output note:
- No live reviewed investment or strategy decision is reported here yet.
- Unit tests use synthetic records only.

Limitations:
- Replay currently validates persisted inputs, tool outputs, harness state and hashes.
- Full tool re-execution replay can be layered on top after verified live/cache datasets are available.
- This report is historical research infrastructure, not investment advice.

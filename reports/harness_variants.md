# Harness Variant Comparison A-E

Status: harness variant comparison engine implemented, not yet populated with live benchmark questions.

Variants:
- A: raw LLM
- B: LLM + tools
- C: tools + enforced states
- D: C + evidence/quality gate
- E: D + memory/human review

Implemented scope:
- Fixed question-set schema.
- Unsupported-number count.
- Invalid-tool-call count.
- Evidence completeness count.
- Quality-gate availability count.
- Replayability count.
- Human-review availability count.
- Capability score and limited/ok status.

Current output note:
- No live LLM run is reported here.
- Synthetic unit tests validate the deterministic comparison logic.

Limitations:
- This compares harness capabilities, not financial strategy returns.
- P20 strategy A-E and P21 harness A-E are separate comparison tracks.
- This report is historical research infrastructure, not investment advice.

# Strategy Variant Comparison A-E

Status: strategy variant comparison engine implemented, not yet populated with live strategy outputs.

Variants:
- A: technical
- B: technical + sector
- C: B + fundamentals
- D: C + macro
- E: D + verified news/video context

Implemented scope:
- Same price data period across variants.
- Same trading cost and slippage assumptions across variants.
- Backtest/risk summary side by side.
- Missing-source variants marked `unavailable`.
- Variant trade output keeps component metadata.
- Variant E can carry RSS context availability, evidence URL count, latest timestamp and quality warnings.
- RSS context metadata does not create trade signals by itself.

Current output note:
- No measured strategy result is reported here yet.
- Verified technical, sector, fundamentals, macro and executable news/context signal records are still required.
- RSS context is available as supporting evidence metadata, not as a standalone performance claim.

Limitations:
- Missing components are not inferred or filled.
- Live/cache market data and verified context records must be prepared before final comparison.
- RSS news density is context evidence only and must not be reported as alpha or strategy superiority.
- This report is historical research infrastructure, not investment advice.

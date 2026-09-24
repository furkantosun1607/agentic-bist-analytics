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

Current output note:
- No measured strategy result is reported here yet.
- Verified technical, sector, fundamentals, macro and news/video signal records are still required.

Limitations:
- Missing components are not inferred or filled.
- Live/cache market data and verified context records must be prepared before final comparison.
- This report is historical research infrastructure, not investment advice.

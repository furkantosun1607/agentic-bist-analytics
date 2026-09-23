# Universe Data Dictionary

`config/universe.csv` freezes the 30-stock study universe from the project README.

| Column | Type | Required | Description |
| --- | --- | --- | --- |
| `ticker` | string | yes | Short BIST ticker without exchange suffix. Must be unique in the fixed universe. |
| `yahoo_symbol` | string | yes | Yahoo Finance symbol used by the market data adapter. For this project, BIST symbols use the `.IS` suffix. |
| `sector` | string | yes | Simplified sector label from the README. Some sectors intentionally contain only one stock. |

Rules:
- The universe must contain exactly 30 rows unless the implementation plan is explicitly updated with a documented exception.
- Do not silently add, remove, or replace tickers between experiments.
- Sector peer comparisons must mark single-stock sectors as `insufficient peers`; a stock is never compared with itself.

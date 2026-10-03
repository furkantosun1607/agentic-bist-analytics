# Integrated BIST 100 Agentic Financial Analytics Harness

> **CSE-481 Engineering Economics --- Project 2026**\
> Educational research system for BIST 100 stocks.\
> **Core principle:** LLM reasons and explains; Python calculates; the
> harness controls; backtests verify; evidence is logged; a human makes
> the final decision.

This repository is intended to become the implementation backbone of the
CSE-481 project described in the course specification. The project is
**not** a single stock-prediction model. It is a controlled,
reproducible financial research and agent-harness system that combines
deterministic market/fundamental/macro calculations, historical
verification, contextual evidence, MCP tools, stateful workflow control,
memory, risk/data-quality gates, and human review.

**Educational/research use only.** The system must not connect to a
broker, send real orders, manage real money, or present personalized
investment advice.

------------------------------------------------------------------------

## 1. Project Objective

The system will investigate four mandatory research scenarios:

1.  **Sector Relative-Value / Catch-Up**
2.  **Weekday and Multi-Day Patterns**
3.  **Technical Reversal Events**
4.  **Quarterly Fundamental Change and Post-Disclosure Price Reaction**

The system should answer research questions with evidence-backed
analytical states rather than simply producing a `BUY` or `SELL` label.

Examples of intended analytical states:

-   `SECTOR_LAGGARD`
-   `POTENTIAL_CATCH_UP_CANDIDATE`
-   `TECHNICAL_REVERSAL_CANDIDATE`
-   `FUNDAMENTAL_IMPROVEMENT_CANDIDATE`
-   `REJECT_SIGNAL`
-   `INVESTIGATE`
-   `ANALYSIS_UNSAFE`

The project specification explicitly distinguishes:

-   Prediction ≠ profitable strategy
-   Correlation ≠ causation
-   Backtest ≠ future guarantee
-   Historical evidence ≠ investment advice
-   LLM confidence ≠ statistical probability
-   Fundamental strength ≠ guaranteed price increase
-   Expert commentary ≠ verified fact

------------------------------------------------------------------------

# 2. Architecture Philosophy

The most important architectural rule is the separation of
responsibilities.

``` text
                    ┌─────────────────────────────┐
                    │   Financial Orchestrator     │
                    │            Agent             │
                    └──────────────┬──────────────┘
                                   │
             ┌─────────────────────┼─────────────────────┐
             ▼                     ▼                     ▼
   ┌─────────────────┐   ┌──────────────────┐   ┌──────────────────┐
   │ Market / Sector │   │ Fundamental/Macro │   │ News / Speech    │
   │ Analysis Agent  │   │ Analysis Agent    │   │ Intelligence     │
   └────────┬────────┘   └────────┬─────────┘   └────────┬─────────┘
            │                     │                      │
            └──────────────┬──────┴──────────────┬───────┘
                           ▼                     ▼
                  ┌─────────────────┐   ┌─────────────────────┐
                  │ Evidence Builder │   │ Risk & Data Quality │
                  └────────┬────────┘   │        Gate         │
                           │            └──────────┬──────────┘
                           └──────────────┬─────────┘
                                          ▼
                              ┌──────────────────────┐
                              │ Strategy / Backtest  │
                              │ Verification Agent   │
                              └──────────┬───────────┘
                                         ▼
                              ┌──────────────────────┐
                              │ Human Review +       │
                              │ Decision Log/Replay  │
                              └──────────────────────┘
```

### Responsibility boundary

  -------------------------------------------------------------------------
  Layer                   Responsibility            Must NOT do
  ----------------------- ------------------------- -----------------------
  Data workers            Retrieve and normalize    Make investment
                          data                      conclusions

  Indicator workers       Calculate technical       Ask an LLM to calculate
                          indicators                indicators

  Research modules        Run deterministic         Invent missing
                          experiments               observations

  MCP tools               Expose controlled         Give the LLM
                          capabilities              unrestricted
                                                    database/system access

  Agents                  Interpret tool outputs    Replace deterministic
                          and coordinate analysis   calculations

  Evidence Builder        Select traceable evidence Create unsupported
                                                    facts

  Risk/Data Quality Gate  Block unsafe analysis     Silently ignore leakage

  Backtest                Verify historical rules   Claim future
                                                    profitability

  Human Review            Challenge/accept/reject   Automatically execute
                          educational conclusions   trades
  -------------------------------------------------------------------------

------------------------------------------------------------------------

# 3. Study Universe

The course specification provides a 30-stock study universe intended to
span multiple sectors.

  Ticker   Yahoo Symbol   Simplified Sector
  -------- -------------- ------------------------------
  ASELS    ASELS.IS       Technology / Defense
  TUPRS    TUPRS.IS       Petroleum / Refining
  BIMAS    BIMAS.IS       Retail Trade
  THYAO    THYAO.IS       Transportation / Airlines
  AKBNK    AKBNK.IS       Banking
  KCHOL    KCHOL.IS       Holding / Investment
  EREGL    EREGL.IS       Basic Metals / Steel
  TCELL    TCELL.IS       Telecommunications
  CCOLA    CCOLA.IS       Food & Beverage
  MGROS    MGROS.IS       Retail Trade
  SASA     SASA.IS        Chemicals / Plastics
  TRALT    TRALT.IS       Mining
  FROTO    FROTO.IS       Automotive
  ENKAI    ENKAI.IS       Construction
  PGSUS    PGSUS.IS       Transportation / Airlines
  MPARK    MPARK.IS       Healthcare
  EKGYO    EKGYO.IS       Real Estate Investment Trust
  GUBRF    GUBRF.IS       Chemicals / Fertilizer
  TURSG    TURSG.IS       Insurance
  ENJSA    ENJSA.IS       Electric Utilities
  TTKOM    TTKOM.IS       Telecommunications
  OYAKC    OYAKC.IS       Cement
  AKSEN    AKSEN.IS       Electric Utilities
  ISMEN    ISMEN.IS       Brokerage / Capital Markets
  ARCLK    ARCLK.IS       Durables / Machinery
  ECILC    ECILC.IS       Healthcare / Pharmaceuticals
  MAVI     MAVI.IS        Retail / Apparel
  PETKM    PETKM.IS       Petrochemicals
  TOASO    TOASO.IS       Automotive
  KRDMD    KRDMD.IS       Basic Metals / Steel

**Important:** The project document states that BIST index membership
changes over time. The universe/sector map therefore needs to be
versioned and re-checked at the beginning of an experiment.

Recommended implementation:

``` text
data/universe/
├── universe_2026.csv
├── sector_map_2026.csv
└── README.md
```

------------------------------------------------------------------------

# 4. Data Sources

The project requires multiple evidence layers.

  -----------------------------------------------------------------------
  Layer                   Source                  Intended Use
  ----------------------- ----------------------- -----------------------
  Market                  Yahoo Finance /         OHLCV, adjusted prices,
                          `yfinance`              XU100 and peer
                                                  histories

  Fundamentals            Fintables               Financial statements,
                                                  growth, profitability,
                                                  leverage, liquidity,
                                                  valuation

  Türkiye macro           TCMB / EVDS             USD/TRY, EUR/TRY,
                                                  policy-related and
                                                  monetary series

  Economy                 TÜİK                    CPI, inflation,
                                                  industrial production,
                                                  unemployment and other
                                                  official statistics

  Global rates            Federal Reserve         Federal funds target
                                                  range and FOMC policy
                                                  changes

  News                    Bloomberg or legally    Timestamped contextual
                          accessible licensed     event metadata
                          feed                    

  Public commentary       Instructor-approved     Speech-to-text topics,
                          public videos           claims, stance and
                                                  context
  -----------------------------------------------------------------------

### Legal/data-use constraints

The course specification requires legally accessible data.

The project must not:

-   bypass paywalls;
-   bypass authentication;
-   bypass licensing restrictions;
-   bypass platform protections.

For public video analysis, retain only the amount of transcript needed
for educational analysis and preserve:

-   source URL;
-   speaker/channel;
-   publication time;
-   transcript segment timestamps.

------------------------------------------------------------------------

# 5. Recommended Repository Structure

The following structure should be used as the implementation target.

``` text
bist100-agentic-financial-analytics/
│
├── README.md
├── pyproject.toml
├── requirements.txt
├── .env.example
├── .gitignore
│
├── config/
│   ├── universe.yaml
│   ├── indicators.yaml
│   ├── backtest.yaml
│   ├── risk_rules.yaml
│   └── agent_states.yaml
│
├── data/
│   ├── raw/
│   │   ├── market/
│   │   ├── fundamentals/
│   │   ├── macro/
│   │   ├── news/
│   │   └── speech/
│   ├── processed/
│   │   ├── market/
│   │   ├── technical/
│   │   ├── sector/
│   │   ├── fundamentals/
│   │   ├── macro/
│   │   └── context/
│   ├── events/
│   └── universe/
│
├── src/
│   ├── data/
│   │   ├── market.py
│   │   ├── fundamentals.py
│   │   ├── macro.py
│   │   ├── news.py
│   │   └── speech.py
│   │
│   ├── indicators/
│   │   ├── trend.py
│   │   ├── momentum.py
│   │   ├── volatility.py
│   │   ├── supertrend.py
│   │   ├── ichimoku.py
│   │   └── structure.py
│   │
│   ├── research/
│   │   ├── sector_relative_value.py
│   │   ├── weekday_patterns.py
│   │   ├── reversal_events.py
│   │   └── fundamental_reaction.py
│   │
│   ├── features/
│   │   └── engineering.py
│   │
│   ├── backtest/
│   │   ├── engine.py
│   │   ├── metrics.py
│   │   └── strategies.py
│   │
│   ├── evidence/
│   │   ├── builder.py
│   │   └── models.py
│   │
│   ├── quality/
│   │   ├── data_quality.py
│   │   ├── leakage.py
│   │   └── risk_gate.py
│   │
│   ├── agents/
│   │   ├── orchestrator.py
│   │   ├── market_agent.py
│   │   ├── fundamental_macro_agent.py
│   │   ├── news_speech_agent.py
│   │   ├── strategy_backtest_agent.py
│   │   └── risk_agent.py
│   │
│   ├── harness/
│   │   ├── state_machine.py
│   │   ├── permissions.py
│   │   ├── memory.py
│   │   └── replay.py
│   │
│   └── mcp/
│       ├── server.py
│       └── tools/
│           ├── market_tools.py
│           ├── technical_tools.py
│           ├── fundamental_tools.py
│           ├── macro_tools.py
│           ├── context_tools.py
│           ├── backtest_tools.py
│           └── quality_tools.py
│
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_technical_analysis.ipynb
│   ├── 03_sector_relative_value.ipynb
│   ├── 04_weekday_patterns.ipynb
│   ├── 05_reversal_events.ipynb
│   ├── 06_fundamental_reaction.ipynb
│   ├── 07_macro_context.ipynb
│   └── 08_backtest_results.ipynb
│
├── reports/
│   ├── technical_reversal/
│   ├── sector_catchup/
│   ├── weekday_patterns/
│   ├── fundamental_reaction/
│   ├── macro_context/
│   └── harness_experiments/
│
├── logs/
│   ├── decisions/
│   ├── evidence/
│   └── replay/
│
└── tests/
    ├── unit/
    ├── integration/
    ├── leakage/
    ├── backtest/
    └── harness/
```

------------------------------------------------------------------------

# 6. Technical Analysis Layer

The technical layer must calculate and store at least:

### Trend

-   SMA
-   EMA
-   KAMA

Research uses:

-   direction;
-   slope;
-   crossovers;
-   distance from adaptive average.

### Momentum

-   RSI
-   MACD

Research uses:

-   momentum regime;
-   RSI local extrema;
-   divergence candidates.

### Volatility

-   Bollinger Bands
-   ATR

Research uses:

-   band touches;
-   bandwidth;
-   volatility regime.

### Trend state

-   Supertrend

Research uses:

-   bullish/bearish state;
-   state changes;
-   post-flip returns.

### Cloud/structure

-   Ichimoku Cloud

Research uses:

-   price above/below cloud;
-   cloud breakout;
-   cloud rejection;
-   Tenkan/Kijun relationships.

### Market structure

-   Support/resistance
-   Pivot clustering
-   Touch count
-   Recency
-   Volume
-   Reversal strength

------------------------------------------------------------------------

# 7. Technical Reversal Event Model

Technical events must be represented as timestamped research events.

Example:

``` json
{
  "ticker": "ASELS",
  "event": "BOLLINGER_LOWER_TOUCH",
  "event_date": "YYYY-MM-DD",
  "rsi_state": "LOCAL_LOW",
  "supertrend_state": "BEARISH",
  "kama_slope": "FLATTENING",
  "ichimoku_state": "BELOW_CLOUD",
  "volume_regime": "HIGH",
  "forward_horizons": [1, 3, 5, 10]
}
```

Mandatory event families:

-   Lower Bollinger Band touch → upward reversal test
-   Middle Bollinger Band test → continuation/rejection
-   Upper Bollinger Band touch → downward reversal test
-   RSI local trough/peak
-   Supertrend direction flip
-   KAMA slope change
-   KAMA-price cross
-   Ichimoku cloud breakout
-   Ichimoku cloud rejection
-   Return into Ichimoku cloud
-   Support/resistance touch

For every event, calculate forward behavior at:

``` text
1 trading day
3 trading days
5 trading days
10 trading days
```

The result should include:

-   event count;
-   bounce/failure count;
-   average forward return;
-   median forward return;
-   reversal strength;
-   regime breakdown;
-   sample size.

------------------------------------------------------------------------

# 8. Fundamental Analysis

Fundamental data must be **point-in-time**.

This means historical tests should use the date the financial statement
became publicly available rather than only the fiscal quarter-end date.

### Required categories

  Category        Metrics
  --------------- --------------------------------------------------
  Growth          Revenue Growth, EBITDA Growth, Net Profit Growth
  Profitability   ROE, ROA, EBITDA Margin, Net Profit Margin
  Leverage        Net Debt/EBITDA, Debt/Equity
  Liquidity       Current Ratio, Quick Ratio
  Valuation       P/E, P/B, EV/EBITDA
  Cash Flow       Operating Cash Flow, Cash Conversion

### Fundamental-change features

At minimum:

-   QoQ revenue change;
-   YoY revenue change;
-   QoQ/YoY EBITDA change;
-   QoQ/YoY net profit change;
-   margin change;
-   ROE change;
-   leverage change;
-   liquidity change;
-   valuation change;
-   operating cash-flow change.

Sector-specific metrics should be supported. The specification
explicitly warns against blindly applying industrial-company ratios to
banks.

------------------------------------------------------------------------

# 9. Feature Engineering

The feature layer should produce deterministic features such as:

``` text
daily_return
weekly_return
rolling_volatility
ATR
volume_zscore

relative_return_vs_XU100
relative_return_vs_sector
relative_return_vs_peer_median
sector_lag_score

distance_from_bollinger
distance_from_KAMA
distance_from_support
distance_from_resistance
distance_from_ichimoku_boundary

historical_reversal_count
reversal_strength_1d
reversal_strength_3d
reversal_strength_5d
reversal_strength_10d

weekday_label
multi_day_sequence

revenue_change
EBITDA_change
net_profit_change
margin_change
ROE_change
leverage_change

post_disclosure_abnormal_return

USDTRY_change
EURTRY_change
TCMB_rate_change
FED_rate_change
CPI_change

news_event_tags
speech_topic_tags
speech_stance_tags
```

Every feature should have a documented definition, source, timestamp
rule, and leakage behavior.

------------------------------------------------------------------------

# 10. Research Scenario 1 --- Sector Laggard / Catch-Up

## Objective

Find stocks that are materially underperforming a strong sector and test
whether historical evidence shows subsequent catch-up behavior.

The system must **not** equate "lagging" with "buy."

### Required process

1.  Build sector peer groups.
2.  Calculate stock return minus sector median/index return.
3.  Calculate the relative gap across multiple windows.
4.  Rank sector leaders and laggards.
5.  Measure subsequent 5/10/20-day relative performance.
6.  Combine technical evidence.
7.  Combine fundamental evidence.
8.  Combine macro context.
9.  Separate temporary laggards from structural laggards.
10. Backtest the rule across sectors and periods.
11. Report false positives.

### Suggested output

``` json
{
  "ticker": "AKBNK",
  "sector": "Banking",
  "sector_strength": "...",
  "relative_gap_20d": "...",
  "technical_state": "...",
  "fundamental_state": "...",
  "macro_state": "...",
  "historical_catchup_result": "...",
  "sample_size": 0,
  "action_state": "POTENTIAL_CATCH_UP_CANDIDATE"
}
```

The actual values must come from tools/data, never from the LLM.

------------------------------------------------------------------------

# 11. Research Scenario 2 --- Weekday and Multi-Day Patterns

Test:

-   Monday weakness → Friday strength
-   Three down days → two-day rebound
-   Post-large-down-day mean reversion
-   End-of-week continuation/reversal
-   Conditional patterns given XU100 direction
-   Conditional patterns given sector direction
-   Conditional patterns during macro-event weeks

Required analysis:

-   occurrence count;
-   mean return;
-   median return;
-   comparison to unconditional returns;
-   transaction costs;
-   market-regime breakdown;
-   out-of-sample stability.

### Multiple-testing warning

The system must explicitly account for the fact that searching many
weekday/multi-day combinations can create patterns by chance.

A discovered pattern is a **research hypothesis** until independently
verified.

------------------------------------------------------------------------

# 12. Research Scenario 3 --- Technical Reversal Patterns

The system should compare:

### Single-indicator conditions

Example:

``` text
Lower Bollinger Band touch
```

### Combined conditions

Example:

``` text
Lower Bollinger touch
+ RSI local trough
+ rising volume
+ flattening KAMA
```

The project specification also requires checking cases where the
technical context contradicts the reversal hypothesis, such as:

``` text
Bearish Supertrend
+
Price below Ichimoku Cloud
```

This prevents the system from treating every indicator event as a
successful reversal.

Required outputs:

-   number of events;
-   success/failure count;
-   average reversal;
-   median reversal;
-   forward return distribution;
-   regime stability;
-   comparison of single vs combined conditions.

------------------------------------------------------------------------

# 13. Research Scenario 4 --- Quarterly Fundamentals and Price Reaction

The central question is not:

> "Good earnings = price rises?"

Instead:

> "Are specific changes in fundamentals historically associated with
> different post-disclosure price reactions?"

### Required workflow

``` text
Financial statement
       │
       ▼
Public disclosure timestamp
       │
       ▼
Point-in-time fundamental state
       │
       ▼
Change calculation
       │
       ▼
Post-disclosure price window
       │
       ├── 1 day
       ├── 5 days
       └── 20 days
       │
       ▼
Abnormal return
       │
       ├── XU100
       └── Sector benchmark
```

Must support:

-   QoQ changes;
-   YoY changes;
-   profitability changes;
-   liquidity changes;
-   leverage changes;
-   valuation changes;
-   disclosure-date alignment;
-   abnormal returns;
-   interaction between fundamentals and technical state.

------------------------------------------------------------------------

# 14. Macro Context Layer

Required macro variables:

### Türkiye

-   USD/TRY
-   EUR/TRY
-   TCMB policy conditions
-   TÜİK CPI

### Global

-   Federal funds target range
-   FOMC policy changes

Optional:

-   industrial production;
-   unemployment;
-   confidence indicators;
-   commodity prices.

### Critical rule

Macro observations must be aligned by **publication timestamp**.

A revised or future observation must not be inserted into a historical
decision unless the experiment explicitly studies revisions.

------------------------------------------------------------------------

# 15. News and Speech Intelligence

News and public commentary are **contextual evidence**, not ground
truth.

### News pipeline

``` text
Source
  ↓
Publication timestamp
  ↓
Company / sector / macro tagging
  ↓
Event category
  ↓
Optional sentiment/stance
  ↓
Evidence metadata
```

Possible event categories:

-   earnings;
-   regulation;
-   FX;
-   interest rates;
-   commodity shock;
-   contract award;
-   geopolitical risk.

### Speech pipeline

For instructor-approved public videos:

``` text
Video
 ↓
Selected timestamped segment
 ↓
Speech-to-text
 ↓
Topic extraction
 ↓
Claim extraction
 ↓
Stance/context
 ↓
Uncertainty
 ↓
Deterministic verification where numerical claims exist
```

Every speech-derived record should retain:

-   URL;
-   speaker/channel;
-   publication time;
-   transcript time range;
-   extracted topic;
-   claim;
-   stance;
-   uncertainty.

Numerical claims from commentary must be checked against deterministic
data tools before becoming committed evidence.

------------------------------------------------------------------------

# 16. Finite Action Space

The strategy layer must use a finite action/state space.

Allowed educational states:

``` text
HOLD
WATCH
INVESTIGATE
POTENTIAL_CATCH_UP_CANDIDATE
TECHNICAL_REVERSAL_CANDIDATE
FUNDAMENTAL_IMPROVEMENT_CANDIDATE
REJECT_SIGNAL
ANALYSIS_UNSAFE
```

Optional `BUY`/`SELL` labels are permitted only as educational backtest
labels.

There must be **no broker integration or real order execution**.

------------------------------------------------------------------------

# 17. Backtesting and Verification

Every meaningful strategy or discovered pattern must be historically
verified.

### Mandatory safeguards

1.  Shift signals correctly.
2.  Prevent future information from entering historical decisions.
3.  Use financial-statement publication dates.
4.  Compare against Buy-and-Hold.
5.  Compare against XU100.
6.  Compare against a sector benchmark where possible.
7.  Include transaction costs.
8.  Include simple slippage assumptions.
9.  Use train/validation/test or rolling walk-forward for mined rules.
10. Report signal/event count.
11. Break results down by market regime.
12. Test out-of-sample stability.

### Required financial metrics

``` text
Cumulative Return
Sharpe Ratio
Maximum Drawdown
Win Rate
Benchmark Difference
```

A high return based on only a few events must be explicitly flagged.

------------------------------------------------------------------------

# 18. Optional Machine Learning

Machine learning is optional.

If implemented, it should support tasks such as:

-   direction classification;
-   abnormal-return classification;
-   defined event-outcome probability.

ML metrics must be separated from financial metrics.

  ML Evaluation      Financial Evaluation
  ------------------ ----------------------
  Accuracy           Cumulative Return
  Precision          Sharpe Ratio
  Recall             Maximum Drawdown
  F1                 Win Rate
  Confusion Matrix   Benchmark Difference

The project requires explaining why prediction accuracy does not
automatically imply a profitable strategy.

------------------------------------------------------------------------

# 19. MCP Tool Architecture

The LLM should access deterministic functionality through constrained
MCP tools.

Required tool concepts:

``` text
get_stock_history(ticker, start, end)

get_index_history(index, start, end)

calculate_indicators(series, config)

detect_reversal_events(series, event_config)

find_support_resistance(ohlcv, tolerance)

rank_sector_relative_strength(sector, horizon)

test_weekday_pattern(ticker, pattern, period)

get_fundamental_metrics(ticker, period)

calculate_fundamental_change(ticker, periods)

get_macro_context(date_range)

get_news_events(ticker/topic, date_range)

get_speech_features(video/source_id)

run_backtest(strategy_spec, universe, period)

check_data_quality(analysis_bundle)

build_evidence_bundle(analysis_id)
```

### Tool rule

The LLM should request calculations and interpret returned results. It
should not manually fabricate numerical values.

------------------------------------------------------------------------

# 20. Stateful Agent Harness

The workflow must be state-controlled.

``` text
START
  ↓
SELECT_UNIVERSE
  ↓
LOAD_MARKET_DATA
  ↓
CHECK_DATA_QUALITY
  ↓
CALCULATE_TECHNICALS
  ↓
RUN_SECTOR_RELATIVE_ANALYSIS
  ↓
RUN_PATTERN_AND_REVERSAL_ANALYSIS
  ↓
LOAD_FUNDAMENTALS
  ↓
LOAD_MACRO_CONTEXT
  ↓
LOAD_NEWS_AND_SPEECH_CONTEXT
  ↓
BUILD_EVIDENCE
  ↓
PREVIEW_STRATEGIES
  ↓
RUN_BACKTEST
  ↓
RISK_GATE
  ↓
GENERATE_EXPLANATION
  ↓
HUMAN_REVIEW
  ↓
LOG_AND_CLOSE
```

### State-control requirements

Each state should expose only its permitted MCP tools.

The LLM must not:

-   invent new actions;
-   skip data-quality validation;
-   skip backtesting where required;
-   bypass the risk gate;
-   directly execute external financial actions.

------------------------------------------------------------------------

# 21. Suggested State Permissions

  State                                 Allowed Operations
  ------------------------------------- -----------------------------
  `SELECT_UNIVERSE`                     Universe/sector metadata
  `LOAD_MARKET_DATA`                    Market history tools
  `CHECK_DATA_QUALITY`                  Data validation
  `CALCULATE_TECHNICALS`                Indicator/event tools
  `RUN_SECTOR_RELATIVE_ANALYSIS`        Sector ranking tools
  `RUN_PATTERN_AND_REVERSAL_ANALYSIS`   Pattern/event tools
  `LOAD_FUNDAMENTALS`                   Fundamental tools
  `LOAD_MACRO_CONTEXT`                  Macro tools
  `LOAD_NEWS_AND_SPEECH_CONTEXT`        Context tools
  `BUILD_EVIDENCE`                      Evidence builder
  `PREVIEW_STRATEGIES`                  Strategy construction
  `RUN_BACKTEST`                        Backtest tools
  `RISK_GATE`                           Quality/risk checks
  `GENERATE_EXPLANATION`                Read-only evidence access
  `HUMAN_REVIEW`                        Human decision input
  `LOG_AND_CLOSE`                       Decision/replay persistence

------------------------------------------------------------------------

# 22. Evidence Architecture

The system must distinguish:

### Observed Context

Everything calculated/observed during the analysis.

Example:

``` text
30+ technical/fundamental/macro/news features
```

### Committed Evidence Set

Only the evidence actually used to justify the final analytical state.

Example:

``` text
E1: Stock is 8.5 percentage points behind sector median over 20 days
E2: KAMA slope turned positive
E3: Lower Bollinger reversal succeeded in 11/17 comparable historical events
E4: Revenue and EBITDA growth improved in latest disclosed quarter
E5: Net Debt/EBITDA declined
E6: Macro regime is not flagged as hard-risk
E7: Backtest variant B outperformed benchmark after costs
```

The explanation generator may cite only evidence that exists in tool
outputs and has been committed to the evidence bundle.

------------------------------------------------------------------------

# 23. Data Quality and Risk Gate

## Hard blocks

The analysis must be blocked when:

-   future financial information enters an earlier historical date;
-   signal construction contains look-ahead bias;
-   ticker/history is wrong or broken;
-   price and financial periods are critically misaligned;
-   backtest uses unavailable information.

## Soft warnings

Examples:

-   macro data missing for a limited interval;
-   sparse news coverage;
-   low-quality transcript;
-   small technical-event sample;
-   temporarily small sector peer group.

## Gate outputs

``` text
PASS
PASS_WITH_WARNINGS
INVESTIGATE
ANALYSIS_UNSAFE
HARD_BLOCK
```

A failed quality gate must remain visible in the final result.

------------------------------------------------------------------------

# 24. Human-in-the-Loop

The system is explicitly human-in-the-loop.

Example:

``` text
Agent conclusion:
POTENTIAL_CATCH_UP_CANDIDATE

Human review:
REJECT

Reason:
Historical maximum drawdown is too high
```

The human decision and reason must be stored for future replay and
educational analysis.

The AI conclusion must never silently become a real market order.

------------------------------------------------------------------------

# 25. Memory Architecture

The project specifies three memory categories.

### Temporal Memory

Stores:

-   historical prices;
-   indicators;
-   macro series;
-   financial metrics;
-   event histories.

### Episodic Memory

Stores:

``` text
state
→ evidence
→ action
→ backtest result
→ human decision
```

### Procedural Memory

Stores:

-   approved workflow order;
-   tool permissions;
-   validation rules;
-   analysis templates.

A student implementation can use:

-   SQLite;
-   PostgreSQL;
-   Parquet;
-   CSV;
-   JSON;
-   Pandas structures.

Enterprise infrastructure is not required.

------------------------------------------------------------------------

# 26. Decision Log

Every completed analysis should be replayable.

Recommended record:

``` json
{
  "analysis_id": "unique-id",
  "ticker": "ASELS",
  "sector": "Technology / Defense",
  "analysis_timestamp": "...",
  "market_data_period": {
    "start": "...",
    "end": "..."
  },
  "data_versions": {},
  "publication_timestamps": [],
  "tools_called": [],
  "tool_outputs": [],
  "technical_state": {},
  "sector_state": {},
  "fundamental_state": {},
  "macro_state": {},
  "context_state": {},
  "evidence_bundle": {},
  "committed_evidence": [],
  "strategy_variant": "B",
  "backtest_result": {},
  "risk_gate": "PASS_WITH_WARNINGS",
  "agent_conclusion": "POTENTIAL_CATCH_UP_CANDIDATE",
  "agent_explanation": "...",
  "human_review": {
    "decision": "REJECT",
    "reason": "..."
  }
}
```

This is essential for reproducibility and replay.

------------------------------------------------------------------------

# 27. Strategy Variant Framework

Before committing to a conclusion, the harness should compare multiple
strategy definitions.

  Variant   Evidence
  --------- ---------------------------------------
  A         Technical only
  B         Technical + sector relative-value
  C         Technical + sector + fundamentals
  D         Structured C + macro
  E         Full D + verified news/speech context

All variants should use the same:

-   backtesting metrics;
-   benchmark definitions;
-   data-quality rules;
-   risk gates;
-   signal-timing rules.

This makes the contribution of each evidence layer measurable.

------------------------------------------------------------------------

# 28. Harness Experiments A--E

The course specification suggests five system versions.

### A --- Raw LLM

All data passed as text.

No deterministic tool requirement.

### B --- LLM + Tools

MCP tools perform calculations.

### C --- Tools + Stateful Harness

Tool permissions and ordered states are enforced.

### D --- C + Evidence + Quality Gate

Committed evidence and blocking rules are introduced.

### E --- D + Memory + Human Review

Replayable memory and human decisions are added.

### Harness-engineering metrics

Measure:

-   numerical hallucination rate;
-   invalid tool-call rate;
-   unsupported conclusion rate;
-   evidence completeness;
-   analysis reproducibility;
-   backtest correctness;
-   number of tool calls;
-   workflow latency/cost.

The final report should compare A--E rather than only presenting the
final system.

------------------------------------------------------------------------

# 29. Evaluation Metrics

## Research metrics

### Sector catch-up

-   subsequent relative return;
-   hit rate;
-   median catch-up size;
-   false-positive rate.

### Calendar patterns

-   occurrence count;
-   conditional mean return;
-   conditional median return;
-   out-of-sample stability;
-   cost-adjusted result.

### Technical reversal

-   bounce rate;
-   reversal strength;
-   forward-return distribution;
-   regime stability.

### Fundamental reaction

-   post-disclosure abnormal return;
-   horizon response;
-   sector-adjusted response.

### Trading/backtest

-   cumulative return;
-   Sharpe ratio;
-   maximum drawdown;
-   win rate;
-   benchmark difference.

### Optional ML

-   accuracy;
-   precision;
-   recall;
-   F1;
-   confusion matrix.

### Agent harness

-   hallucination rate;
-   tool-call validity;
-   evidence completeness;
-   reproducibility;
-   backtest correctness.

------------------------------------------------------------------------

# 30. Suggested Python API

The implementation should expose functions corresponding to the
specification:

``` python
load_universe()
get_stock_history()
get_index_history()
build_sector_peer_groups()

calculate_indicators()
calculate_bollinger_events()
calculate_kama_state()
calculate_supertrend_state()
calculate_ichimoku_state()
find_support_resistance()
calculate_reversal_strength()

rank_sector_laggards()
test_weekday_pattern()
detect_multiday_patterns()

get_fundamental_metrics()
calculate_quarterly_changes()
align_financial_disclosure_dates()

get_macro_context()
extract_news_events()
transcribe_finance_video_segment()
extract_speech_features()

build_evidence_bundle()
generate_strategy_variants()

run_backtest()
calculate_performance()

check_data_quality()
log_decision()
replay_analysis()
```

Function names are intentionally aligned with the project specification
to keep the implementation traceable to the requirements.

------------------------------------------------------------------------

# 31. Recommended Core Data Models

The project will be easier to maintain if the following conceptual
entities are implemented.

## `Stock`

``` text
ticker
yahoo_symbol
company_name
sector
universe_version
valid_from
valid_to
```

## `MarketObservation`

``` text
ticker
timestamp
open
high
low
close
adjusted_close
volume
source
retrieved_at
data_version
```

## `TechnicalSnapshot`

``` text
ticker
timestamp
SMA
EMA
KAMA
RSI
MACD
bollinger_upper
bollinger_middle
bollinger_lower
ATR
supertrend
ichimoku_state
volume_zscore
```

## `ReversalEvent`

``` text
event_id
ticker
timestamp
event_type
market_regime
indicator_state
volume_regime
forward_return_1d
forward_return_3d
forward_return_5d
forward_return_10d
reversal_strength
```

## `FundamentalSnapshot`

``` text
ticker
period
publication_timestamp
revenue
EBITDA
net_profit
ROE
ROA
EBITDA_margin
net_profit_margin
net_debt_to_EBITDA
debt_to_equity
current_ratio
quick_ratio
PE
PB
EV_EBITDA
operating_cash_flow
source
```

## `MacroObservation`

``` text
series
observation_timestamp
publication_timestamp
value
source
revision_status
```

## `Evidence`

``` text
evidence_id
analysis_id
source_tool
timestamp
claim
value
unit
committed
```

## `BacktestResult`

``` text
strategy_id
period
universe
signal_count
cumulative_return
sharpe
max_drawdown
win_rate
benchmark_difference
transaction_cost
slippage
out_of_sample
```

## `DecisionLog`

``` text
analysis_id
state_history
tool_calls
evidence_bundle
strategy_variants
risk_gate
agent_conclusion
human_review
created_at
```

------------------------------------------------------------------------

# 32. Reproducibility Requirements

Every experiment should record:

``` text
Experiment ID
Run timestamp
Universe version
Sector-map version
Data source
Data retrieval timestamp
Data version
Analysis period
Indicator configuration
Feature configuration
Strategy definition
Transaction cost assumption
Slippage assumption
Benchmark
Random seed, if applicable
Code version / commit hash
Risk-gate result
```

The same input configuration should produce the same deterministic
calculations whenever the underlying source data are unchanged.

------------------------------------------------------------------------

# 33. Leakage Prevention Checklist

Before accepting a historical result, verify:

-   [ ] No future closing prices are used to construct a decision at
    time `t`.
-   [ ] Financial data are available by their public disclosure
    timestamp.
-   [ ] Macro data use publication availability, not only observation
    date.
-   [ ] News uses publication timestamp.
-   [ ] Speech features use only material available by the analysis
    timestamp.
-   [ ] Feature windows do not extend into the future.
-   [ ] Backtest execution occurs after signal generation.
-   [ ] Benchmark returns use the correct time window.
-   [ ] No future universe membership silently enters a historical
    experiment.
-   [ ] No manually selected "successful" events are used as the entire
    sample.
-   [ ] Out-of-sample evaluation is separated from rule discovery.

------------------------------------------------------------------------

# 34. Quality Gates Before a Research Result Is Published

A research result should not be presented as a strong conclusion unless:

``` text
DATA
 └── valid?
      ├── no → HARD_BLOCK
      └── yes
           ↓
TIMING
 └── point-in-time correct?
      ├── no → HARD_BLOCK
      └── yes
           ↓
SAMPLE
 └── enough observations?
      ├── weak → INVESTIGATE / WARNING
      └── adequate
           ↓
BACKTEST
 └── verified?
      ├── no → INVESTIGATE
      └── yes
           ↓
RISK
 └── leakage / instability?
      ├── yes → ANALYSIS_UNSAFE
      └── no
           ↓
EVIDENCE
 └── traceable?
      ├── no → INVESTIGATE
      └── yes
           ↓
HUMAN REVIEW
```

------------------------------------------------------------------------

# 35. End-to-End Example

Example research question:

> "Find BIST 100 stocks that are lagging a strong sector but may be
> entering a historically favorable catch-up state."

Expected workflow:

``` text
1. Select the 30-stock study universe
2. Load OHLCV and XU100
3. Check data quality
4. Build sector peer groups
5. Calculate sector-relative performance
6. Rank leaders and laggards
7. Calculate technical states
8. Search historical reversal/catch-up events
9. Load point-in-time fundamentals
10. Load macro context
11. Load timestamped news/speech context
12. Build observed-context bundle
13. Build committed evidence set
14. Generate strategy variants A–E
15. Backtest candidates
16. Apply risk/data-quality gate
17. Generate evidence-backed explanation
18. Human reviews result
19. Save complete decision log
20. Enable replay
```

The final result should explain **why** an analytical state was produced
and exactly which evidence supports it.

------------------------------------------------------------------------

# 36. Development Roadmap

Do not try to implement the entire system at once.

## Phase 0 --- Project foundation

-   [ ] Create repository
-   [ ] Create Python environment
-   [ ] Add configuration system
-   [ ] Add logging
-   [ ] Add tests
-   [ ] Add `.env.example`
-   [ ] Add universe configuration

## Phase 1 --- Market data

-   [ ] Implement `get_stock_history`
-   [ ] Implement `get_index_history`
-   [ ] Download OHLCV
-   [ ] Normalize timestamps
-   [ ] Handle missing values
-   [ ] Cache data
-   [ ] Version datasets

**Deliverable:** reproducible market-data pipeline.

## Phase 2 --- Technical engine

-   [ ] SMA
-   [ ] EMA
-   [ ] KAMA
-   [ ] RSI
-   [ ] MACD
-   [ ] Bollinger Bands
-   [ ] ATR
-   [ ] Supertrend
-   [ ] Ichimoku
-   [ ] Support/resistance
-   [ ] Technical event storage

**Deliverable:** deterministic technical-analysis module.

## Phase 3 --- Sector research

-   [ ] Build peer groups
-   [ ] Calculate sector median returns
-   [ ] Calculate relative gaps
-   [ ] Rank laggards/leaders
-   [ ] Test 5/10/20-day catch-up
-   [ ] Calculate false positives

**Deliverable:** sector catch-up research report.

## Phase 4 --- Calendar patterns

-   [ ] Weekday returns
-   [ ] Multi-day sequences
-   [ ] Conditional patterns
-   [ ] Regime analysis
-   [ ] Multiple-testing controls
-   [ ] Out-of-sample tests

**Deliverable:** calendar-pattern report.

## Phase 5 --- Reversal research

-   [ ] Event detector
-   [ ] Forward-return engine
-   [ ] Single-indicator tests
-   [ ] Combined-indicator tests
-   [ ] Market-regime breakdown

**Deliverable:** technical reversal-event database/report.

## Phase 6 --- Fundamentals

-   [ ] Fintables integration
-   [ ] Point-in-time storage
-   [ ] Quarterly change calculations
-   [ ] Disclosure-date alignment
-   [ ] Abnormal return calculations

**Deliverable:** fundamental reaction report.

## Phase 7 --- Macro/context

-   [ ] TCMB/EVDS
-   [ ] TÜİK
-   [ ] Federal Reserve
-   [ ] News metadata
-   [ ] Speech metadata/STT

**Deliverable:** macro/context evidence layer.

## Phase 8 --- Backtest engine

-   [ ] Strategy specification
-   [ ] Signal shifting
-   [ ] Costs
-   [ ] Slippage
-   [ ] Benchmarking
-   [ ] Walk-forward/out-of-sample
-   [ ] Performance metrics

**Deliverable:** verification harness.

## Phase 9 --- MCP

-   [ ] MCP server
-   [ ] Tool schemas
-   [ ] Tool validation
-   [ ] Tool permissions
-   [ ] Error handling
-   [ ] Tool-call logging

**Deliverable:** deterministic MCP tool layer.

## Phase 10 --- Agent harness

-   [ ] Orchestrator
-   [ ] Specialized agents
-   [ ] State machine
-   [ ] State-specific permissions
-   [ ] Evidence builder
-   [ ] Risk gate
-   [ ] Human review

**Deliverable:** controlled agentic workflow.

## Phase 11 --- Memory and replay

-   [ ] Temporal memory
-   [ ] Episodic memory
-   [ ] Procedural memory
-   [ ] Decision logs
-   [ ] Replay mechanism

**Deliverable:** reproducible stateful harness.

## Phase 12 --- Experiments A--E

-   [ ] Raw LLM
-   [ ] LLM + tools
-   [ ] Stateful harness
-   [ ] Evidence + quality gate
-   [ ] Memory + human review
-   [ ] Compare engineering metrics

**Deliverable:** final harness experiment report.

------------------------------------------------------------------------

# 37. Testing Strategy

Testing must exist at several levels.

## Unit tests

Test deterministic functions:

``` text
indicator calculations
return calculations
sector-relative calculations
event detection
fundamental changes
abnormal returns
performance metrics
```

## Leakage tests

Construct synthetic examples where future information exists and ensure
the system rejects it.

## Integration tests

Verify:

``` text
data → indicators → research → evidence → backtest
```

## MCP tests

Verify:

-   valid tool arguments;
-   invalid tool arguments;
-   unavailable data;
-   permission restrictions;
-   deterministic outputs.

## Harness tests

Verify that:

-   invalid state transitions are rejected;
-   mandatory quality states cannot be skipped;
-   unauthorized tools cannot be called;
-   risk-gate failures stop the workflow;
-   every analysis produces a replayable log.

------------------------------------------------------------------------

# 38. Configuration Example

A future `config/indicators.yaml` can follow this pattern:

``` yaml
technical:
  sma:
    windows: [20, 50, 200]

  ema:
    windows: [12, 26]

  rsi:
    period: 14

  bollinger:
    period: 20
    stddev: 2

  atr:
    period: 14

  forward_horizons:
    - 1
    - 3
    - 5
    - 10
```

Backtest configuration should separately define:

``` yaml
backtest:
  transaction_cost_bps: 0
  slippage_bps: 0
  benchmark: XU100
  horizons: [5, 10, 20]
```

The actual assumptions used in the project report must be documented
rather than hidden in code.

------------------------------------------------------------------------

# 39. Environment Variables

Do not commit secrets.

Example `.env.example`:

``` env
# Optional LLM provider
LLM_API_KEY=

# Optional Fintables integration
FINTABLES_API_KEY=

# Optional news provider
NEWS_API_KEY=

# Database
DATABASE_URL=sqlite:///data/project.db

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
```

The exact provider/API availability should be verified before
implementation. The architecture should allow mock/local implementations
so the project does not become dependent on one external service.

------------------------------------------------------------------------

# 40. First Milestone

The first meaningful milestone should **not** be the AI agent.

Build this first:

``` text
30-stock universe
      ↓
Yahoo OHLCV
      ↓
Data validation
      ↓
Technical indicators
      ↓
Sector-relative returns
      ↓
Reversal events
      ↓
Basic backtest
      ↓
CSV/Parquet research outputs
```

Only after these deterministic components work should the agent layer be
added.

This follows the project's central principle: **the agent orchestrates
and explains deterministic analytical tools; it does not replace them.**

------------------------------------------------------------------------

# 41. Minimum Viable Project (MVP)

If development time is limited, the MVP should contain:

### Required

-   [ ] 30-stock universe
-   [ ] OHLCV retrieval
-   [ ] XU100 benchmark
-   [ ] SMA/EMA/KAMA
-   [ ] RSI/MACD
-   [ ] Bollinger/ATR
-   [ ] Supertrend
-   [ ] Ichimoku
-   [ ] Sector-relative ranking
-   [ ] Technical reversal events
-   [ ] Weekday pattern analysis
-   [ ] Point-in-time fundamental framework
-   [ ] Macro framework
-   [ ] Backtesting
-   [ ] Evidence bundle
-   [ ] Risk/data-quality gate
-   [ ] MCP tool layer
-   [ ] Stateful agent workflow
-   [ ] Decision log

### Can be implemented later

-   [ ] Full news provider integration
-   [ ] Speech-to-text automation
-   [ ] Optional machine learning
-   [ ] Advanced database infrastructure
-   [ ] Rich dashboard/UI

------------------------------------------------------------------------

# 42. Final Deliverables Checklist

The final project should contain:

-   [ ] Python source code
-   [ ] notebooks
-   [ ] environment instructions
-   [ ] fixed/versioned BIST study universe
-   [ ] sector map
-   [ ] data dictionary
-   [ ] technical reversal report
-   [ ] sector laggard/catch-up report
-   [ ] weekday/multi-day pattern report
-   [ ] quarterly fundamentals/price-reaction report
-   [ ] macro/context integration report
-   [ ] MCP tool definitions
-   [ ] stateful harness
-   [ ] decision log
-   [ ] replay demonstration
-   [ ] backtesting results
-   [ ] benchmark comparisons
-   [ ] A--E agent-harness experiment comparison
-   [ ] final technical report
-   [ ] classroom demonstration

------------------------------------------------------------------------

# 43. Final Quality Checklist

Before submission:

### Data

-   [ ] Sources documented
-   [ ] Data versions recorded
-   [ ] Universe version recorded
-   [ ] Missing data handled
-   [ ] Publication timestamps preserved

### Research

-   [ ] Four mandatory scenarios implemented
-   [ ] Results have sufficient sample context
-   [ ] False positives reported
-   [ ] Regime breakdown included
-   [ ] Out-of-sample checks performed

### Backtest

-   [ ] No look-ahead bias
-   [ ] Correct signal timing
-   [ ] Transaction costs documented
-   [ ] Slippage documented
-   [ ] Benchmarks included
-   [ ] Drawdown reported
-   [ ] Sample size reported

### Agent

-   [ ] Tool calls constrained
-   [ ] States enforced
-   [ ] Quality gate enforced
-   [ ] Evidence is traceable
-   [ ] Unsupported conclusions rejected
-   [ ] Human review recorded
-   [ ] Replay works

### Documentation

-   [ ] Architecture documented
-   [ ] Data dictionary complete
-   [ ] MCP tools documented
-   [ ] Experiments A--E documented
-   [ ] Limitations documented
-   [ ] Educational-use warning included

------------------------------------------------------------------------

# 44. What the Final System Should Demonstrate

The project should ultimately demonstrate that an agentic
financial-analysis system is valuable not because an LLM can produce a
confident financial sentence, but because:

1.  its data are correctly timed;
2.  its calculations are reproducible;
3.  its tools are constrained;
4.  its evidence is inspectable;
5.  historical claims are verified;
6.  unsafe analysis is blocked;
7.  decisions can be replayed;
8.  a human can challenge the conclusion.

The LLM's primary role is therefore:

``` text
ORCHESTRATE
    ↓
SELECT APPROVED TOOLS
    ↓
READ DETERMINISTIC OUTPUTS
    ↓
MERGE EVIDENCE
    ↓
CHECK CONTRADICTIONS
    ↓
REQUEST VERIFICATION
    ↓
EXPLAIN
```

It is **not**:

``` text
GUESS
  ↓
INVENT NUMBERS
  ↓
DECLARE A STOCK WINNER
  ↓
TRADE
```

------------------------------------------------------------------------

# 45. Source Basis

This README is derived from the uploaded **CSE-481 Engineering Economics
--- Integrated BIST 100 Agentic Financial Analytics Harness** project
specification. The specification defines the mandatory research
scenarios, 30-stock study universe, data sources,
technical/fundamental/macro/context layers, MCP tools, stateful agent
architecture, evidence model, risk gates, backtesting requirements,
memory, human review, experiments A--E, evaluation metrics, methodology,
expected outcomes, and final deliverables.

The project specification also states that its numerical scenario
examples are hypothetical and are not current market signals or
investment recommendations.

------------------------------------------------------------------------

## License / Educational Notice

This repository is an educational coursework project.

It is intended for:

-   financial data engineering education;
-   quantitative research methodology;
-   backtesting education;
-   agentic-system engineering;
-   MCP/tool orchestration;
-   reproducibility and explainability research.

It is **not** intended to provide personalized investment advice or
execute real financial transactions.

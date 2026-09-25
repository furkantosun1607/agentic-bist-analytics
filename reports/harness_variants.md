# Harness Variant Comparison A-E

Variants:
- A: raw LLM
- B: LLM + tools
- C: tools + enforced states
- D: C + evidence/quality gate
- E: D + memory/human review

## Summary

| variant   | description               |   question_count |   unsupported_number_count |   invalid_tool_call_count |   evidence_complete_count |   replayable_count |   quality_gate_count |   human_review_count |   score | status   |
|:----------|:--------------------------|-----------------:|---------------------------:|--------------------------:|--------------------------:|-------------------:|---------------------:|---------------------:|--------:|:---------|
| A         | raw LLM                   |                5 |                          4 |                         5 |                         1 |                  2 |                    1 |                    4 |     0   | limited  |
| B         | LLM + tools               |                5 |                          0 |                         4 |                         1 |                  2 |                    1 |                    4 |     0.2 | limited  |
| C         | tools + enforced states   |                5 |                          0 |                         0 |                         1 |                  2 |                    1 |                    4 |     0.2 | limited  |
| D         | C + evidence/quality gate |                5 |                          0 |                         0 |                         5 |                  2 |                    5 |                    4 |     0.4 | limited  |
| E         | D + memory/human review   |                5 |                          0 |                         0 |                         5 |                  5 |                    5 |                    5 |     1   | ok       |

Limitations:
- This compares harness capabilities on fixed question requirements.
- It does not execute a live LLM.
- Financial strategy A-E and harness A-E are separate comparison tracks.

## Deterministic Experiment Run

Status: measured_deterministic.
Fixed question set: `config\harness_questions.csv`.
Execution policy: this run does not call a live LLM; it deterministically scores harness capabilities against fixed question requirements.

## Question Outcomes

| variant   | passed   |   question_count |
|:----------|:---------|-----------------:|
| A         | False    |                5 |
| B         | False    |                4 |
| B         | True     |                1 |
| C         | False    |                4 |
| C         | True     |                1 |
| D         | False    |                3 |
| D         | True     |                2 |
| E         | True     |                5 |

Measured-run limitations:
- This is a deterministic harness capability experiment, not a live LLM benchmark.
- It measures whether a harness design can support required controls; it does not judge answer prose quality.
- Financial strategy A-E and harness A-E are separate comparison tracks.

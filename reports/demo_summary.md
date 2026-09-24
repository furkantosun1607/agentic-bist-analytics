# Classroom Demo Summary

Command: `python -m scripts.demo --offline`

This demo performs no network calls. It validates the fixed universe, regenerates the report index and final technical report, checks for an optional cached market dataset, and records whether the run is infrastructure-only.

| Check | Status | Detail |
| --- | --- | --- |
| settings | pass | loaded config\settings.yaml |
| universe | pass | 30 fixed symbols validated |
| report_generation | pass | wrote reports\report_index.md and reports\final_technical_report.md |
| report_manifest | pass | all report metadata paths are present |
| cache | pass | 31 cached market files found in data\cache |

## Cached Dataset

To populate a live cache before class, run `python -m scripts.fetch_market_data` with source access available. The offline demo command can then be rerun without live source availability and will read the cache status from `data/cache`.

## Interpretation

Warnings do not create measured financial findings. They identify missing live/cache inputs that must be populated before empirical return, risk or strategy-comparison claims can be made.

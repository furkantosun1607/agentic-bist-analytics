# Classroom Demo Summary

Command: `python -m scripts.demo --offline`

This demo performs no network calls. It validates the fixed universe, regenerates the report index and final technical report, checks cached market data, checks RSS news/context artifacts, and records whether the run is infrastructure-only.

| Check | Status | Detail |
| --- | --- | --- |
| settings | pass | loaded config\settings.yaml |
| universe | pass | 30 fixed symbols validated |
| report_generation | pass | wrote reports\report_index.md and reports\final_technical_report.md |
| report_manifest | pass | all report metadata paths are present |
| cache | pass | 31 cached market files found in data\cache |
| rss_raw_cache | pass | 259 rows found in data\rss\news_raw.jsonl |
| rss_normalized_cache | pass | 259 rows found in data\rss\news.jsonl |
| rss_matched_cache | pass | 259 rows found in data\rss\news_matched.jsonl |
| rss_context | pass | 51 context rows and 24 active rows found in data\rss\news_context.csv |
| rss_source_health | pass | reports\rss_source_health.md present |

## Cached Dataset

To populate a live cache before class, run `python -m scripts.fetch_market_data` with source access available. The offline demo command can then be rerun without live source availability and will read the cache status from `data/cache`.

## RSS News Context

To refresh RSS context, run `python -m scripts.fetch_rss_news`, `python -m scripts.normalize_rss_news`, `python -m scripts.match_news_aliases`, then `python -m scripts.build_news_context`. The offline demo reads those local artifacts and does not fetch live news.

## Interpretation

Warnings do not create measured financial findings. They identify missing live/cache inputs that must be populated before empirical return, risk or strategy-comparison claims can be made.

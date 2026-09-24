# Context Data Dictionary

`src.context` normalizes macro, news, and public-video context into a point-in-time schema.

Required common columns:
- `context_id`: stable unique context id.
- `context_type`: `macro`, `news`, or `video`.
- `scope`: context scope such as `macro`, `company`, `sector`, or `global`.
- `observed_period_start`: period start for the fact or event.
- `observed_period_end`: period end for the fact or event.
- `publication_timestamp`: when the context became public.
- `download_timestamp`: when the record was collected.
- `source`: source name.
- `source_access`: `public`, `licensed`, or `instructor_approved`.

Macro fields:
- `indicator`: one of `usd_try`, `eur_try`, `tcmb_policy_rate`, `tuik_inflation`, `fed_policy_rate`.
- `value`: numeric observed value.
- `unit`: value unit such as `TRY`, `%`, or `bps`.

News/video fields:
- `title`: source title.
- `claim`: short verified claim used by the evidence bundle.
- `source_url`: URL or stable source locator.
- `video_timestamp`: required for `video` records.

Rules:
- Do not include inaccessible, unlicensed, or unverifiable records.
- Keep observation period, publication timestamp, and download timestamp separate.
- Missing source or timestamp metadata must block use in evidence.

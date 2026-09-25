# Strategy Variant Comparison A-E

Variants:
- A: technical
- B: technical + sector
- C: B + fundamentals
- D: C + macro
- E: D + verified news/video context

RSS context policy:
- RSS context metadata can make Variant E context availability explicit.
- RSS context does not create trade signals by itself.
- Future-dated or missing source metadata remains a warning/blocking quality issue.

## Summary

| variant   | description                                                             | status      | components                                     | missing_components   | data_start   | data_end   |   trading_cost_bps |   slippage_bps | rss_context_status   | rss_context_evidence_count   | rss_context_source_count   | rss_context_latest_timestamp   | rss_context_warnings   | rss_context_evidence_urls                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | signal_count   | trade_count   | symbol_count   | average_gross_return   | median_gross_return   | average_cost_adjusted_return   | median_cost_adjusted_return   | cumulative_return      | sharpe_ratio       | maximum_drawdown    | win_rate           | cumulative_benchmark_return   | benchmark_difference    | average_benchmark_relative_return   | average_sector_relative_return   |
|:----------|:------------------------------------------------------------------------|:------------|:-----------------------------------------------|:---------------------|:-------------|:-----------|-------------------:|---------------:|:---------------------|:-----------------------------|:---------------------------|:-------------------------------|:-----------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:---------------|:--------------|:---------------|:-----------------------|:----------------------|:-------------------------------|:------------------------------|:-----------------------|:-------------------|:--------------------|:-------------------|:------------------------------|:------------------------|:------------------------------------|:---------------------------------|
| A         | technical                                                               | ok          | technical                                      |                      | 2021-01-04   | 2026-09-24 |                 10 |              5 | <NA>                 | <NA>                         | <NA>                       | <NA>                           | <NA>                   | <NA>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | 8523           | 8523          | 30             | 0.006823681666946388   | 0.0035502643370828313 | 0.005323681666946387           | 0.0020502643370828313         | 60369213925.40134      | 7.038828566875953  | -0.9999516191124553 | 0.5127302592983691 | 8.85303113698029e+24          | -8.85303113698023e+24   | -0.0008241739170294696              | nan                              |
| B         | technical + sector                                                      | ok          | technical+sector                               |                      | 2021-01-04   | 2026-09-24 |                 10 |              5 | <NA>                 | <NA>                         | <NA>                       | <NA>                           | <NA>                   | <NA>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | 16982          | 16976         | 30             | 0.007419764744517687   | 0.004052694032600335  | 0.005919764744517703           | 0.0025526940326003346         | 1.609701857147616e+27  | 11.477426140413396 | -0.9999999998260855 | 0.5173185673892554 | 1.1248226292365498e+53        | -1.1248226292365498e+53 | -0.0006621419113466504              | nan                              |
| C         | technical + sector + fundamentals                                       | ok          | technical+sector+fundamentals                  |                      | 2021-01-04   | 2026-09-24 |                 10 |              5 | <NA>                 | <NA>                         | <NA>                       | <NA>                           | <NA>                   | <NA>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | 17359          | 17353         | 30             | 0.006874367121506237   | 0.003553283863618084  | 0.005374367121506252           | 0.002053283863618084          | 1.2833965381235537e+23 | 10.35555184753628  | -0.9999999999986225 | 0.5139169019766034 | 1.9598826060517138e+50        | -1.9598826060517138e+50 | -0.0007003664761078628              | nan                              |
| D         | technical + sector + fundamentals + macro                               | unavailable | technical+sector+fundamentals+macro            | macro                | 2021-01-04   | 2026-09-24 |                 10 |              5 | <NA>                 | <NA>                         | <NA>                       | <NA>                           | <NA>                   | <NA>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | <NA>           | <NA>          | <NA>           | <NA>                   | <NA>                  | <NA>                           | <NA>                          | <NA>                   | <NA>               | <NA>                | <NA>               | <NA>                          | <NA>                    | <NA>                                | <NA>                             |
| E         | technical + sector + fundamentals + macro + verified news/video context | unavailable | technical+sector+fundamentals+macro+news_video | macro+news_video     | 2021-01-04   | 2026-09-24 |                 10 |              5 | available            | 125                          | 51                         | 2026-09-24T10:44:06+00:00      |                        | https://www.yenisafak.com/galeri/ekonomi/altinda-son-dakika-gram-ve-ceyrek-altin-ne-kadar-4858196;https://www.yenisafak.com/ekonomi/petrolde-gerileme-hizlandi-abd-iran-temasi-fiyatlari-frenledi-4858231;https://www.yenisafak.com/galeri/ekonomi/altin-icin-kritik-saatler-altin-fiyatlari-yukselecek-mi-dusecek-mi-piyasalar-bu-veriye-kilitlendi-4858257;https://www.yeniakit.com.tr/haber/gun-icinde-inisli-cikisli-grafik-izledi-altinin-kilogram-fiyati-geriledi-2024479.html;https://www.yenisafak.com/ekonomi/new-york-borsasi-dususle-acildi-4858426 | <NA>           | <NA>          | <NA>           | <NA>                   | <NA>                  | <NA>                           | <NA>                          | <NA>                   | <NA>               | <NA>                | <NA>               | <NA>                          | <NA>                    | <NA>                                | <NA>                             |

Limitations:
- Missing-source variants are marked unavailable; values are not invented.
- RSS news density is context evidence only and is not reported as a performance claim.
- All variants use the same provided price data, benchmark hooks and cost assumptions.
- This report is historical research infrastructure, not investment advice.

## Measured Variant Run

Status: measured_partial.
Signal policy: executable components are mapped from fixed P35 signals without selecting on future returns.
Component policy: weekday research signals are not counted as A-E strategy components; RSS context metadata is not a trade signal.

## Component Signal Counts

| component    |   signal_count |
|:-------------|---------------:|
| fundamentals |            377 |
| sector       |           8459 |
| technical    |           8523 |

## Unavailable Executable Components

- `macro`
- `news_video`

## RSS Context Metadata

RSS context path: `data\rss\news_context.csv`.
RSS context is included only as Variant E evidence metadata and does not create `news_video` trade signals.

Measured-run limitations:
- Variants D and E remain unavailable until executable macro and news/video signals are defined.
- Available variants are trade-level historical research outputs, not investment recommendations.

# Context Sources Report

Status: RSS news context pipeline is implemented for cached, timestamped, legally accessible RSS records. Macro and video context schemas remain available; video is not required for the current RSS-only flow.

Context types:
- Macro: USD/TRY, EUR/TRY, TCMB policy rate, TUIK inflation and Fed policy-rate records.
- News: RSS company, sector and macro event records with publication and fetch timestamps.
- Video: optional instructor-approved public-video segments with timestamps and verified claims.

## RSS News Context

Context rows: 51
Ticker rows: 30
Tickers with RSS context: 3
Entities with RSS context: 24

| Entity | News count | Sources | Latest published | Evidence URLs |
| --- | --- | --- | --- | --- |
| sector:Holding / Investment | 18 | 4 | 2026-09-24T10:43:35+00:00 | https://www.yenisafak.com/ekonomi/aramco-oyak-ile-ortaklik-yolunda-4858183<br>https://www.yenisafak.com/ekonomi/bakan-bolat-new-yorkta-mesaji-verdi-turkiyeye-yatirim-cagrisi-4858208<br>https://www.yeniakit.com.tr/haber/secici-finansman-mekanizmalari-guclendirilsin-2024372.html |
| sector:Technology / Defense | 15 | 4 | 2026-09-24T10:36:08+00:00 | https://www.yenisafak.com/ekonomi/celik-kubbe-icin-kritik-imza-aselsan-ve-roketsan-arasinda-sozlesme-imzalandi-4858255<br>https://www.yeniakit.com.tr/haber/sunar-yatirim-110dan-fazla-ulkeye-ihracat-yapiyor-2024382.html<br>https://www.yenisafak.com/video/ekonomi/muharebe-sahasinda-kurallari-degistiren-vurus-roketsanin-karaok-fuzesi-ilk-kez-bir-hava-hedefini-imha-etti-4858266 |
| macro:commodities | 14 | 4 | 2026-09-24T08:43:17+00:00 | https://www.yenisafak.com/galeri/ekonomi/altinda-son-dakika-gram-ve-ceyrek-altin-ne-kadar-4858196<br>https://www.yenisafak.com/ekonomi/petrolde-gerileme-hizlandi-abd-iran-temasi-fiyatlari-frenledi-4858231<br>https://www.yenisafak.com/galeri/ekonomi/altin-icin-kritik-saatler-altin-fiyatlari-yukselecek-mi-dusecek-mi-piyasalar-bu-veriye-kilitlendi-4858257 |
| macro:fx | 14 | 4 | 2026-09-24T09:33:03+00:00 | https://www.yenisafak.com/galeri/ekonomi/steve-mcqueenin-ferrari-275-gtbsi-acik-artirmada-tahmini-fiyati-20-milyon-dolar-steve-mcqueen-kimdir-kac-yasinda-neden-oldu-4858099<br>https://www.yeniakit.com.tr/haber/dolar-ve-euro-gune-nasil-basladi-piyasalar-bu-rakamlarla-acildi-2024343.html<br>https://www.yenisafak.com/galeri/ekonomi/altin-icin-kritik-saatler-altin-fiyatlari-yukselecek-mi-dusecek-mi-piyasalar-bu-veriye-kilitlendi-4858257 |
| sector:Electric Utilities | 12 | 2 | 2026-09-24T10:44:06+00:00 | https://www.yenisafak.com/ekonomi/aramco-oyak-ile-ortaklik-yolunda-4858183<br>https://www.yenisafak.com/ekonomi/kuresel-piyasalar-enerji-arzina-yonelik-iyimserliklerden-destek-buluyor-4858212<br>https://www.milliyet.com.tr/dunya/terminator-zirvesi-trumpin-xiyi-karsiladigi-torene-damga-vuran-anlar-7666466 |
| sector:Petroleum / Refining | 7 | 3 | 2026-09-24T08:43:17+00:00 | https://www.yenisafak.com/ekonomi/petrolde-gerileme-hizlandi-abd-iran-temasi-fiyatlari-frenledi-4858231<br>https://www.yenisafak.com/ekonomi/new-york-borsasi-dususle-acildi-4858426<br>https://www.cnnturk.com/ekonomi/hurmuzde-gemi-vuruldu-petrol-yeniden-yukseldi-3470424 |
| macro:global_rates | 6 | 3 | 2026-09-24T08:04:55+00:00 | https://www.ft.com/content/ba73ddd6-9fc0-49ba-909e-7305a23844dc?syn-25a6b1a6=1<br>https://finance.yahoo.com/markets/crypto/articles/bitcoin-cleared-85-000-week-225254328.html<br>https://www.ft.com/content/d2e5ed9c-a123-4275-afc7-14b75b9337a0?syn-25a6b1a6=1 |
| macro:policy_rate | 5 | 3 | 2026-09-23T17:18:42+00:00 | https://www.yeniakit.com.tr/haber/finansal-hizmetler-guven-endeksi-yukseldi-2024377.html<br>https://www.yenisafak.com/ekonomi/ecb-yeni-avro-banknotlari-2030da-tedavule-girecek-4858336<br>https://www.cnnturk.com/ekonomi/tcmb-acikladi-enflasyon-beklentileri-eylulde-nasil-degisti-3470304 |
| sector:Brokerage / Capital Markets | 4 | 3 | 2026-09-23T19:32:48+00:00 | https://www.yenisafak.com/ekonomi/spk-acikladi-iste-tasfiye-edilecek-fonlardaki-yatirimci-sayisi-4858219<br>https://www.yenisafak.com/ekonomi/sermaye-piyasasi-islemleri-sorusturmalarinda-11-zanlinin-mal-varligina-el-konuldu-4858394<br>https://www.yeniakit.com.tr/haber/bir-gida-sirketi-daha-halka-arz-basvurusu-yapti-2024544.html |
| sector:Automotive | 3 | 1 | 2026-09-24T09:52:11+00:00 | https://www.yenisafak.com/galeri/ekonomi/otomobil-devi-5-binden-fazla-araci-geri-cagiriyor-cocuklari-sakin-oturtmayin-4858306<br>https://www.yenisafak.com/galeri/ekonomi/ucuz-sifir-araba-almak-isteyenlere-mujde-dusuk-fiyata-alici-bulan-arabalar-listelendi-4858620<br>https://www.yenisafak.com/galeri/ekonomi/luks-otomobil-markasi-tamamen-elektriklendi-112-milyon-tlye-satista-4858641 |
| sector:Construction | 3 | 2 | 2026-09-24T07:13:26+00:00 | https://www.yeniakit.com.tr/haber/oyak-sirketleri-musiad-expoda-uluslararasi-is-dunyasiyla-bulusuyor-2024355.html<br>https://www.yeniakit.com.tr/haber/marmara-bolgesinde-yatirim-atagi-d-100-hattina-yeni-sanayi-ussu-2024435.html<br>https://www.yenisafak.com/ekonomi/guven-endeksinde-sektorler-ayristi-perakende-yukseldi-insaat-geriledi-4858583 |
| sector:Food & Beverage | 3 | 2 | 2026-09-24T06:42:38+00:00 | https://www.yenisafak.com/ekonomi/yildiz-holding-yonetim-kurulu-baskani-ve-ceosu-mehmet-tutuncu-cop31-is-forumunda-es-baskanlik-yapacak-4858303<br>https://www.yeniakit.com.tr/haber/bir-gida-sirketi-daha-halka-arz-basvurusu-yapti-2024544.html<br>https://www.yenisafak.com/ekonomi/bu-baharatlara-dikkat-3-urunde-yasakli-boya-bulundu-4858568 |
| sector:Healthcare | 3 | 2 | 2026-09-24T09:56:44+00:00 | https://www.yeniakit.com.tr/haber/saglik-sanayii-buyuk-bir-ekonomiye-evrilebilir-2024403.html<br>https://www.milliyet.com.tr/ekonomi/bakan-kacir-uluslararasi-yatirimlarda-ileri-teknolojinin-one-cikacagini-soyledi-7666519<br>https://www.milliyet.com.tr/gundem/karamanda-kari-kocanin-supheli-olumu-cesetler-siyanur-var-girmeyin-notuyla-bulundu-7666496 |
| ticker:THYAO | 3 | 2 | 2026-09-24T01:00:00+00:00 | https://www.yenisafak.com/ekonomi/thyden-dev-ucak-siparisi-boeingden-150-adet-b737-max-alacak-4858437<br>https://www.yeniakit.com.tr/haber/thy-boeingden-150-adet-ucak-satin-alacak-2024547.html<br>https://www.yenisafak.com/ekonomi/thy-150-boeing-aliyor-4858542 |
| macro:inflation | 2 | 1 | 2026-09-23T13:38:54+00:00 | https://www.cnnturk.com/ekonomi/tcmb-acikladi-enflasyon-beklentileri-eylulde-nasil-degisti-3470304<br>https://www.cnnturk.com/ekonomi/oecdnin-turkiye-raporu-yayimlandi-iste-buyume-ve-enflasyon-tahminleri-3470356 |
| sector:Basic Metals / Steel | 2 | 2 | 2026-09-23T22:09:00+00:00 | https://www.yenisafak.com/ekonomi/celik-kubbe-icin-kritik-imza-aselsan-ve-roketsan-arasinda-sozlesme-imzalandi-4858255<br>https://www.yeniakit.com.tr/haber/spkdan-iki-sirkete-165-milyar-liralik-bedelsiz-artirim-izni-2024562.html |
| sector:Telecommunications | 2 | 1 | 2026-09-24T10:09:00+00:00 | https://www.yeniakit.com.tr/haber/surdurulebilir-gelecegin-tasarlanmasina-yatirim-yapiyor-turk-telekomdan-kuresel-katki-2024457.html<br>https://www.yeniakit.com.tr/haber/turk-telekom-stratejik-isbirligine-imza-atti-2024630.html |
| sector:Transportation / Airlines | 2 | 2 | 2026-09-24T08:17:35+00:00 | https://www.yenisafak.com/ekonomi/hepsiburada-teknofest-guneydoguda-yer-alacak-4858343<br>https://www.milliyet.com.tr/ekonomi/bakan-bolat-turkiye-ile-abdnin-ticaret-hacminin-50-milyar-dolara-ulasacagini-soyledi-7666516 |
| ticker:TTKOM | 2 | 1 | 2026-09-24T10:09:00+00:00 | https://www.yeniakit.com.tr/haber/surdurulebilir-gelecegin-tasarlanmasina-yatirim-yapiyor-turk-telekomdan-kuresel-katki-2024457.html<br>https://www.yeniakit.com.tr/haber/turk-telekom-stratejik-isbirligine-imza-atti-2024630.html |
| sector:Banking | 1 | 1 | 2026-09-23T07:59:31+00:00 | https://www.yenisafak.com/galeri/ekonomi/masak-para-transferi-limitlerini-guncelledi-milyonlarca-banka-musterisini-ilgilendiren-karar-yururluge-girdi-4858259 |

Decision-time rule:
- Only RSS records with `published_timestamp <= decision_timestamp` are included.
- The default lookback window is 7 days.
- Alias matches are context evidence, not trade signals.

Limitations:
- RSS source availability and publication timestamps can vary by publisher.
- Source access and licensing must be respected before records are used in final conclusions.
- This report is historical research infrastructure, not investment advice.

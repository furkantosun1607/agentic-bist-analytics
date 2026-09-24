# Implementation Plan

Bu dosya, CSE-481 Engineering Economics BIST 100 Research Harness projesinin ana takip dokumanidir. Her gelistirme adimi bu plana gore yapilacak ve tamamlanan islerden sonra ilgili faz durumu, notlari ve gerekiyorsa kabul kriterleri guncellenecektir.

## Plan Kullanimi

- Her faz kucuk tutulmustur; amac, tek bir gelistirme oturumunda uygulanabilir ve test edilebilir parcalar halinde ilerlemektir.
- Bir faz tamamlanmadan sonraki faza gecilmez; ancak blokaj varsa `Blocked` olarak isaretlenir ve sebebi yazilir.
- Her kod degisikliginden sonra ilgili fazin `Status`, `Completed`, `Notes` ve varsa `Tests` alanlari guncellenir.
- Sayisal sonuc ureten her gelistirme, veri kaynagi, veri donemi, varsayim ve limitasyon bilgisini raporlayabilecek sekilde tasarlanir.
- Gelecek bilgi sizintisi, hatali tarih eslesmesi veya kritik kaynak eksikligi tespit edilirse ilgili analiz sonucu uretilmez; durum kalite kapisinda bloklanir.

## Durum Etiketleri

- `Not Started`: Henuz baslanmadi.
- `In Progress`: Aktif olarak gelistiriliyor.
- `Blocked`: Dis kaynak, karar veya kritik eksik nedeniyle ilerleyemiyor.
- `Done`: Kod, temel dogrulama ve plan guncellemesi tamamlandi.

## Guncel Ozet

| Alan | Durum |
| --- | --- |
| Proje durumu | RSS demo status ready |
| Son guncelleme | 2026-09-24 |
| Aktif faz | P29 - Strategy Variant E RSS Context Integration |
| Kritik sonraki hedef | RSS context'i Strategy Variant E availability ve evidence akisina baglamak |

## Degismez Proje Kurallari

- Sabit evren README'deki 30 hisse ile baslar ve `config/universe.csv` icinde tutulur.
- Deneyler arasinda hisse listesi sessizce degistirilmez; farkliliklar raporlanir.
- Her tarihsel karar icin yalnizca karar ani `t` itibariyla kamuya acik olan bilgi kullanilir.
- Finansal verilerde ceyrek sonu tarihi tek basina sinyal tarihi sayilmaz; aciklanma zamani ayrica izlenir.
- Eksik veya dogrulanamayan kaynaklar uydurulmaz; raporda eksik olarak isaretlenir.
- LLM fiyat, oran veya getiri hesaplamaz; hesaplamalar deterministik Python araclariyla yapilir.
- Her rapor veri donemi, kaynak, orneklem sayisi, varsayimlar ve limitasyonlar icerir.
- RSS haberleri gercek zamanli dinlenmez; zamanlanmis polling ile cekilir, `published_timestamp` ve `fetched_timestamp` birlikte saklanir.
- Haber context'i tek basina al/sat aksiyonu uretmez; yalnizca kanit, risk ve Strategy Variant E girdisi olarak kullanilir.

## Hedef Dosya Yapisi

```text
README.md
implementationplan.md
requirements.txt
config/universe.csv
config/settings.yaml
config/rss_sources.yaml
config/news_aliases.csv
src/data.py
src/rss_news.py
src/indicators.py
src/research.py
src/backtest.py
src/mcp_server.py
src/harness.py
notebooks/
reports/
tests/
```

## Fazlar

### P00 - Repository Baseline

Status: `Done`

Goal: Projenin minimum dosya/dizin iskeletini kurmak ve gelistirme akisini standartlastirmak.

Deliverables:
- `requirements.txt`
- `config/`, `src/`, `reports/`, `notebooks/`, `tests/` dizinleri
- Bos veya minimal modul dosyalari

Acceptance:
- Hedef dosya yapisi repoda mevcut olur.
- Python import yapisi temel olarak calisir.
- Plan dosyasinda aktif faz guncellenir.

Completed:
- `requirements.txt` eklendi.
- `config/`, `src/`, `reports/`, `notebooks/`, `tests/` dizinleri olusturuldu.
- `src` altinda minimal modul dosyalari ve package initializer eklendi.
- `tests/test_imports.py` ile temel import smoke testi eklendi.

Tests:
- `python -c "from src import backtest, data, harness, indicators, mcp_server, research; print('imports ok')"` passed.
- `python -m pytest tests/test_imports.py"` not run: local ortamda `pytest` henuz kurulu degil.

Notes:
- README proje durumunu planned olarak belirtiyordu; P00 sonunda repo temel gelistirme iskeletine sahip.

### P01 - Fixed Universe And Data Dictionary

Status: `Done`

Goal: README'deki 30 hisselik sabit evreni ve basit sektor etiketlerini kaynak veri olarak dondurmak.

Deliverables:
- `config/universe.csv`
- Universe kolon sozlugu veya README uyumlu dokumantasyon notu
- Ticker/yahoo_symbol/sector validasyon testi

Acceptance:
- CSV tam 30 satir icerir.
- `ticker`, `yahoo_symbol`, `sector` kolonlari eksiksizdir.
- Yinelenen ticker yoktur.

Completed:
- README'deki 30 hisselik sabit evren `config/universe.csv` olarak eklendi.
- `config/universe_dictionary.md` ile `ticker`, `yahoo_symbol`, `sector` kolonlari dokumante edildi.
- `src.data.load_universe` ve `src.data.validate_universe` yardimcilari eklendi.
- Universe testleri standart `unittest` ile calisacak sekilde eklendi.

Tests:
- `python -m unittest discover -s tests` passed: 4 tests.
- `python -c "from src.data import load_universe, validate_universe; members=load_universe(); print(len(members)); print(validate_universe(members))"` returned `30` and `[]`.

Notes:
- Sektorlerde tek hisseli gruplar olabilir; bu durum ileride `insufficient peers` olarak ele alinacak.
- CSV 31 satirdir: 1 header + 30 universe member.

### P02 - Settings And Runtime Configuration

Status: `Done`

Goal: Veri donemi, cache yolu, maliyet varsayimlari ve rapor ciktilari icin merkezi ayar dosyasi olusturmak.

Deliverables:
- `config/settings.yaml`
- Ayarlari okuyan yardimci fonksiyon
- Varsayilan cache/report path tanimlari

Acceptance:
- Kod sabit pathlere bagimli kalmaz.
- Trading cost/slippage varsayimlari ayarlardan okunabilir.
- Test ve demo icin tek ayar noktasi vardir.

Completed:
- `config/settings.yaml` merkezi runtime ayar dosyasi olarak eklendi.
- `src/settings.py` ile typed settings dataclass'lari ve YAML loader eklendi.
- Universe, cache, reports, notebooks ve decision log pathleri proje kokune gore normalize ediliyor.
- Market data benchmark/source, adjusted price policy, backtest timing, nonzero cost/slippage, horizons ve kalite ayarlari merkezi hale getirildi.
- Settings testleri eklendi.

Tests:
- `python -m unittest discover -s tests` passed: 8 tests.
- `python -c "from src.settings import load_settings; s=load_settings(); print(s.paths.universe); print(s.backtest.trading_cost_bps, s.backtest.slippage_bps)"` returned the resolved universe path and `10.0 5.0`.
- `python -c "from src import settings; print(settings.load_settings().market_data.benchmark_symbol)"` returned `XU100.IS`.

Notes:
- API key veya gizli bilgi dosyaya yazilmadi.
- Ilk maliyet varsayimi `trading_cost_bps: 10` ve `slippage_bps: 5`; P14 sirasinda gerekirse gerekceli olarak revize edilecek.

### P03 - Market Data Adapter And Cache

Status: `Done`

Goal: Hisse ve XU100 fiyatlarini indirip tekrar kullanilabilir cache formatinda saklamak.

Deliverables:
- `src/data.py` market data adapter
- Dated OHLCV cache
- XU100 benchmark verisi
- Eksik sembol raporu

Acceptance:
- Her fiyat kaydinda observation date ve download timestamp izlenir.
- Adjusted price politikasi dokumante edilir.
- Kaynak ulasilamazsa demo icin cache kullanilabilir.

Completed:
- `src.data` icinde yfinance destekli, provider enjekte edilebilir market data adapter eklendi.
- Fiyat kayitlari `symbol`, `date`, OHLCV, `adj_close`, `source`, `download_timestamp` kolonlariyla normalize ediliyor.
- Symbol bazli CSV cache path/write/read yardimcilari eklendi.
- XU100 benchmark sembolunu hisse sembolleriyle birlikte fetch eden `fetch_market_data` akisi eklendi.
- Eksik semboller icin structured `MissingSymbol` kaydi ve `reports/missing_symbols.csv` yazicisi eklendi.
- `python -m scripts.fetch_market_data` ile ayarlardaki universe ve benchmark icin cache ureten script eklendi.
- `data/.gitkeep` eklendi; runtime cache dosyalari `.gitignore` nedeniyle repoya alinmayacak.

Tests:
- `python -m unittest discover -s tests` passed: 12 tests.
- `python -c "import scripts.fetch_market_data as f; print(callable(f.main))"` returned `True`.
- `python -c "from src.data import load_universe; from src.settings import load_settings; s=load_settings(); print(len([m.yahoo_symbol for m in load_universe(s.paths.universe)]), s.market_data.benchmark_symbol)"` returned `30 XU100.IS`.

Notes:
- Yahoo/yfinance README'de fiyat kaynagi olarak belirtilmis.
- Testler ag cagrisina bagli degil; fake provider ile cache, benchmark ve missing-symbol davranisi dogrulandi.
- Canli fiyat cache'i bu fazda repoya commitlenmedi. Gerekirse `python -m scripts.fetch_market_data` komutu yerel cache'i uretir.

### P04 - Data Validation And Point-In-Time Checks

Status: `Done`

Goal: Veri kalitesi, tarih sirasi ve gelecek bilgi sizintisi icin bloklayici kontroller eklemek.

Deliverables:
- Data-quality validator
- Missing history/date mismatch warnings
- Leakage blocking checks
- Temel testler

Acceptance:
- Kritik tarih hatasi analiz sonucunu `ANALYSIS_UNSAFE` seviyesine tasiyabilir.
- Eksik veri uyarilari raporlanir.
- Gelecek getiri sinyal girdisi olarak kullanilamaz.

Completed:
- `src/validation.py` data-quality ve point-in-time safety modulu olarak eklendi.
- `QualityIssue` ve `QualityReport` ile warning/blocking issue modeli olusturuldu.
- Gate ciktisi `ANALYSIS_SAFE` veya `ANALYSIS_UNSAFE` olarak standardize edildi.
- Price history kontrolleri eklendi: bos veri, eksik kolon, kucuk orneklem, parse edilemeyen tarih, sirali olmayan tarih, duplicate tarih, numeric olmayan veya non-positive fiyat, high/low uyumsuzlugu, negatif volume, invalid download timestamp ve price-date-after-download.
- Market dataset validator eklendi; missing symbol ve expected-but-not-fetched durumlari warning olarak raporlanir.
- Point-in-time record validator eklendi; publication timestamp decision time'dan sonraysa blocking future leakage uretir.
- Future outcome feature kolonlari icin leakage blok kontrolu eklendi.
- Validation testleri eklendi.

Tests:
- `python -m unittest discover -s tests` passed: 20 tests.
- `python -c "from src.validation import validate_no_future_outcome_columns; print(validate_no_future_outcome_columns(['rsi','next_return']).gate_status)"` returned `ANALYSIS_UNSAFE`.

Notes:
- Bu faz sonraki tum analizlerin guvenlik temelidir.
- Missing source veya small sample warning olarak kalir; future-information leakage ve kritik tarih uyumsuzluklari `ANALYSIS_UNSAFE` uretir.

### P05 - Core Technical Indicators

Status: `Done`

Goal: Deterministik teknik indikator hesaplamalarini eklemek.

Deliverables:
- `src/indicators.py`
- SMA, EMA, KAMA, RSI, MACD, Bollinger Bands, ATR, Supertrend, Ichimoku
- Support/resistance ve volume yardimci hesaplari
- Hesaplama testleri

Acceptance:
- Fonksiyonlar LLM'e hesap yaptirmadan numerik sonuc uretir.
- Eksik veri pencerelerinde beklenen NaN/uyari davranisi vardir.
- En az bir kucuk sentetik veri testi bulunur.

Completed:
- `src/indicators.py` deterministik teknik indikator modulu olarak dolduruldu.
- SMA, EMA, KAMA, RSI, MACD, Bollinger Bands, True Range, ATR, Supertrend, Ichimoku hesaplari eklendi.
- Rolling support/resistance ve volume/relative volume yardimcilari eklendi.
- `add_all_indicators` ile normalize OHLCV tablosuna cekirdek indikator setini ekleyen birlesik fonksiyon eklendi.
- Sentetik OHLCV verisiyle indikator hesaplama testleri eklendi.

Tests:
- `python -m unittest discover -s tests` passed: 26 tests.
- `python -c "from tests.test_indicators import sample_prices; from src.indicators import add_all_indicators; df=add_all_indicators(sample_prices(80)); print(len(df.columns), df[['sma_20','rsi_14','supertrend']].tail(1).to_dict('records')[0])"` returned 38 columns with populated `sma_20`, `rsi_14` and `supertrend`.

Notes:
- Kural optimizasyonu yapilmayacak; az sayida acik ve tekrar edilebilir indikator kullanilacak.
- Eksik pencere donemlerinde pandas'in standart `NaN` davranisi korunur.

### P06 - Technical Event Detectors

Status: `Done`

Goal: Scenario 3 icin timestamped teknik olaylari tespit etmek.

Deliverables:
- Bollinger lower/middle/upper tests
- RSI peak/trough events
- Supertrend flips
- KAMA changes
- Ichimoku interactions
- Support/resistance touches

Acceptance:
- Her event sinyal zamani ve knowable timestamp tasir.
- Event ciktisi structured data olarak uretilebilir.
- Her event ailesi icin en az bir smoke test vardir.

Completed:
- `src/events.py` teknik event detector modulu olarak eklendi.
- Standart event ciktisi `symbol`, `event_family`, `event_type`, `event_date`, `known_at`, `value`, `reference`, `details` kolonlariyla tanimlandi.
- Bollinger lower/middle/upper testleri ve cross eventleri eklendi.
- RSI peak/trough ve threshold exit eventleri eklendi.
- Supertrend flip up/down eventleri eklendi.
- KAMA price cross ve slope turn eventleri eklendi.
- Ichimoku conversion/base cross ve cloud break eventleri eklendi.
- Support/resistance touch eventleri toleransli olarak eklendi.
- `detect_all_events` her detector'i ayri calistirip hatalari `DetectorError` olarak toplar; tek detector hatasi diger eventleri dusurmez.
- Missing-column ve event-date parse problemleri icin acik hata mesajlari eklendi.
- Event detector smoke testleri eklendi.

Tests:
- `python -m unittest discover -s tests` passed: 31 tests.
- `python -c "from tests.test_events import event_frame; from src.events import detect_all_events; r=detect_all_events(event_frame()); print(len(r.events), len(r.errors), sorted(r.events.event_family.unique()))"` returned 21 events, 0 errors and all six event families.

Notes:
- Her aile icin bir kucuk detector yeterli; asiri parametre taramasi yapilmayacak.
- Event `known_at` simdilik gunluk kapanis sonrasi Istanbul timestamp'i olarak `T18:10:00+03:00` formatinda yazilir.

### P07 - Sector Catch-Up Research

Status: `Done`

Goal: Scenario 1 sektor catch-up analizini uygulamak.

Deliverables:
- 20 gunluk getiri eksi sektor peer mediani
- 5/10/20 gun sonrasi relatif getiri olcumleri
- Peer count ve insufficient peers isaretleme
- `reports/sector_catch_up.*`

Acceptance:
- Hisse kendisiyle karsilastirilmaz.
- Tek hisseli sektorlerde sonuc yerine `insufficient peers` raporlanir.
- False positive ve sample count raporda yer alir.

Completed:
- `src.research.run_sector_catch_up` ile 20 gunluk lookback return, peer median, catch-up score ve 5/10/20 benzeri horizon bazli ileri relatif getiri hesaplama altyapisi eklendi.
- Hisse kendisiyle karsilastirilmez; peer median hesaplari ayni sektor ve tarih icinde self-exclusion ile yapilir.
- Tek hisseli sektorler `insufficient_peers` olarak isaretlenir.
- Eksik history, forward history ve peer forward history durumlari structured `status` degeriyle raporlanir.
- Laggard, false-positive ve rank-in-sector alanlari eklendi.
- `ResearchError` ve `ResearchInputError` ile horizon/input problemleri icin acik error handling eklendi.
- `write_sector_catch_up_report` markdown rapor yazicisi eklendi.
- `reports/sector_catch_up.md` olcum uydurmayan baslangic raporu olarak eklendi.
- Sector catch-up unit testleri eklendi.

Tests:
- `python -m unittest discover -s tests` passed: 36 tests.
- `python -c "from tests.test_research_sector_catch_up import prices, universe; from src.research import run_sector_catch_up; r=run_sector_catch_up({'AAA.IS': prices('AAA.IS',[100,90,95,98,102,105]), 'BBB.IS': prices('BBB.IS',[100,110,111,112,113,114])}, universe()[:2], lookback_days=1, horizons=(2,)); print(len(r.observations), len(r.errors), sorted(r.observations.status.unique()))"` returned 12 observations, 0 errors and expected status values.

Notes:
- Fixed 30 disindaki PDF ornekleri kullanilmayacak.
- Canli/cache market data henuz repoda olmadigi icin `reports/sector_catch_up.md` measured result icermeyen uygulama durumu raporudur.

### P08 - Weekday And Multi-Day Pattern Research

Status: `Done`

Goal: Scenario 2 hafta ici ve 2-5 gunluk takvim desenlerini test etmek.

Deliverables:
- Predefined weekday pattern tests
- 2-5 trading day pattern tests
- Unconditional return baseline
- Costs and market-regime split
- `reports/weekday_patterns.*`

Acceptance:
- Occurrence count, average/median return ve cost-adjusted sonuc raporlanir.
- Multiple-testing riski acikca belirtilir.
- Unseen period stabilitesi icin alan hazirdir.

Completed:
- `src.research.run_weekday_patterns` ile weekday ve 2-5 gunluk holding pattern analizleri eklendi.
- Pattern gozlem semasi `symbol`, `date`, `weekday`, `pattern_type`, `pattern_name`, `holding_days`, `status`, gross/cost-adjusted return, unconditional baseline, market regime ve period split alanlariyla tanimlandi.
- `summarize_weekday_patterns` ile occurrence count, average/median return, cost-adjusted return ve unconditional baseline ozeti eklendi.
- Trading cost ve slippage gross return'den dusulerek cost-adjusted return hesaplanir.
- Benchmark verisi verilirse market regime benchmark returnu uzerinden; verilmezse sembol returnu uzerinden hesaplanir.
- `unseen_start_date` ile `selection` / `unseen` split destegi eklendi.
- Eksik kolon, invalid holding day, duplicate date ve benchmark hazirlama problemleri icin acik error handling eklendi.
- `write_weekday_patterns_report` markdown rapor yazicisi eklendi.
- `reports/weekday_patterns.md` olcum uydurmayan baslangic raporu olarak eklendi.
- Weekday/multi-day pattern unit testleri eklendi.

Tests:
- `python -m unittest discover -s tests` passed: 42 tests.
- `python -c "from tests.test_research_weekday_patterns import prices, benchmark; from src.research import run_weekday_patterns; r=run_weekday_patterns({'AAA.IS': prices()}, benchmark_prices=benchmark(), holding_days=(1,2,5), regime_lookback_days=3, unseen_start_date='2024-02-01'); print(len(r.observations), len(r.summary), len(r.errors), sorted(r.observations.pattern_type.unique()))"` returned 105 observations, 30 summary rows, 0 errors and weekday/multi_day types.

Notes:
- Hipotetik yuzdeler sonuc gibi yazilmayacak.
- Canli/cache market data henuz repoda olmadigi icin `reports/weekday_patterns.md` measured result icermeyen uygulama durumu raporudur.
- Multiple-testing riski rapor yazicisinda acikca belirtilir.

### P09 - Technical Reversal Research

Status: `Done`

Goal: Scenario 3 teknik reversal olaylarini ileri getirilerle karsilastirmak.

Deliverables:
- Next 1/3/5/10-day returns
- Individual vs combined signals
- Bounce/failure counts
- Market-regime comparison
- `reports/technical_reversals.*`

Acceptance:
- Event timestamp sonrasi uygulanabilir ilk islem noktasi dikkate alinir.
- Return distribution ve failure cases raporda gorunur.
- Combined signal kurallari onceden tanimli olur.

Completed:
- `src.research.run_technical_reversals` ile teknik eventleri 1/3/5/10 benzeri horizonlarda ileri getirilerle karsilastiran analiz eklendi.
- Eventler, event tarihinden sonraki ilk uygun trading day ile entry alir; event gunu kapanisi sinyal bilgisi olarak kalir.
- Observation semasi `symbol`, event family/type/date, `known_at`, `signal_group`, horizon, status, entry/exit date-close, forward return, bounce ve market regime alanlariyla tanimlandi.
- Individual event sonuclari ve ayni sembol/tarihteki coklu eventler icin `combined` sinyal grubu eklendi.
- Bounce/failure counts, bounce rate, average/median return ve market-regime kirilimli summary eklendi.
- Eksik price history, eksik event kolonlari, duplicate date, invalid horizon ve benchmark hazirlama problemleri icin acik error handling eklendi.
- `write_technical_reversals_report` markdown rapor yazicisi eklendi.
- `reports/technical_reversals.md` olcum uydurmayan baslangic raporu olarak eklendi.
- Technical reversal unit testleri eklendi.

Tests:
- `python -m unittest discover -s tests` passed: 48 tests.
- `python -c "from tests.test_research_technical_reversals import prices, events; from src.research import run_technical_reversals; r=run_technical_reversals({'AAA.IS': prices()}, {'AAA.IS': events()}, horizons=(1,3,5,10), regime_lookback_days=1); print(len(r.observations), len(r.summary), len(r.errors), sorted(r.observations.signal_group.unique()))"` returned 16 observations, 15 summary rows, 0 errors and combined/individual signal groups.

Notes:
- P05 ve P06 tamamlanmadan baslanmaz.
- Canli/cache market data henuz repoda olmadigi icin `reports/technical_reversals.md` measured result icermeyen uygulama durumu raporudur.
- Combined signal kurali: ayni sembol ve ayni event tarihinde iki veya daha fazla teknik event varsa ayri bir `combined` observation uretilir.

### P10 - Fundamentals Data Schema

Status: `Done`

Goal: Ceyreklik finansal veriler icin point-in-time sema ve import akisi olusturmak.

Deliverables:
- Fundamentals schema
- Disclosure timestamp alani
- Revenue/profit/margin/debt/cash-flow fields
- Bank vs industrial metric ayrimi icin kategori alani

Acceptance:
- Observation period, publication time ve download time ayri tutulur.
- Eksik disclosure timestamp durumunda analiz bloklanabilir veya eksik raporlanir.
- Kaynak bilgisi her kayitta yer alir.

Completed:
- `src/fundamentals.py` point-in-time fundamentals schema ve import modulu olarak eklendi.
- Normalized schema; `ticker`, `yahoo_symbol`, `sector`, `metric_profile`, `period_end`, `period_type`, `disclosure_timestamp`, `download_timestamp`, `source`, `currency` ve temel finansal metrik alanlarini kapsar.
- Revenue/profit/margin icin ileride kullanilacak gelir tablosu alanlari; debt/cash-flow analizi icin bilanço ve nakit akisi alanlari eklendi.
- Banking sektorleri icin `metric_profile=bank`, diger sektorler icin `metric_profile=industrial` ayrimi eklendi.
- CSV import ve DataFrame normalize akisi row-level error handling ile eklendi; hatali satirlar valid satirlari dusurmez.
- Eksik disclosure timestamp import seviyesinde reddedilir; quarter-end tek basina sinyal tarihi olarak kabul edilmez.
- Fundamentals kayitlari `PointInTimeRecord` listesine cevrilerek P04 kalite kapisi ile uyumlu hale getirildi.
- `config/fundamentals_dictionary.md` ve header-only `config/fundamentals_template.csv` eklendi.
- Fundamentals schema/import testleri eklendi.

Tests:
- `python -m unittest discover -s tests` passed: 55 tests.
- `python -c "from tests.test_fundamentals import raw_records, universe; from src.fundamentals import normalize_fundamentals; r=normalize_fundamentals(raw_records(), universe()); print(len(r.records), len(r.errors), sorted(r.records.metric_profile.unique()))"` returned 2 records, 0 errors and bank/industrial profiles.

Notes:
- Fintables README'de finansal kaynak olarak belirtilmis; erisim kosullari kontrol edilecek.
- Bu fazda canli Fintables erisimi yapilmadi; sema ve import akisi hazirlandi.

### P11 - Quarterly Fundamentals Research

Status: `Done`

Goal: Scenario 4 finansal degisimler ile aciklama sonrasi getirileri karsilastirmak.

Deliverables:
- QoQ/YoY growth calculations
- 1/5/20-day post-disclosure returns
- XU100 and sector-relative returns
- `reports/quarterly_fundamentals.*`

Acceptance:
- Quarter-end tarihi sinyal tarihi olarak kullanilmaz.
- Bankalar sanayi sirketi metrikleriyle korlemesine degerlendirilmez.
- Disclosure timestamp eksikse sonuc guvenli sekilde sinirlandirilir.

Completed:
- `src.research.run_quarterly_fundamentals` ile point-in-time fundamentals kayitlari disclosure timestamp sonrasi fiyat getirilerine baglandi.
- QoQ ve YoY degisim hesaplari eklendi; quarterly kayitlarda YoY icin 4 ceyrek once, annual kayitlarda 1 onceki annual kayit kullanilir.
- Industrial metric seti revenue, net income, gross/operating margin, debt-to-assets, operating cash flow ve free cash flow alanlarini kapsar.
- Bank metric seti net interest income, net income, assets-to-equity ve liabilities-to-assets alanlarini kapsar; bankalar industrial margin metrikleriyle degerlendirilmez.
- Entry, disclosure tarihinden sonraki ilk trading day olarak tanimlandi; quarter-end tarihi sinyal tarihi olarak kullanilmaz.
- 1/5/20 benzeri horizonlarda post-disclosure return, benchmark-relative return ve same-sector peer-relative return alanlari eklendi.
- Eksik price history, eksik disclosure timestamp, invalid horizon, duplicate dates ve tarih uyumsuzluklari icin acik error/status handling eklendi.
- `write_quarterly_fundamentals_report` markdown rapor yazicisi eklendi.
- `reports/quarterly_fundamentals.md` olcum uydurmayan baslangic raporu olarak eklendi.
- Quarterly fundamentals research unit testleri eklendi.

Tests:
- `python -m unittest discover -s tests` passed: 63 tests.
- `python -c "from tests.test_research_quarterly_fundamentals import normalized_fundamentals, prices; from src.research import run_quarterly_fundamentals; f=normalized_fundamentals(); r=run_quarterly_fundamentals(f, {'ASELS.IS': prices('ASELS.IS'), 'FROTO.IS': prices('FROTO.IS', start=200, step=.5), 'AKBNK.IS': prices('AKBNK.IS', start=50, step=.25)}, benchmark_prices=prices('XU100.IS', start=1000, step=2), horizons=(1,5,20)); print(len(r.observations), len(r.summary), len(r.errors), sorted(r.observations.metric_profile.unique()))"` returned 117 observations, 33 summary rows, 0 errors and bank/industrial profiles.

Notes:
- P10 tamamlanmadan baslanmaz.
- Canli veya manuel dogrulanmis fundamentals verisi henuz repoda olmadigi icin `reports/quarterly_fundamentals.md` measured result icermeyen uygulama durumu raporudur.
- Same-sector peer relative return, sadece fundamentals kayitlarindan sektoru bilinen ayni sektor sembolleriyle hesaplanir.

### P12 - Macro, News And Video Context

Status: `Done`

Goal: Makro, haber ve public-video baglamini kaynak ve timestamp ile kaydetmek.

Deliverables:
- Macro records: USD/TRY, EUR/TRY, policy rate, inflation, Fed changes
- Legally accessible news event records
- Instructor-approved public video segment records
- `reports/context_sources.*`

Acceptance:
- Her baglam kaydinda source, observed period, publication time ve download time vardir.
- Lisans veya erisim sorunu olan kaynaklar dahil edilmez.
- Eksik kaynaklar uydurulmadan raporlanir.

Completed:
- `src/context.py` macro, news ve video context semasi ve import akisi olarak eklendi.
- Context kayitlari `context_id`, `context_type`, `scope`, observed period, publication timestamp, download timestamp, source ve source access metadata'siyle normalize ediliyor.
- `source_access` yalnizca `public`, `licensed` veya `instructor_approved` degerlerini kabul edecek sekilde sinirlandi.
- Macro kayitlari USD/TRY, EUR/TRY, TCMB policy rate, TUIK inflation ve Fed policy rate indikatorleriyle sinirlandi; numeric value zorunlu tutuldu.
- News/video kayitlarinda title, claim ve source URL zorunlu; video kayitlarinda ayrica segment timestamp zorunlu tutuldu.
- Import akisi row-level error handling ile kuruldu; hatali satirlar valid satirlari dusurmuyor.
- Context kayitlari P04 point-in-time validator icin `PointInTimeRecord` listesine cevrilebiliyor.
- Historical decision timestamp icin public olan context kayitlarini filtreleyen yardimci eklendi.
- `config/context_dictionary.md`, `config/context_template.csv` ve `reports/context_sources.md` eklendi.
- Context schema/import testleri eklendi.

Tests:
- `python -m unittest discover -s tests` passed: 70 tests.

Notes:
- TCMB/EVDS, TUIK ve Federal Reserve kaynaklari README'de belirtilmis.
- Bu fazda canli makro/haber/video kaynagi cekilmedi; sema, import akisi ve kaynak uygunluk raporu hazirlandi.
- Gercek kaynaklar ve lisans/erisim kosullari veri doldurma sirasinda dogrulanacak; kaynak uydurma yapilmadi.

### P13 - Backtest Engine

Status: `Done`

Goal: Sinyaller icin temel tarihsel degerlendirme motorunu kurmak.

Deliverables:
- `src/backtest.py`
- Entry/exit timing rules
- Buy-and-Hold, XU100 and sector benchmark comparison hooks
- Signal count tracking

Acceptance:
- Sinyal bilinebilir olduktan once trade acilmaz.
- Future returns yalnizca outcome olarak kullanilir.
- Her backtest structured result dondurur.

Completed:
- `src/backtest.py` point-in-time guvenli backtest motoru olarak dolduruldu.
- Signal input semasi `signal_id`, `symbol`, `known_at`, opsiyonel `horizon`, `direction` ve `source` alanlariyla desteklendi.
- Entry kuralı `known_at` timestamp'inden sonraki ilk trading day olarak uygulanir; sinyal bilinmeden once trade acilmaz.
- Entry fiyatinda `open` varsa kullanilir, yoksa `close` fallback olarak kullanilir.
- Exit kuralı horizon sonrasi kapanis fiyatidir.
- Long-only trade generation eklendi; unsupported direction acik `status` ile raporlanir.
- Missing price history, insufficient forward history ve invalid price history durumlari structured status/error olarak ele alinir.
- XU100 benchmark, sector benchmark ve buy-and-hold comparison hook'lari eklendi.
- Signal count, tradable trade count ve temel gross/relative return summary alanlari eklendi.
- `write_backtest_report` markdown rapor yazicisi ve `reports/backtest.md` baslangic raporu eklendi.
- Backtest unit testleri eklendi.

Tests:
- `python -m unittest discover -s tests` passed: 77 tests.

Notes:
- Baslangicta basit long-only varsayim yeterli.
- Maliyet, slippage, Sharpe, max drawdown ve win rate hesaplari P14'e birakildi.

### P14 - Costs, Slippage And Risk Metrics

Status: `Done`

Goal: Backtest sonuclarina gercekci maliyet ve risk olcumlerini eklemek.

Deliverables:
- Nonzero trading cost and slippage assumptions
- Cumulative return
- Sharpe ratio
- Maximum drawdown
- Win rate
- Benchmark difference

Acceptance:
- Maliyet varsayimlari `settings.yaml` icinden okunur.
- Maliyet oncesi ve sonrasi ayrimi raporlanabilir.
- Risk metrikleri icin testler vardir.

Completed:
- `src.backtest.run_backtest` trading cost ve slippage parametreleriyle genisletildi.
- Varsayilan maliyetler `settings.yaml` ile uyumlu olacak sekilde `trading_cost_bps=10` ve `slippage_bps=5` olarak korundu.
- `run_backtest_from_settings` helper'i eklendi; timing, horizon ve maliyet varsayimlari merkezi settings nesnesinden okunabiliyor.
- Trade ciktisina `trading_cost_bps`, `slippage_bps`, `total_cost_bps` ve `cost_adjusted_return` alanlari eklendi.
- Sifir toplam maliyet varsayimi reddediliyor; negatif cost/slippage icin acik hata mesaji donuyor.
- `calculate_risk_metrics` ile cumulative return, Sharpe ratio, maximum drawdown, win rate, cumulative benchmark return ve benchmark difference hesaplari eklendi.
- Backtest summary maliyet oncesi ve maliyet sonrasi ortalama/medyan getirileri, risk metriklerini ve benchmark farkini raporlayacak sekilde genisletildi.
- `reports/backtest.md` P14 kapsamiyla guncellendi.
- Cost/slippage ve risk metric unit testleri eklendi.

Tests:
- `python -m unittest discover -s tests` passed: 81 tests.

Notes:
- Maliyetler sifir varsayilmamali.
- Sharpe ratio trade-level cost-adjusted return serisi uzerinden hesaplanir; daily portfolio return Sharpe'i degildir.

### P15 - Unseen Period And Regime Splits

Status: `Done`

Goal: Kural secimi ve nihai test icin unseen period ve piyasa rejimi ayrimini eklemek.

Deliverables:
- Train/selection vs unseen test split
- Rising/falling market regime labels
- Stability comparison outputs

Acceptance:
- Unseen donem kural seciminde kullanilmaz.
- Rising/falling market ayrimi en az temel benchmarka gore yapilir.
- Raporlarda donem ayrimi acikca gorunur.

Completed:
- `src/splits.py` selection/unseen split ve market-regime yardimci modulu olarak eklendi.
- `label_period_split` ile `selection`, `unseen` ve unseen tarihi yoksa `full_sample` etiketleri deterministik uretiliyor.
- `build_market_regime_frame` ve `label_market_regime` ile benchmark veya lokal price history uzerinden `rising`, `falling`, `unknown` regime etiketleri uretiliyor.
- `apply_split_and_regime_labels` split ve regime etiketlerini tek akista uyguluyor.
- `summarize_unseen_stability` predefined grup kolonlari icin selection vs unseen average return, count, delta ve stability label uretiyor.
- Stability label degerleri `stable_positive`, `stable_negative`, `sign_flip`, `inconclusive` ve `unavailable` olarak sinirlandi.
- `write_split_regime_report` markdown rapor yazicisi ve `reports/split_regime.md` baslangic raporu eklendi.
- `config/settings.yaml` icine `experiment.unseen_start_date` ve `experiment.regime_lookback_days` alanlari eklendi.
- `src.settings` experiment config'i okuyacak sekilde genisletildi.
- Split/regime unit testleri eklendi.

Tests:
- `python -m unittest discover -s tests` passed: 89 tests.

Notes:
- Bu faz verification asamasinin ana parcasi.
- `experiment.unseen_start_date` simdilik `null`; veri kapsami dogrulanmadan unseen tarihi uydurulmadi.

### P16 - Deterministic MCP Tool Set

Status: `Done`

Goal: README'deki arac kategorilerini kapsayan kucuk, deterministik MCP araclarini eklemek.

Deliverables:
- `src/mcp_server.py`
- Market/index history tool
- Indicators/events tool
- Sector ranking tool
- Weekday test tool
- Point-in-time fundamentals tool
- Macro/news/video context tool
- Backtest tool
- Data-quality check and evidence bundle tools

Acceptance:
- Tool ciktisi structured values, source ve time metadata icerir.
- Tool hesaplari Python tarafinda yapilir; LLM sayisal hesap yapmaz.
- Gecersiz veya eksik veri durumunda warning/block status uretilebilir.

Completed:
- `src/mcp_server.py` deterministic MCP-like tool registry ve callable tool surface olarak dolduruldu.
- `ToolSpec`, `ToolResponse`, `list_tools()` ve `call_tool(name, args)` public arayuzu eklendi.
- `market_history` araci cache veya verilen price frame'leri icin symbol/date/source metadata ozeti donuyor.
- `indicators_events` araci teknik indikatorleri ve event detector ciktisini deterministik hesapliyor.
- `sector_ranking` araci fixed-universe sector catch-up analizini tool payload'i olarak donuyor.
- `weekday_test` araci weekday/multi-day pattern analizini summary ile donuyor.
- `point_in_time_fundamentals` araci fundamentals point-in-time gate ve opsiyonel quarterly fundamentals research ciktisi uretiyor.
- `context` araci macro/news/video context normalize etme, decision-time filtreleme ve point-in-time gate islemini yapiyor.
- `backtest` araci P13/P14 backtest motorunu structured response olarak calistiriyor.
- `data_quality` araci market data kalite kontrollerini ve future-outcome feature leakage kontrolunu expose ediyor.
- `evidence_bundle` araci observed feature ve source alanlarindan source-linked evidence bundle uretiyor.
- Bilinmeyen tool, gecersiz input ve alt modul hatalari `ToolResponse.errors` / `warnings` icinde structured olarak donuyor.
- `reports/mcp_tools.md` tool katalog raporu eklendi.
- MCP tool surface unit testleri eklendi.

Tests:
- `python -m unittest discover -s tests` passed: 99 tests.

Notes:
- Tool sayisi kucuk tutulacak; ders prototipi icin yeterli kapsama hedeflenecek.
- Bu faz stdio/SSE MCP transport wrapper'i eklemedi; test edilebilir deterministik tool surface hazirlandi.

### P17 - Harness State Machine

Status: `Done`

Goal: Analiz akisini README'deki sira ile enforce eden stateful harness kurmak.

Deliverables:
- `src/harness.py`
- State order enforcement
- Permitted tools per state
- Educational output states

Acceptance:
- Akis su sirayi izler: select universe -> load/validate -> run analyses -> add context -> build evidence -> compare variants -> backtest -> risk gate -> explain -> human review -> save decision.
- Siradisi tool kullanimi engellenir veya hata verir.
- Cikti durumlari `WATCH`, `INVESTIGATE`, `POTENTIAL_CATCH_UP_CANDIDATE`, `REJECT_SIGNAL`, `ANALYSIS_UNSAFE` gibi sinirli etiketlerden gelir.

Completed:
- `src/harness.py` stateful analysis harness olarak dolduruldu.
- Zorunlu akis sirasi `select_universe -> load_validate -> run_analyses -> add_context -> build_evidence -> compare_variants -> backtest -> risk_gate -> explain -> human_review -> save_decision` olarak tanimlandi.
- `PERMITTED_TOOLS_BY_STATE` ile her state icin izinli tool listesi belirlendi.
- `AnalysisHarness.call_tool` P16 tool registry'sini cagirmadan once state/tool iznini kontrol ediyor.
- Siradisi tool kullanimi `HarnessStepResult(status="error")` ve event log kaydi ile bloklaniyor.
- `advance(expected_state=...)` ile out-of-order state tamamlama girisimleri bloklaniyor.
- Educational output label seti `WATCH`, `INVESTIGATE`, `POTENTIAL_CATCH_UP_CANDIDATE`, `REJECT_SIGNAL`, `ANALYSIS_UNSAFE` olarak sinirlandi.
- Output label sadece `explain` state'inde set edilebiliyor.
- Human review sadece `human_review` state'inde `accept`, `modify`, `reject` degerleriyle kaydedilebiliyor.
- Decision save islemi output label ve human review olmadan bloklaniyor.
- Harness snapshot ve replay-friendly event log eklendi.
- `reports/harness_state_machine.md` akisi belgelemek icin eklendi.
- Harness state machine unit testleri eklendi.

Tests:
- `python -m unittest discover -s tests` passed: 107 tests.

Notes:
- Ayrik reasoning servisleri gerekmiyor; tek orchestrator yeterli.
- P18 evidence bundle ve quality gate semantigini bu state machine uzerine ekleyecek.

### P18 - Evidence Bundle And Quality Gate

Status: `Done`

Goal: Aciklamalarda kullanilacak kanit setini ve kalite kapisini uygulamak.

Deliverables:
- Observed feature list
- Committed evidence set
- Source-linked numerical claims
- Warning/block gate status

Acceptance:
- Her sayisal ifade bir tool outputuna baglanabilir.
- Missing source veya small sample warning uretir.
- Future leakage, broken history veya critical date mismatch sonucu bloklar.

Completed:
- `src/evidence.py` evidence bundle ve quality gate modulu olarak eklendi.
- `build_evidence_bundle` observed feature listelerini source metadata ile source-linked evidence kayitlarina donusturuyor.
- `commit_evidence_set` ile committed evidence set icin stable SHA-256 hash uretiliyor.
- `evaluate_quality_gate` evidence completeness, future-outcome feature leakage ve dis validation report'larini tek gate sonucunda birlestiriyor.
- Missing evidence bundle blocking issue uretir; missing source ve small evidence set warning olarak kalir.
- Future-outcome feature leakage, future information leakage, broken history veya critical date mismatch gibi blocking validation issue'lari `ANALYSIS_UNSAFE` uretir.
- `quality_gate_to_dict` ve `write_evidence_report` yardimcilari eklendi.
- P16 `evidence_bundle` tool'u yeni evidence modulu uzerinden evidence hash ve quality gate payload'i donecek sekilde guncellendi.
- P17 harness'e `apply_quality_gate` eklendi; gate sonucu sadece `risk_gate` state'inde uygulanabilir.
- `ANALYSIS_UNSAFE` gate sonucu harness output label'ini otomatik `ANALYSIS_UNSAFE` yapar.
- `reports/evidence_quality_gate.md` baslangic raporu eklendi.
- Evidence/gate unit testleri ve MCP evidence tool testi eklendi.

Tests:
- `python -m unittest discover -s tests` passed: 115 tests.

Notes:
- Bu faz harness guvenilirligini belirleyen ana parca.
- Canli karar veya strategy sonucu uydurulmadi; moduller verified tool outputlari icin hazirlandi.

### P19 - Human Review And Replayable Decision Log

Status: `Done`

Goal: Insan onayi ve tekrar oynatilabilir karar kaydi eklemek.

Deliverables:
- Decision log schema
- Accept/modify/reject review states
- Replay inputs and tool outputs
- Example reviewed decision

Acceptance:
- Bir analiz karari yeterli girdiyle yeniden oynatilabilir.
- Human review sonucu karar kaydinda gorunur.
- Raporlama karar loguna link verebilir.

Completed:
- `src/decision_log.py` human-reviewed replayable decision log modulu olarak eklendi.
- `DecisionRecord` JSONL semasi `schema_version`, `decision_id`, `created_at`, output label, review status, reviewer, harness snapshot, inputs, tool outputs, evidence hash ve quality gate alanlarini kapsar.
- `create_decision_record` harness output label, human review, saved decision ve evidence hash olmadan kayit olusturmayacak sekilde guard eder.
- Review status degerleri `accept`, `modify`, `reject` ile sinirlandi.
- `append_decision_record` karar kaydini `decisions.jsonl` dosyasina append eder.
- `load_decision_records` JSONL kayitlarini typed `DecisionRecord` listesine yukler.
- `replay_decision_record` record hash, evidence hash, harness output label/review status ve zorunlu bolumleri dogrular.
- `write_decision_log_report` markdown rapor yazicisi eklendi.
- `reports/decision_log.md` karar logu durum raporu olarak eklendi.
- Decision log unit testleri eklendi.

Tests:
- `python -m unittest discover -s tests` passed: 120 tests.

Notes:
- Classroom demo icin en az bir tam replay ornegi yeterli.
- Bu fazda live reviewed investment/strategy decision kaydi uydurulmadi; testler sentetik kayit kullanir.

### P20 - Strategy Variant Comparison A-E

Status: `Done`

Goal: Finansal strateji kombinasyonlari A-E'yi ayni veri uzerinde karsilastirmak.

Deliverables:
- A: technical
- B: technical + sector
- C: B + fundamentals
- D: C + macro
- E: D + verified news/video context
- `reports/strategy_variants.*`

Acceptance:
- Eksik kaynakli varyant unavailable olarak isaretlenir.
- Ayni veri donemi ve maliyet varsayimlari kullanilir.
- Performans ve risk metrikleri yan yana raporlanir.

Completed:
- `src/strategy_variants.py` strategy variant comparison modulu olarak eklendi.
- A-E varyant tanimlari sabitlendi: A technical, B technical+sector, C B+fundamentals, D C+macro, E D+verified news/video context.
- `compare_strategy_variants` bileşen bazli signal DataFrame'lerini ayni price data, benchmark hook'lari ve cost/slippage varsayimlariyla backtest eder.
- Eksik bileşenli varyantlar `unavailable` status ve `missing_components` alanlariyla raporlanir; kaynak uydurma yapilmaz.
- Varyant summary data period, cost/slippage, signal/trade count, risk metrikleri ve benchmark farkini yan yana raporlar.
- Trade ciktisi `variant`, `component` ve `component_signal_id` metadata'sini korur.
- `compare_strategy_variants_from_settings` merkezi settings'teki horizon ve cost varsayimlarini kullanir.
- `write_strategy_variants_report` markdown rapor yazicisi ve `reports/strategy_variants.md` baslangic raporu eklendi.
- Strategy variant unit testleri eklendi.

Tests:
- `python -m unittest discover -s tests` passed: 125 tests.

Notes:
- Kaynak yoksa deger uydurulmaz.
- Bu fazda live/verified strateji sinyal kaydi uydurulmadi; motor verified signal records icin hazirlandi.

### P21 - Harness Variant Comparison A-E

Status: `Done`

Goal: Agent harness varyantlarini ayni sabit sorularla karsilastirmak.

Deliverables:
- A: raw LLM
- B: LLM + tools
- C: tools + enforced states
- D: C + evidence/quality gate
- E: D + memory/human review
- `reports/harness_variants.*`

Acceptance:
- Unsupported numbers, invalid tool calls, evidence completeness ve replayability karsilastirilir.
- Sabit soru seti ayni kalir.
- Finansal strateji A-E ile harness A-E birbirine karistirilmaz.

Completed:
- `src/harness_variants.py` harness variant comparison modulu olarak eklendi.
- Harness A-E varyant tanimlari sabitlendi: A raw LLM, B LLM+tools, C tools+enforced states, D C+evidence/quality gate, E D+memory/human review.
- Fixed question-set semasi `requires_numbers`, `requires_tools`, `requires_state_enforcement`, `requires_evidence`, `requires_quality_gate`, `requires_replay`, `requires_human_review` alanlariyla tanimlandi.
- `compare_harness_variants` ayni sabit sorular uzerinden unsupported number, invalid tool call, evidence completeness, quality gate, replayability ve human review coverage metriklerini hesaplar.
- Varyant summary `score` ve `status` alanlariyla yan yana raporlanir.
- `write_harness_variants_report` markdown rapor yazicisi ve `reports/harness_variants.md` baslangic raporu eklendi.
- Harness variant unit testleri eklendi.

Tests:
- `python -m unittest discover -s tests` passed: 129 tests.

Notes:
- Bu faz teslimat icin ayri bir karsilastirma basligidir.
- P20 strategy A-E ile P21 harness A-E ayri tutuldu; bu fazda live LLM run uydurulmadi.

### P22 - Reports And Final Technical Narrative

Status: `Done`

Goal: Dört senaryo raporu, context raporu, backtest raporlari ve final teknik raporu tamamlamak.

Deliverables:
- Sector catch-up report
- Weekday/multi-day patterns report
- Technical reversals report
- Quarterly fundamentals report
- Macro/context report
- Backtest and risk report
- Final technical report

Acceptance:
- Her rapor data period, source, sample size, assumptions ve limitations icerir.
- Inconclusive bulgular net sekilde inconclusive olarak yazilir.
- Sonuclar investment advice dili kullanmaz.

Completed:
- `src/reporting.py` rapor manifest'i ve final teknik anlatim yardimcilari olarak eklendi.
- `REPORT_MANIFEST` ile senaryo raporlari, context, backtest/risk, split/regime, strategy variants, harness variants ve decision log raporlari tek envanterde toplandi.
- Her manifest girdisi status, data period, source, sample size, assumptions ve limitations metadata'si icerir.
- `validate_report_manifest` rapor dosyalarinin mevcut oldugunu ve metadata alanlarinin bos olmadigini kontrol eder.
- `write_report_index` rapor envanterini markdown tablo olarak uretir.
- `write_final_technical_report` current implementation state icin final teknik anlatimi uretir.
- `reports/report_index.md` eklendi.
- `reports/final_technical_report.md` eklendi.
- Final rapor empirical findings icin `inconclusive` dilini kullanir ve investment advice dili kullanmaz.
- Reporting unit testleri eklendi.

Tests:
- `python -m unittest discover -s tests` passed: 132 tests.

Notes:
- README'deki PDF kaynakli sinirlar korunacak.
- Canli/cache veri ve verified source records olmadigi icin final rapor measured result iddia etmez.

### P23 - Demo Command And Documentation Polish

Status: `Done`

Goal: Projeyi kurulabilir, calistirilabilir ve sinif demosuna hazir hale getirmek.

Deliverables:
- README install/update notlari
- One working demo command
- Cached demo dataset instructions
- Final smoke tests

Acceptance:
- Temiz ortamda kurulum adimlari takip edilebilir.
- Demo live source availability olmadan cache ile calisabilir.
- Teslim checklist'indeki ana maddeler tamamlanmistir.

Completed:
- `src/demo.py` ile offline classroom demo orkestrasyonu eklendi.
- `scripts/demo.py` CLI komutu eklendi: `python -m scripts.demo --offline`.
- `reports/demo_summary.md` uretildi.
- README kurulum, test, demo ve cache doldurma notlariyla guncellendi.
- Demo smoke testleri eklendi.

Tests:
- `python -m unittest tests.test_demo` passed: 3 tests.
- `python -m scripts.demo --offline --output reports/demo_summary.md` passed.
- `python -m unittest discover -s tests` passed: 135 tests.

Notes:
- Web dashboard zorunlu degil; notebook veya CLI demo yeterli olabilir.
- Cache yoklugu warning olarak raporlanir; measured financial finding uretilmez.

## RSS Haber Akisi Ve Zamanlama Politikasi

Karar: RSS kaynaklari anlik stream gibi dinlenmeyecek. RSS feed'ler dogasi geregi polling ile calisir; bu yuzden sistem haberleri zamanlanmis araliklarla ceker, normalize eder, deduplicate eder ve replay edilebilir cache'e yazar.

Varsayilan cekim sikligi:
- Piyasa saatlerinde: 15 dakikada bir RSS polling.
- Piyasa disinda: 60 dakikada bir RSS polling.
- Sinif demosunda: once `python -m scripts.fetch_rss_news`, sonra `python -m scripts.demo --offline`.
- Backtest/replay modunda: yalnizca cache'teki `published_timestamp <= decision_timestamp` haberleri kullanilir.

Neden anlik dinleme degil:
- RSS kaynaklari push/websocket garantisi vermez.
- Tekrarlanabilir akademik deney icin snapshot/cache gerekir.
- Rate-limit, kaynak hatasi veya RSS format degisikligi tum sistemi durdurmamalidir.
- Haberler karar girdisi olabilir, fakat tek basina otomatik trade aksiyonu uretmez.

Ilk RSS kaynaklari:
- `https://www.cnnturk.com/feed/rss/ekonomi/news`
- `https://www.ntv.com.tr/ekonomi.rss`
- `https://www.milliyet.com.tr/rss/rssnew/sondakikarss.xml`
- `https://www.yeniakit.com.tr/rss/haber/ekonomi`
- `https://www.yenisafak.com/rss?category=ekonomi`
- `https://www.ft.com/global-economy?format=rss`
- `https://www.investing.com/rss/news.rss`
- `https://finance.yahoo.com/news/rssindex`

### P24 - RSS Source Config And Fetcher

Status: `Done`

Goal: RSS kaynaklarini konfigurasyona alip, haberleri timestamp'li raw cache olarak cekmek.

Deliverables:
- `config/rss_sources.yaml`
- `src/rss_news.py`
- `scripts/fetch_rss_news.py`
- `data/rss/news_raw.jsonl` cikti formati
- RSS fetch unit testleri

Acceptance:
- Her RSS kaydinda `source_id`, `title`, `url`, `published_timestamp`, `fetched_timestamp`, `language`, `source_access` ve `content_hash` bulunur.
- Bir kaynak hata verdiginde diger kaynaklar cekilmeye devam eder.
- Fetch komutu exit code ve raporda kaynak bazli basari/uyari bilgisini verir.

Completed:
- `config/rss_sources.yaml` ile 8 RSS kaynagi ve polling ayarlari eklendi.
- `src/rss_news.py` ile RSS source loader, urllib client, RSS/Atom parser, timestamp normalization, JSONL writer ve fetch status report writer eklendi.
- `scripts/fetch_rss_news.py` CLI komutu eklendi.
- `.gitignore` icine `data/rss/` eklendi; canli haber cache'i commitlenmeyecek.
- `reports/rss_fetch_status.md` source-level fetch raporu uretildi.
- RSS fetch unit testleri eklendi.

Tests:
- `python -m unittest tests.test_rss_news` passed: 4 tests.
- `python -m unittest discover -s tests` passed: 139 tests.
- `python -m scripts.fetch_rss_news` passed with 8 sources and 259 cached raw items.

Notes:
- Canli RSS ciktilari commitlenmez; replay icin gerekirse kucuk fixture kullanilir.
- `published_timestamp` yoksa kayit `warning` alir ve decision-time filtrelerinde guvenli sekilde ele alinir.
- P24 raw cache fazidir; dedup ve source health olgunlastirma P25'e ayrildi.

### P25 - RSS Normalization Dedup And Source Health

Status: `Done`

Goal: Raw RSS kayitlarini tekillestirip kaynak sagligi raporunu uretmek.

Deliverables:
- Normalize edilmis `data/rss/news.jsonl`
- URL/title/content hash tabanli dedup
- `reports/rss_source_health.md`
- Kaynak stale/error/empty durumlari

Acceptance:
- Ayni URL veya ayni normalize title tekrar yazilmaz.
- Her source icin item count, latest published time ve error/warning durumu raporlanir.
- Bos feed tum pipeline'i durdurmaz, warning olarak islenir.

Completed:
- `deduplicate_news_items` ile URL, normalize title ve content hash tabanli deterministik dedup eklendi.
- `normalize_news_item` ile title/summary HTML temizleme ve normalized content hash uretimi eklendi.
- `normalize_rss_news_cache` raw RSS cache'i okuyup `data/rss/news.jsonl` ve source health raporu uretir.
- `build_source_health` ile raw count, normalized count, duplicate count, latest published ve stale/error/empty durumlari hesaplanir.
- `scripts/normalize_rss_news.py` CLI komutu eklendi.
- `reports/rss_source_health.md` uretildi.
- RSS normalization ve source health unit testleri eklendi.

Tests:
- `python -m unittest tests.test_rss_news` passed: 8 tests.
- `python -m scripts.normalize_rss_news` passed: 259 normalized items, 8 source health rows.
- `python -m unittest discover -s tests` passed: 143 tests.

Notes:
- Dedup deterministik olacak; LLM kullanilmayacak.
- Canli normalize cache `data/rss/news.jsonl` ignore altindadir ve commitlenmez.
- Current live health report NTV ve Yahoo Finance icin 24 saat stale warning uretmistir; bu kaynak sagligi notudur, pipeline hatasi degildir.

### P26 - News Alias Matching

Status: `Done`

Goal: Haberleri hisse, sektor ve makro konu basliklariyla eslestirmek.

Deliverables:
- `config/news_aliases.csv`
- Ticker/sektor/makro alias matcher
- `linked_entities` ve `matched_terms` alanlari
- Alias matching testleri

Acceptance:
- Haber basligi ve ozetinden deterministic alias match uretilir.
- Eslesme yoksa haber genel ekonomi context'i olarak saklanabilir.
- Alias eslesmesi trade sinyali sayilmaz; sadece context evidence olur.

Completed:
- `config/news_aliases.csv` ile ticker, sektor ve makro alias sozlugu eklendi.
- `src/news_aliases.py` ile deterministic alias loader, Turkish/English text normalization, matcher, JSONL writer ve coverage summary eklendi.
- Alias matcher `linked_entities` ve `matched_terms` alanlarini uretir.
- `scripts/match_news_aliases.py` CLI komutu eklendi.
- `reports/news_alias_matches.md` coverage raporu uretildi.
- Alias matching unit testleri eklendi.

Tests:
- `python -m unittest tests.test_news_aliases` passed: 5 tests.
- `python -m scripts.match_news_aliases` passed: 259 total items, 97 matched items.
- `python -m unittest discover -s tests` passed: 148 tests.

Notes:
- Ilk fazda sentiment modeli yok; yanlis pozitifleri azaltmak icin basit, acik alias sozlugu kullanilacak.
- Alias eslesmesi trade sinyali degildir; yalnizca RSS context evidence baglantisi uretir.
- Current live alias report 259 normalized haberden 97 eslesmeli haber bulmustur.

### P27 - News Context Builder And Report Integration

Status: `Done`

Goal: RSS haberlerini karar zamanina gore filtreleyip ticker/sektor/makro context ozeti uretmek.

Deliverables:
- `scripts/build_news_context.py`
- `data/rss/news_context.csv`
- `reports/context_sources.md` RSS bolumu guncellemesi
- Decision-time filtre testleri

Acceptance:
- Context builder yalnizca `published_timestamp <= decision_timestamp` haberleri kullanir.
- Lookback penceresi ayarlanabilir olur; varsayilan 7 gun.
- Her ticker icin news_count, source_count, latest_news_timestamp ve evidence_urls raporlanir.

Completed:
- `src/news_context.py` ile decision-time guvenli RSS context builder eklendi.
- `scripts/build_news_context.py` CLI komutu eklendi.
- `data/rss/news_context.csv` cikti formati tanimlandi ve canli cache uzerinden uretildi.
- `reports/context_sources.md` RSS context bolumuyle guncellendi.
- `src.reporting.REPORT_MANIFEST`, `reports/report_index.md` ve `reports/final_technical_report.md` RSS context durumuyla uyumlu hale getirildi.
- Decision-time filtre ve lookback unit testleri eklendi.

Tests:
- `python -m unittest tests.test_news_context` passed: 3 tests.
- `python -m scripts.build_news_context` passed: 51 context rows, 24 active context rows.
- `python -m unittest discover -s tests` passed: 151 tests.

Notes:
- Bu faz P12 context semasina baglanir; video zorunlu degildir.
- Context builder yalnizca `published_timestamp <= decision_timestamp` haberlerini kullanir.
- Her fixed-universe ticker icin context satiri uretilir; haber yoksa `news_count=0` kalir.

### P28 - Demo Update With RSS Context Status

Status: `Done`

Goal: Offline demo komutuna RSS cache ve context durumunu eklemek.

Deliverables:
- `python -m scripts.demo --offline` RSS cache kontrolu
- `reports/demo_summary.md` RSS source/context satirlari
- Demo smoke testleri

Acceptance:
- Demo internet olmadan RSS cache durumunu raporlar.
- RSS cache yoksa warning verir; proje demo akisi durmaz.
- RSS context varsa kac haber/kaynak/ticker eslestigi ozetlenir.

Completed:
- `src.demo.run_offline_demo` RSS raw, normalized, matched, context CSV ve source health artifact kontrolleriyle genisletildi.
- `reports/demo_summary.md` RSS News Context bolumuyle guncellendi.
- Demo hicbir live RSS istegi yapmadan local artifact durumunu raporlar.
- Missing RSS artifact durumlari warning olarak ele alinir; demo akisi durmaz.
- Demo smoke testleri RSS artifact kontrollerini kapsayacak sekilde genisletildi.

Tests:
- `python -m unittest tests.test_demo` passed: 5 tests.
- `python -m scripts.demo --offline` passed with RSS raw/normalized/matched/context/source-health checks.
- `python -m unittest discover -s tests` passed: 153 tests.

Notes:
- Demo anlik haber cekmez; once fetch komutu calistirilir, demo cache'i okur.
- Current demo 259 raw, 259 normalized, 259 matched RSS row ve 51 context row raporlamistir.

### P29 - Strategy Variant E RSS Context Integration

Status: `Not Started`

Goal: RSS haber context'ini Strategy Variant E icin verified context girdisi yapmak.

Deliverables:
- Strategy Variant E news/context availability kontrolu
- Evidence bundle'a RSS evidence linkleri
- Quality gate'e RSS timestamp/source warnings
- Variant raporu guncellemesi

Acceptance:
- Variant E sadece timestamp'i guvenli ve source metadata'si olan haberleri kullanir.
- Eksik RSS context `unavailable` veya `warning` olarak raporlanir, uydurma sinyal uretilmez.
- Haber yogunlugu tek basina performans iddiasi olarak yazilmaz.

Completed:
- Yok.

Notes:
- Haber context'i finansal tavsiye degildir; strategy comparison icin destekleyici evidence olarak kullanilir.

## Gelistirme Gunlugu

| Tarih | Faz | Degisiklik | Test/Dogrulama | Not |
| --- | --- | --- | --- | --- |
| 2026-09-23 | Planning | README okundu ve implementation plan olusturuldu. | Dosya olusturma kontrolu yapilacak. | Ilk plan. |
| 2026-09-23 | P00 | Repository baseline dosya ve dizin iskeleti eklendi. | Python import smoke testi passed; pytest dependency eksik oldugu icin kosulmadi. | Aktif faz P01'e tasindi. |
| 2026-09-23 | P01 | Fixed universe CSV, data dictionary ve universe validation eklendi. | `python -m unittest discover -s tests` passed. | Aktif faz P02'ye tasindi. |
| 2026-09-23 | P02 | Merkezi settings YAML'i, typed config loader ve settings testleri eklendi. | `python -m unittest discover -s tests` passed: 8 tests. | Aktif faz P03'e tasindi. |
| 2026-09-23 | P03 | Market data adapter, normalized OHLCV cache helpers, missing-symbol report ve fetch script eklendi. | `python -m unittest discover -s tests` passed: 12 tests. | Aktif faz P04'e tasindi; live cache commitlenmedi. |
| 2026-09-23 | P04 | Data-quality validator, point-in-time checks ve leakage blok kontrolleri eklendi. | `python -m unittest discover -s tests` passed: 20 tests. | Aktif faz P05'e tasindi. |
| 2026-09-23 | P05 | Cekirdek teknik indikator fonksiyonlari ve sentetik veri testleri eklendi. | `python -m unittest discover -s tests` passed: 26 tests. | Aktif faz P06'ya tasindi. |
| 2026-09-23 | P06 | Teknik event detectorleri, ortak event semasi ve detector-level error handling eklendi. | `python -m unittest discover -s tests` passed: 31 tests. | Aktif faz P07'ye tasindi. |
| 2026-09-24 | P07 | Sector catch-up hesaplayici, self-excluding peer median, status alanlari, rapor yazici ve testler eklendi. | `python -m unittest discover -s tests` passed: 36 tests. | Aktif faz P08'e tasindi. |
| 2026-09-24 | P08 | Weekday/multi-day pattern hesaplayici, cost-adjusted return, regime/split alanlari, ozet ve rapor yazici eklendi. | `python -m unittest discover -s tests` passed: 42 tests. | Aktif faz P09'a tasindi. |
| 2026-09-24 | P09 | Teknik reversal analizi, individual/combined signal grouping, bounce/failure summary ve rapor yazici eklendi. | `python -m unittest discover -s tests` passed: 48 tests. | Aktif faz P10'a tasindi. |
| 2026-09-24 | P10 | Point-in-time fundamentals semasi, bank/industrial metric profile ayrimi, import helperlari ve testler eklendi. | `python -m unittest discover -s tests` passed: 55 tests. | Aktif faz P11'e tasindi. |
| 2026-09-24 | P11 | Quarterly fundamentals research, QoQ/YoY metrics, post-disclosure returns ve benchmark/sector-relative karsilastirmalar eklendi. | `python -m unittest discover -s tests` passed: 63 tests. | Aktif faz P12'ye tasindi. |
| 2026-09-24 | P12 | Macro/news/video context semasi, source access kontrolleri, point-in-time donusumu, decision-time filtresi ve context dokumanlari eklendi. | `python -m unittest discover -s tests` passed: 70 tests. | Aktif faz P13'e tasindi; canli context verisi uydurulmadi. |
| 2026-09-24 | P13 | Point-in-time guvenli backtest motoru, signal semasi, entry/exit timing, benchmark hook'lari, summary ve rapor yazici eklendi. | `python -m unittest discover -s tests` passed: 77 tests. | Aktif faz P14'e tasindi; maliyet/risk metrikleri sonraki fazda. |
| 2026-09-24 | P14 | Backtest maliyet/slippage kesintileri, settings baglantisi, cost-adjusted return, cumulative return, Sharpe, max drawdown, win rate ve benchmark difference eklendi. | `python -m unittest discover -s tests` passed: 81 tests. | Aktif faz P15'e tasindi; gercek backtest verisi henuz uydurulmadi. |
| 2026-09-24 | P15 | Selection/unseen split, benchmark regime labels, stability comparison helperlari, experiment settings ve split/regime rapor iskeleti eklendi. | `python -m unittest discover -s tests` passed: 89 tests. | Aktif faz P16'ya tasindi; unseen tarihi veri kapsami dogrulaninca sabitlenecek. |
| 2026-09-24 | P16 | Deterministic tool registry, market/indicator/event/sector/weekday/fundamentals/context/backtest/data-quality/evidence tools ve tool katalog raporu eklendi. | `python -m unittest discover -s tests` passed: 99 tests. | Aktif faz P17'ye tasindi; transport wrapper gerekirse sonra eklenecek. |
| 2026-09-24 | P17 | Harness state machine, state order enforcement, permitted tool rules, educational labels, human review guard ve event log eklendi. | `python -m unittest discover -s tests` passed: 107 tests. | Aktif faz P18'e tasindi; quality gate semantigi sonraki fazda. |
| 2026-09-24 | P18 | Evidence bundle, committed evidence hash, quality gate, MCP evidence tool entegrasyonu ve harness risk-gate baglantisi eklendi. | `python -m unittest discover -s tests` passed: 115 tests. | Aktif faz P19'a tasindi; karar logu sonraki fazda. |
| 2026-09-24 | P19 | Replayable decision log semasi, JSONL append/load, human review guard, record hash ve replay integrity check eklendi. | `python -m unittest discover -s tests` passed: 120 tests. | Aktif faz P20'ye tasindi; live decision kaydi uydurulmadi. |
| 2026-09-24 | P20 | Strategy variant comparison A-E motoru, missing-component unavailable status, shared cost/data period ve markdown rapor iskeleti eklendi. | `python -m unittest discover -s tests` passed: 125 tests. | Aktif faz P21'e tasindi; live strategy sonucu uydurulmadi. |
| 2026-09-24 | P21 | Harness variant comparison A-E motoru, fixed question-set semasi, capability metrikleri ve markdown rapor iskeleti eklendi. | `python -m unittest discover -s tests` passed: 129 tests. | Aktif faz P22'ye tasindi; live LLM run uydurulmadi. |
| 2026-09-24 | P22 | Rapor manifest'i, report index, final technical report ve reporting testleri eklendi. | `python -m unittest discover -s tests` passed: 132 tests. | Aktif faz P23'e tasindi; measured result iddiasi eklenmedi. |
| 2026-09-24 | P23 | Offline demo komutu, demo summary raporu, README kurulum/cache notlari ve demo smoke testleri eklendi. | `python -m unittest discover -s tests` passed: 135 tests. | Planlanan fazlar tamamlandi; cache yoklugu warning olarak raporlanir. |
| 2026-09-24 | RSS Planning | RSS haber kaynaklari icin polling, cache, dedup, alias matching, context builder ve Strategy Variant E entegrasyon fazlari plana eklendi. | Dokuman guncellemesi. | Aktif faz P24'e tasindi; RSS anlik dinlenmeyecek, periyodik polling yapilacak. |
| 2026-09-24 | P24 | RSS source config, raw RSS fetcher, JSONL cache writer, source-level fetch report ve testler eklendi. | `python -m unittest discover -s tests` passed: 139 tests; live `python -m scripts.fetch_rss_news` 8 kaynak ve 259 raw item ile passed. | Aktif faz P25'e tasindi; canli `data/rss/` cache commitlenmez. |
| 2026-09-24 | P25 | RSS normalize/dedup akisi, source health hesaplari, normalize CLI ve health raporu eklendi. | `python -m unittest discover -s tests` passed: 143 tests; `python -m scripts.normalize_rss_news` 259 normalized item ile passed. | Aktif faz P26'ya tasindi; NTV ve Yahoo Finance stale warning verdi. |
| 2026-09-24 | P26 | News alias sozlugu, deterministic alias matcher, matched news JSONL writer, coverage raporu ve testler eklendi. | `python -m unittest discover -s tests` passed: 148 tests; `python -m scripts.match_news_aliases` 259 total ve 97 matched item ile passed. | Aktif faz P27'ye tasindi; alias eslesmesi trade sinyali degildir. |
| 2026-09-24 | P27 | Decision-time guvenli RSS context builder, context CSV, context report entegrasyonu, reporting manifest guncellemesi ve testler eklendi. | `python -m unittest discover -s tests` passed: 151 tests; `python -m scripts.build_news_context` 51 context row ve 24 active row ile passed. | Aktif faz P28'e tasindi; context evidence trade sinyali degildir. |
| 2026-09-24 | P28 | Offline demo RSS raw/normalized/matched/context/source-health artifact kontrolleriyle genisletildi ve demo summary guncellendi. | `python -m unittest discover -s tests` passed: 153 tests; `python -m scripts.demo --offline` RSS checks ile passed. | Aktif faz P29'a tasindi; demo live RSS cekmez. |

## Acik Riskler Ve Kararlar

| Konu | Durum | Karar/Not |
| --- | --- | --- |
| Finansal veri erisimi | Open | Fintables erisim ve lisans kosullari uygulanirken dogrulanacak. |
| Haber/video kaynaklari | Open | P12 sema ve import akisi hazir; yalnizca yasal erisilebilir, instructor-approved ve timestamp dogrulanabilir kaynaklar doldurulacak. |
| RSS cekim sikligi | Decided | RSS kaynaklari anlik dinlenmez; piyasa saatinde 15 dakikada bir, piyasa disinda 60 dakikada bir polling yapilir. Backtest/replay yalnizca cache snapshot kullanir. |
| BIST/XU100 sembol uyumu | Open | P03 adapter ve missing-symbol rapor yazicisi eklendi; canli `python -m scripts.fetch_market_data` calistirildiginda rapor uretilecek. |
| Unseen period tarihleri | Open | P15 altyapisi ve settings alani hazir; `experiment.unseen_start_date` veri kapsami dogrulandiktan sonra sabitlenecek. |
| Maliyet/slippage varsayimlari | Decided | `settings.yaml` icindeki `trading_cost_bps: 10` ve `slippage_bps: 5` backtest motoruna baglandi; sifir toplam maliyet reddedilir. |

## Teslimat Checklist

- [x] Fixed 30-stock universe and data dictionary
- [ ] Market price and XU100 cache
- [ ] Point-in-time fundamentals data
- [ ] Macro/news/video context records
- [x] RSS news cache and ticker/sector/macro context
- [ ] Four required scenario reports
- [ ] Backtests with costs, benchmarks and risk metrics
- [ ] Unseen test period and regime comparison
- [x] Deterministic MCP tools
- [x] Stateful harness with evidence and quality gate
- [x] Human-reviewed replayable decision log
- [ ] Strategy variants A-E comparison
- [ ] Harness variants A-E comparison
- [x] Final report and classroom demo command

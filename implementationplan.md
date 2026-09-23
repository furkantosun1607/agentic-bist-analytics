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
| Proje durumu | Technical event detectors ready |
| Son guncelleme | 2026-09-23 |
| Aktif faz | P07 - Sector Catch-Up Research |
| Kritik sonraki hedef | Sektor catch-up analizini ve insufficient-peer davranisini uygulamak |

## Degismez Proje Kurallari

- Sabit evren README'deki 30 hisse ile baslar ve `config/universe.csv` icinde tutulur.
- Deneyler arasinda hisse listesi sessizce degistirilmez; farkliliklar raporlanir.
- Her tarihsel karar icin yalnizca karar ani `t` itibariyla kamuya acik olan bilgi kullanilir.
- Finansal verilerde ceyrek sonu tarihi tek basina sinyal tarihi sayilmaz; aciklanma zamani ayrica izlenir.
- Eksik veya dogrulanamayan kaynaklar uydurulmaz; raporda eksik olarak isaretlenir.
- LLM fiyat, oran veya getiri hesaplamaz; hesaplamalar deterministik Python araclariyla yapilir.
- Her rapor veri donemi, kaynak, orneklem sayisi, varsayimlar ve limitasyonlar icerir.

## Hedef Dosya Yapisi

```text
README.md
implementationplan.md
requirements.txt
config/universe.csv
config/settings.yaml
src/data.py
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

Status: `Not Started`

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
- Yok.

Notes:
- Fixed 30 disindaki PDF ornekleri kullanilmayacak.

### P08 - Weekday And Multi-Day Pattern Research

Status: `Not Started`

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
- Yok.

Notes:
- Hipotetik yuzdeler sonuc gibi yazilmayacak.

### P09 - Technical Reversal Research

Status: `Not Started`

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
- Yok.

Notes:
- P05 ve P06 tamamlanmadan baslanmaz.

### P10 - Fundamentals Data Schema

Status: `Not Started`

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
- Yok.

Notes:
- Fintables README'de finansal kaynak olarak belirtilmis; erisim kosullari kontrol edilecek.

### P11 - Quarterly Fundamentals Research

Status: `Not Started`

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
- Yok.

Notes:
- P10 tamamlanmadan baslanmaz.

### P12 - Macro, News And Video Context

Status: `Not Started`

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
- Yok.

Notes:
- TCMB/EVDS, TUIK ve Federal Reserve kaynaklari README'de belirtilmis.

### P13 - Backtest Engine

Status: `Not Started`

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
- Yok.

Notes:
- Baslangicta basit long-only varsayim yeterli.

### P14 - Costs, Slippage And Risk Metrics

Status: `Not Started`

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
- Yok.

Notes:
- Maliyetler sifir varsayilmamali.

### P15 - Unseen Period And Regime Splits

Status: `Not Started`

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
- Yok.

Notes:
- Bu faz verification asamasinin ana parcasi.

### P16 - Deterministic MCP Tool Set

Status: `Not Started`

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
- Yok.

Notes:
- Tool sayisi kucuk tutulacak; ders prototipi icin yeterli kapsama hedeflenecek.

### P17 - Harness State Machine

Status: `Not Started`

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
- Yok.

Notes:
- Ayrik reasoning servisleri gerekmiyor; tek orchestrator yeterli.

### P18 - Evidence Bundle And Quality Gate

Status: `Not Started`

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
- Yok.

Notes:
- Bu faz harness guvenilirligini belirleyen ana parca.

### P19 - Human Review And Replayable Decision Log

Status: `Not Started`

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
- Yok.

Notes:
- Classroom demo icin en az bir tam replay ornegi yeterli.

### P20 - Strategy Variant Comparison A-E

Status: `Not Started`

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
- Yok.

Notes:
- Kaynak yoksa deger uydurulmaz.

### P21 - Harness Variant Comparison A-E

Status: `Not Started`

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
- Yok.

Notes:
- Bu faz teslimat icin ayri bir karsilastirma basligidir.

### P22 - Reports And Final Technical Narrative

Status: `Not Started`

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
- Yok.

Notes:
- README'deki PDF kaynakli sinirlar korunacak.

### P23 - Demo Command And Documentation Polish

Status: `Not Started`

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
- Yok.

Notes:
- Web dashboard zorunlu degil; notebook veya CLI demo yeterli olabilir.

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

## Acik Riskler Ve Kararlar

| Konu | Durum | Karar/Not |
| --- | --- | --- |
| Finansal veri erisimi | Open | Fintables erisim ve lisans kosullari uygulanirken dogrulanacak. |
| Haber/video kaynaklari | Open | Yalnizca yasal erisilebilir ve timestamp dogrulanabilir kaynaklar kullanilacak. |
| BIST/XU100 sembol uyumu | Open | P03 adapter ve missing-symbol rapor yazicisi eklendi; canli `python -m scripts.fetch_market_data` calistirildiginda rapor uretilecek. |
| Unseen period tarihleri | Open | Veri kapsamindan sonra settings icinde sabitlenecek. |
| Maliyet/slippage varsayimlari | Decided | Ilk varsayim `trading_cost_bps: 10` ve `slippage_bps: 5`; P14 sirasinda risk raporu icin tekrar gozden gecirilecek. |

## Teslimat Checklist

- [x] Fixed 30-stock universe and data dictionary
- [ ] Market price and XU100 cache
- [ ] Point-in-time fundamentals data
- [ ] Macro/news/video context records
- [ ] Four required scenario reports
- [ ] Backtests with costs, benchmarks and risk metrics
- [ ] Unseen test period and regime comparison
- [ ] Deterministic MCP tools
- [ ] Stateful harness with evidence and quality gate
- [ ] Human-reviewed replayable decision log
- [ ] Strategy variants A-E comparison
- [ ] Harness variants A-E comparison
- [ ] Final report and classroom demo command

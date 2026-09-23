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
| Proje durumu | Universe frozen |
| Son guncelleme | 2026-09-23 |
| Aktif faz | P02 - Settings And Runtime Configuration |
| Kritik sonraki hedef | Merkezi ayar dosyasini ve ayar okuma yardimcisini eklemek |

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

Status: `Not Started`

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
- Yok.

Notes:
- API key veya gizli bilgi dosyaya yazilmayacak.

### P03 - Market Data Adapter And Cache

Status: `Not Started`

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
- Yok.

Notes:
- Yahoo/yfinance README'de fiyat kaynagi olarak belirtilmis.

### P04 - Data Validation And Point-In-Time Checks

Status: `Not Started`

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
- Yok.

Notes:
- Bu faz sonraki tum analizlerin guvenlik temelidir.

### P05 - Core Technical Indicators

Status: `Not Started`

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
- Yok.

Notes:
- Kural optimizasyonu yapilmayacak; az sayida acik ve tekrar edilebilir indikator kullanilacak.

### P06 - Technical Event Detectors

Status: `Not Started`

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
- Yok.

Notes:
- Her aile icin bir kucuk detector yeterli; asiri parametre taramasi yapilmayacak.

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

## Acik Riskler Ve Kararlar

| Konu | Durum | Karar/Not |
| --- | --- | --- |
| Finansal veri erisimi | Open | Fintables erisim ve lisans kosullari uygulanirken dogrulanacak. |
| Haber/video kaynaklari | Open | Yalnizca yasal erisilebilir ve timestamp dogrulanabilir kaynaklar kullanilacak. |
| BIST/XU100 sembol uyumu | Open | P03 sirasinda missing symbol ve uyumsuzluk raporu uretilecek. |
| Unseen period tarihleri | Open | Veri kapsamindan sonra settings icinde sabitlenecek. |
| Maliyet/slippage varsayimlari | Open | P02/P14 sirasinda makul nonzero varsayim olarak belirlenecek. |

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

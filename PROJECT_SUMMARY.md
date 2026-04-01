# OpenClaudeClaw — Proje Özeti

## Ne Bu?

OpenClaw için gelişmiş harness sistemi. Claude Code'dan esinlenilmiştir ama tamamen Python/OpenClaw için özgün olarak yazılmıştır.

## Özellikler

- **42 Tool** — Core, Extended, Advanced kategorilerinde
- **Harness Context** — SOUL + MEMORY + USER otomatik birleştirme
- **State Management** — Persistent state (.harness/ dizini)
- **Policy Engine** — Tool bazlı izinler
- **Cache** — 60s TTL
- **Event Bus** — Async event handling
- **Agent Registry** — Sub-agent tracking

## Yapı

```
OpenClaudeClaw/
├── src/openclaudeclaw/    # Ana paket (45 modül)
│   ├── tools/             # 42 tool implementasyonu
│   ├── runtime.py         # HarnessRuntime
│   ├── tool_pool.py       # Tool registry
│   ├── context_builder.py # Context merge
│   └── ...
├── install.py             # Kurulum sihirbazı
├── demos/                 # 3 örnek workflow
├── tests/                 # Test suite
├── docs/                  # Dokümantasyon
├── README.md
├── LICENSE                # MIT
└── requirements.txt
```

## Kurulum

```bash
git clone https://github.com/ayzekdiolar/OpenClaudeClaw.git
cd OpenClaudeClaw
python3 install.py
```

## Demo

```bash
python3 demos/demo1_cargo_research.py  # Cargo araştırma
python3 demos/demo2_plan_lsp.py        # Plan mode + LSP
python3 demos/demo3_repl.py            # REPL execution
```

## Test

```bash
python3 tests/test_all.py
```

## İstatistikler

- **Toplam dosya:** 68
- **Python modülü:** 45 (src/) + 16 (tools/)
- **Tool sayısı:** 42
- **Dokümantasyon:** 3 MD dosyası
- **Demo:** 3 adet
- **Test:** 1 suite

## Lisans

MIT — Ayzekdiolar (2026)

---

**Not:** Hiçbir kişisel bilgi içermez. Tamamen genel kullanım için.

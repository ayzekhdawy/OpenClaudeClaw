# Sürüm 1.0.0 — İlk Yayın

**Tarih:** 2026-04-01  
**Geliştirici:** Ayzekdiolar

## Yeni Özellikler

### 42 Tool
- **Core (8):** Bash, Read, Write, Edit, Glob, Grep, Think, Task
- **Extended (19):** TodoWrite, WebFetch, WebSearch, Brief, SendMessage, Task CRUD, AskUserQuestion, ToolSearch, Sleep, Config, NotebookEdit, MCP Resources, SyntheticOutput
- **Advanced (15):** LSP, REPL, Plan Mode (4 tool), Worktree (3 tool), Skill, AnswerQuestion, Agent, Runtime, AnalyzeContext, MCP, Schedule

### Harness Sistemi
- **Context Builder:** SOUL + MEMORY + USER otomatik birleştirme
- **State Management:** `.harness/` dizininde persistent state
- **Policy Engine:** Tool bazlı izinler + approval flow
- **Cache:** 60 saniye TTL ile hızlı context analizi
- **Event Bus:** Async event handling
- **Agent Registry:** Sub-agent tracking + steering
- **Skill Registry:** Wizard mode ile skill oluşturma

### Kurulum Sihirbazı
- Seçmeli kurulum (Core/Extended/Advanced/Hepsi)
- Otomatik state dizini yapılandırması
- Policy engine konfigürasyonu
- Cache sistemi ayarları

### Dokümantasyon
- README.md — Genel bakış
- docs/USAGE.md — Detaylı kullanım kılavuzu
- demos/ — 3 örnek workflow (cargo araştırma, plan mode, REPL)
- tests/test_all.py — Test suite

## Teknik Detaylar

- **Python:** 3.10+
- **Bağımlılıklar:** openclaudeclaw, pathlib, jsonschema, pyyaml
- **Lisans:** MIT
- **Boyut:** ~200 KB (source)

## Kurulum

```bash
git clone https://github.com/ayzekdiolar/OpenClaudeClaw.git
cd OpenClaudeClaw
python3 install.py
```

## Demo

```bash
python3 demos/demo1_cargo_research.py
python3 demos/demo2_plan_lsp.py
python3 demos/demo3_repl.py
```

## Test

```bash
python3 tests/test_all.py
```

---

**Not:** Bu sürüm Claude Code'dan esinlenilmiştir ama tamamen Python/OpenClaw için özgün olarak yazılmıştır.

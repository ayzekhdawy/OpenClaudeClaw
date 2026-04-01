# OpenClaudeClaw

**OpenClaw için gelişmiş harness sistemi** — 42 tool, state management, context builder, policy engine.

## Özellikler

- **42 Tool** — Bash, Read, Write, Edit, Glob, Grep, LSP, REPL, Task, MCP, Plan Mode, Worktree ve daha fazlası
- **Harness Context** — SOUL, MEMORY, USER otomatik birleştirme
- **State Management** — `.harness/` dizininde persistent state
- **Policy Engine** — Tool bazlı izinler + approval flow
- **Cache Sistemi** — 60 saniye TTL ile hızlı context analizi
- **Event Bus** — Async event handling
- **Agent Registry** — Sub-agent tracking + steering
- **Skill Registry** — Wizard mode ile skill oluşturma

## Kurulum

```bash
# OpenClaudeClaw kurulum sihirbazını çalıştır
python3 install.py
```

Kurulum sihirbazı size şunları sorar:
- Hangi tool'ları kurmak istiyorsunuz? (Core/Extended/All)
- State dizini neresi olsun? (varsayılan: `.harness/`)
- Policy engine aktif olsun mu?
- Cache sistemi aktif olsun mu?

## Hızlı Başlangıç

```python
from openclaudeclaw import HarnessRuntime, get_tool_pool

# Runtime oluştur
runtime = HarnessRuntime()

# Tool pool'a eriş
pool = get_tool_pool()

# Tool çalıştır
result = pool.execute("Bash", {"command": "echo 'Merhaba Dünya'"})
print(result.output)

# Context builder kullan
from openclaudeclaw.context_builder import build_context
ctx = build_context("Flech için cargo fiyatlarını araştır")
print(ctx.full_prompt)
```

## Tool Kategorileri

### Core Tools (8)
- `Bash` — Shell komutları çalıştır
- `Read` — Dosya oku
- `Write` — Dosya yaz
- `Edit` — Dosya düzenle
- `Glob` — Dosya ara (pattern)
- `Grep` — İçerik ara
- `Think` — Düşünce notu
- `Task` — Task yönetimi

### Extended Tools (19)
- `TodoWrite` — Todo listesi
- `WebFetch` — Web sayfası çek
- `WebSearch` — Web araması
- `Brief` — Kullanıcıya mesaj
- `SendMessage` — Mesaj gönder
- `TaskCreate/Get/Update/Stop` — Task CRUD
- `AskUserQuestion` — Çoklu soru
- `ToolSearch` — Tool ara
- `Sleep` — Bekleme
- `Config` — Konfigürasyon
- `NotebookEdit` — Jupyter notebook düzenle
- `ListMcpResources` — MCP server listesi
- `ReadMcpResource` — MCP resource oku
- `SyntheticOutput` — Şablon tabanlı çıktı

### Advanced Tools (15)
- `LSP` — Code intelligence (goto definition, references, symbols)
- `REPL` — Interactive Python shell
- `EnterPlanMode/ExitPlanMode/UpdatePlan/PlanStatus` — Planlama sistemi
- `EnterWorktree/ExitWorktree/WorktreeList` — Git worktree yönetimi
- `Skill` — Skill registry + wizard mode
- `AnswerQuestion` — Soru cevaplama
- `Agent` — Sub-agent yönetimi
- `Runtime` — Runtime status
- `AnalyzeContext` — Context analizi + cache
- `MCP` — MCP wrapper
- `Schedule` — Cron job yönetimi

## Yapı

```
openclaudeclaw/
├── src/
│   └── openclaudeclaw/
│       ├── __init__.py
│       ├── runtime.py          # HarnessRuntime
│       ├── tool_pool.py        # 42 tool registry
│       ├── context_builder.py  # Context merge
│       ├── policy_engine.py    # İzin sistemi
│       ├── models.py           # Data modelleri
│       ├── state.py            # State management
│       ├── event_bus.py        # Event handling
│       ├── agent_registry.py   # Sub-agent tracking
│       ├── skills.py           # Skill registry
│       ├── schedule.py         # Cron store
│       └── tools/              # 42 tool implementasyonu
│           ├── core_tools.py
│           ├── extended_tools.py
│           ├── advanced_tools.py
│           └── ...
├── install.py                  # Kurulum sihirbazı
├── README.md
├── LICENSE
└── requirements.txt
```

## Lisans

MIT License — Detaylar için `LICENSE` dosyasına bakın.

## Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/yeni-ozellik`)
3. Commit yapın (`git commit -m 'Yeni özellik eklendi'`)
4. Push edin (`git push origin feature/yeni-ozellik`)
5. Pull Request açın

## Destek

- GitHub Issues: [Report bug or request feature]
- Discord: [OpenClaw topluluğu]
- Dokümantasyon: `docs/` dizini

---

**Geliştirici:** Ayzekdiolar  
**Versiyon:** 1.0.0  
**Son Güncelleme:** 2026-04-01

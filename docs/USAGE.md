# OpenClaudeClaw Dokümantasyonu

## Kurulum

1. Repoyu klonlayın:
```bash
git clone https://github.com/ayzekdiolar/OpenClaudeClaw.git
cd OpenClaudeClaw
```

2. Kurulum sihirbazını çalıştırın:
```bash
python3 install.py
```

3. Sihirbaz size şunları sorar:
   - Hangi tool paketlerini kurmak istiyorsunuz? (Core/Extended/Advanced/Hepsi)
   - State dizini neresi olsun?
   - Policy Engine aktif olsun mu?
   - Cache sistemi aktif olsun mu?

## Hızlı Başlangıç

### Temel Kullanım

```python
from openclaudeclaw import HarnessRuntime, get_tool_pool

# Runtime oluştur
runtime = HarnessRuntime()

# Tool pool'a eriş
pool = get_tool_pool()

# Bash komutu çalıştır
result = pool.execute("Bash", {"command": "ls -la"})
print(result.output)

# Dosya oku
result = pool.execute("Read", {"path": "README.md"})
print(result.output[:500])
```

### Context Builder

```python
from openclaudeclaw.context_builder import build_context

# Görev için context oluştur
ctx = build_context("Flech için cargo fiyatlarını araştır")

# Tüm context'i tek prompt olarak al
print(ctx.full_prompt)

# Bileşenlere eriş
print(ctx.persona)      # SOUL.md içeriği
print(ctx.user)         # USER.md içeriği
print(ctx.memory)       # MEMORY.md içeriği
print(ctx.task_context) # Göreve özel context
```

### Task Yönetimi

```python
# Yeni task oluştur
task = pool.execute("TaskCreate", {
    "description": "Cargo fiyatlarını karşılaştır",
    "priority": "high"
})

# Task'ı güncelle
pool.execute("TaskUpdate", {
    "task_id": task.task_id,
    "status": "in_progress"
})

# Task'ı tamamla
pool.execute("TaskStop", {"task_id": task.task_id})
```

### Plan Mode

```python
# Plan moduna gir
pool.execute("EnterPlanMode", {
    "mode": "plan",
    "description": "Cargo araştırma planı"
})

# Plan durumunu kontrol et
result = pool.execute("PlanStatus", {})
print(result.output)

# Plan modundan çık
pool.execute("ExitPlanMode", {"action": "discard"})
```

### LSP (Code Intelligence)

```python
# Symbol listesi al
result = pool.execute("LSP", {
    "operation": "documentSymbol",
    "file_path": "src/openclaudeclaw/tool_pool.py"
})
print(result.output)

# Definition'a git
result = pool.execute("LSP", {
    "operation": "goToDefinition",
    "file_path": "src/openclaudeclaw/tool_pool.py",
    "line": 42,
    "character": 10
})
```

### REPL (Interactive Python)

```python
# REPL başlat
pool.execute("REPL", {"command": "start"})

# Kod çalıştır
result = pool.execute("REPL", {
    "command": "eval",
    "code": "import json; print(json.dumps({'status': 'ok'}))"
})
print(result.output)

# REPL durdur
pool.execute("REPL", {"command": "stop"})
```

## Tool Referansı

### Core Tools (8)

| Tool | Açıklama | Input |
|------|----------|-------|
| `Bash` | Shell komutu çalıştır | `{"command": "ls -la", "cwd": "/path", "timeout": 30}` |
| `Read` | Dosya oku | `{"path": "file.txt", "offset": 0, "limit": 100}` |
| `Write` | Dosya yaz | `{"path": "file.txt", "content": "..."}` |
| `Edit` | Dosya düzenle | `{"path": "file.txt", "old_text": "...", "new_text": "..."}` |
| `Glob` | Pattern ile dosya ara | `{"pattern": "*.py"}` |
| `Grep` | İçerik ara | `{"pattern": "class ", "path": "src/"}` |
| `Think` | Düşünce notu | `{"thought": "Bu görev için..."}` |
| `Task` | Task yönetimi | `{"description": "...", "priority": "high"}` |

### Extended Tools (19)

| Tool | Açıklama |
|------|----------|
| `TodoWrite` | Todo listesi yönetimi |
| `WebFetch` | Web sayfası çek |
| `WebSearch` | Web araması (Brave API) |
| `Brief` | Kullanıcıya mesaj gönder |
| `SendMessage` | Mesaj gönder (webhook) |
| `TaskCreate` | Yeni task oluştur |
| `TaskGet` | Task getir |
| `TaskUpdate` | Task güncelle |
| `TaskStop` | Task durdur |
| `AskUserQuestion` | Çoklu soru sor |
| `ToolSearch` | Tool ara |
| `Sleep` | Bekleme (ms) |
| `Config` | Konfigürasyon oku/yaz |
| `NotebookEdit` | Jupyter notebook düzenle |
| `ListMcpResources` | MCP server listesi |
| `ReadMcpResource` | MCP resource oku |
| `SyntheticOutput` | Şablon tabanlı çıktı |

### Advanced Tools (15)

| Tool | Açıklama |
|------|----------|
| `LSP` | Code intelligence (AST-based) |
| `REPL` | Interactive Python shell |
| `EnterPlanMode` | Plan moduna gir |
| `ExitPlanMode` | Plan modundan çık |
| `UpdatePlan` | Plan güncelle |
| `PlanStatus` | Plan durumu |
| `EnterWorktree` | Git worktree oluştur/aç |
| `ExitWorktree` | Worktree'den çık |
| `WorktreeList` | Worktree listesi |
| `Skill` | Skill registry + wizard |
| `AnswerQuestion` | Soru cevapla |
| `Agent` | Sub-agent yönetimi |
| `Runtime` | Runtime status |
| `AnalyzeContext` | Context analizi + cache |
| `MCP` | MCP wrapper |
| `Schedule` | Cron job yönetimi |

## Yapılandırma

### Environment Variables

`.openclaudeclaw.env` dosyasında tanımlanır:

```bash
OPENCLAUDECLAW_VERSION=1.0.0
STATE_DIR=.harness
POLICY_ENGINE=true
CACHE_ENABLED=true
CACHE_TTL=60
LOG_LEVEL=INFO
```

### Policy Engine

`.harness/permissions.json` — Tool bazlı izinler:

```json
{
  "auto_approve": ["Read", "Glob", "Think", "TodoWrite"],
  "require_approval": ["Bash", "Write", "Edit", "WebFetch"],
  "deny": []
}
```

### Cache Sistemi

`.harness/cache_config.json`:

```json
{
  "enabled": true,
  "ttl_seconds": 60,
  "max_entries": 100
}
```

## State Management

State dosyaları `.harness/` dizininde saklanır:

- `tasks.json` — Task state
- `plan_state.json` — Plan mode state
- `worktree_state.json` — Worktree state
- `repl_state.json` — REPL state
- `todo_state.json` — Todo state
- `permissions.json` — Policy permissions
- `cache_config.json` — Cache ayarları

## Test

```bash
# Tüm testleri çalıştır
pytest tests/

# Tek tool testi
python3 -c "
from openclaudeclaw import get_tool_pool
pool = get_tool_pool()
r = pool.execute('Bash', {'command': 'echo 1'})
print('OK' if r.success else 'FAIL')
"
```

## SSS

**S: OpenClaw ile nasıl entegre olur?**
A: OpenClaudeClaw, OpenClaw üzerinde çalışır. `openclaw.json` konfigürasyonuna harness path'i ekleyin.

**S: Claude Code ile aynı mı?**
A: Claude Code'dan esinlenilmiştir ama tamamen Python/OpenClaw için yazılmıştır.

**S: 42 tool'un hepsi gerekli mi?**
A: Hayır. Kurulum sihirbazı ile sadece ihtiyacınız olanları seçebilirsiniz.

**S: Cache ne işe yarar?**
A: Context analizini 60 saniye boyunca cache'ler. Aynı query için 0ms yanıt süresi.

---

**Geliştirici:** Ayzekdiolar  
**Versiyon:** 1.0.0  
**Lisans:** MIT

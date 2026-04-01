# Demo 2: Plan Mode + LSP Kullanımı

**Senaryo:** Yeni bir Python projesine başla, plan oluştur, kod analizi yap.

```python
from openclaudeclaw import HarnessRuntime, get_tool_pool

runtime = HarnessRuntime()
pool = get_tool_pool()

print("=== Demo 2: Plan Mode + LSP ===\n")

# 1. Plan moduna gir
plan = pool.execute("EnterPlanMode", {
    "mode": "plan",
    "description": "Python proje iskeleti oluştur"
})
print(f"Plan mode: {plan.output}")

# 2. Mevcut Python dosyalarını listele
glob_result = pool.execute("Glob", {"pattern": "*.py"})
print(f"\nPython dosyaları: {len(glob_result.output.splitlines())} adet")

# 3. LSP ile symbol analizi yap
lsp_result = pool.execute("LSP", {
    "operation": "documentSymbol",
    "file_path": "src/openclaudeclaw/tool_pool.py"
})
symbols = [line.strip() for line in lsp_result.output.split('\n') if line.startswith('[')]
print(f"\nTool pool symbols: {len(symbols)} adet")
for sym in symbols[:5]:
    print(f"  • {sym}")

# 4. Task'ları oluştur
tasks = [
    ("Proje iskeleti oluştur", "high"),
    ("Tool'ları yaz", "high"),
    ("Testleri yaz", "medium"),
    ("Dokümantasyon", "low"),
]

for desc, priority in tasks:
    task = pool.execute("TaskCreate", {
        "description": desc,
        "priority": priority
    })
    print(f"Task oluşturuldu: {desc} ({priority})")

# 5. Plan durumunu göster
status = pool.execute("PlanStatus", {})
print(f"\n{status.output}")

# 6. Todo listesi güncelle
pool.execute("TodoWrite", {
    "todos": [
        {"content": "Proje iskeleti", "status": "completed"},
        {"content": "Tool'ları yaz", "status": "in_progress"},
        {"content": "Testleri yaz", "status": "pending"},
        {"content": "Dokümantasyon", "status": "pending"},
    ]
})

# 7. Think ile not ekle
pool.execute("Think", {
    "thought": "LSP analizi başarılı. 32 symbol bulundu. Tool pool yapısı Claude Code ile uyumlu."
})

# 8. Plan modundan çık (discard)
exit_plan = pool.execute("ExitPlanMode", {"action": "discard"})
print(f"\nPlan mode: {exit_plan.output}")

print("\n✓ Demo 2 tamamlandı!")
```

## Çalıştırma

```bash
cd /home/ayzek/.openclaw/workspace/repos/OpenClaudeClaw
python3 demos/demo2_plan_lsp.py
```

## Beklenen Çıktı

```
=== Demo 2: Plan Mode + LSP ===

Plan mode: [PLAN MODE] Plan modu aktif...

Python dosyaları: 45 adet

Tool pool symbols: 32 adet
  • [class] ToolPool @ line 380
  • [def] __init__ @ line 387
  ...

Task oluşturuldu: Proje iskeleti oluştur (high)
Task oluşturuldu: Tool'ları yaz (high)
...

[PLAN] 4 task, 1 plan aktif...

Plan mode: [PLAN MODE] Plan modu kapatıldı.

✓ Demo 2 tamamlandı!
```

---

**Süre:** ~5 saniye  
**Tool kullanımı:** EnterPlanMode(1), Glob(1), LSP(1), TaskCreate(4), PlanStatus(1), TodoWrite(1), Think(1), ExitPlanMode(1)

# Demo 3: REPL + Code Execution

**Senaryo:** Interactive Python shell ile veri işleme.

```python
from openclaudeclaw import HarnessRuntime, get_tool_pool
import json

runtime = HarnessRuntime()
pool = get_tool_pool()

print("=== Demo 3: REPL + Code Execution ===\n")

# 1. REPL başlat
start = pool.execute("REPL", {"command": "start"})
print(f"REPL: {start.output}")

# 2. Veri işleme kodu çalıştır
code1 = """
import json
data = {
    "markalar": ["Urbica", "Flech", "Morecano"],
    "ciro": [73000, 45000, 12000],
    "ay": "Mart 2026"
}
print(json.dumps(data, indent=2, ensure_ascii=False))
"""

result = pool.execute("REPL", {
    "command": "eval",
    "code": code1
})
print(f"\nVeri işleme sonucu:\n{result.output}")

# 3. Hesaplama yap
code2 = """
ciro = [73000, 45000, 12000]
toplam = sum(ciro)
ortalama = toplam / len(ciro)
buyume = ((ciro[0] - ciro[1]) / ciro[1]) * 100
print(f"Toplam ciro: {toplam:,.0f} TL")
print(f"Ortalama: {ortalama:,.0f} TL")
print(f"Urbica-Flech büyüme: %{buyume:.1f}")
"""

result = pool.execute("REPL", {
    "command": "eval",
    "code": code2
})
print(f"\nHesaplama:\n{result.output}")

# 4. Hata yakalama
code3 = """
# Kasıtlı hata
x = 1 / 0
"""

result = pool.execute("REPL", {
    "command": "eval",
    "code": code3
})
print(f"\nHata durumu:\nSuccess: {result.success}\nError: {result.error or result.output}")

# 5. REPL history göster
history = pool.execute("REPL", {"command": "history"})
print(f"\n{history.output}")

# 6. REPL durdur
stop = pool.execute("REPL", {"command": "stop"})
print(f"\nREPL: {stop.output}")

print("\n✓ Demo 3 tamamlandı!")
```

## Çalıştırma

```bash
cd /home/ayzek/.openclaw/workspace/repos/OpenClaudeClaw
python3 demos/demo3_repl.py
```

## Beklenen Çıktı

```
=== Demo 3: REPL + Code Execution ===

REPL: [REPL] Python REPL started...

Veri işleme sonucu:
{
  "markalar": ["Urbica", "Flech", "Morecano"],
  "ciro": [73000, 45000, 12000],
  "ay": "Mart 2026"
}

Hesaplama:
Toplam ciro: 130,000 TL
Ortalama: 43,333 TL
Urbica-Flech büyüme: %62.2

Hata durumu:
Success: False
Error: [ERROR] ... ZeroDivisionError ...

[REPL Session]
Started: 2026-04-01 21:00:00
Executions: 3
Last output: ...

REPL: [REPL] Stopped. 3 executions.

✓ Demo 3 tamamlandı!
```

---

**Süre:** ~3 saniye  
**Tool kullanımı:** REPL(5: start, eval x3, history, stop)

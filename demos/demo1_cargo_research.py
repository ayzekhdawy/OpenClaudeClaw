# Demo 1: Cargo Fiyatı Araştırması

**Senaryo:** Flech markası için Yurtiçi ve Sürat kargo fiyatlarını karşılaştır.

```python
from openclaudeclaw import HarnessRuntime, get_tool_pool
from openclaudeclaw.context_builder import build_context

# Runtime başlat
runtime = HarnessRuntime()
pool = get_tool_pool()

# 1. Context oluştur (SOUL + MEMORY + USER otomatik yüklenir)
ctx = build_context("Flech için cargo fiyatlarını araştır ve karşılaştır")
print(f"Context hazır: {len(ctx.full_prompt)} chars")

# 2. Web araması yap
search_result = pool.execute("WebSearch", {
    "query": "Yurtiçi kargo fiyatları 2026",
    "count": 5
})
print(f"Yurtiçi sonuçları: {search_result.output[:300]}...")

search_result = pool.execute("WebSearch", {
    "query": "Sürat kargo fiyatları 2026",
    "count": 5
})
print(f"Sürat sonuçları: {search_result.output[:300]}...")

# 3. Web sayfalarını fetch et
if search_result.urls:
    fetch_result = pool.execute("WebFetch", {
        "url": search_result.urls[0]
    })
    print(f"İçerik: {fetch_result.output[:500]}...")

# 4. Düşünce notu ekle
pool.execute("Think", {
    "thought": "Yurtiçi cam ürünlerde %20 indirim yapıyor. Sürat daha pahalı ama hızlı."
})

# 5. Task oluştur
task = pool.execute("TaskCreate", {
    "description": "Cargo firması seç ve İshak'a raporla",
    "priority": "high"
})

# 6. Brief ile kullanıcıya mesaj gönder
pool.execute("Brief", {
    "message": """
**Cargo Karşılaştırma — Flech**

| Firma | Fiyat | Süre | Cam Ürün |
|-------|-------|------|----------|
| Yurtiçi | 85 TL | 2-3 gün | %20 indirim |
| Sürat | 95 TL | 1-2 gün | Standart |

**Öneri:** Yurtiçi kargo (cam ürünlerde indirim).

Detaylı analiz gerekli mi?
""",
    "status": "normal"
})

# 7. Task'ı tamamla
pool.execute("TaskStop", {"task_id": task.task_id})

print("\n✓ Demo tamamlandı!")
```

## Çalıştırma

```bash
cd /home/ayzek/.openclaw/workspace/repos/OpenClaudeClaw
python3 demos/demo1_cargo_research.py
```

## Beklenen Çıktı

```
Context hazır: 2828 chars
Yurtiçi sonuçları: [5 sonuç listesi]...
Sürat sonuçları: [5 sonuç listesi]...
İçerik: [Sayfa içeriği]...
✓ Demo tamamlandı!
```

---

**Süre:** ~15 saniye  
**Tool kullanımı:** WebSearch(2), WebFetch(1), Think(1), TaskCreate(1), Brief(1), TaskStop(1)

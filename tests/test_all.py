# OpenClaudeClaw Test Suite

```bash
#!/usr/bin/env python3
"""
OpenClaudeClaw — Test Suite
──────────────────────────────────────────────────────────
Tüm tool'ları test eder.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from openclaudeclaw.tool_pool import ToolPool


def test_tool_pool_init():
    """Tool pool oluşturma testi."""
    print("Test: Tool pool init... ", end="")
    t0 = time.time()
    pool = ToolPool()
    elapsed = time.time() - t0
    
    assert len(pool.tools) == 42, f"Beklenen: 42, Bulunan: {len(pool.tools)}"
    print(f"OK ({elapsed:.2f}s, {len(pool.tools)} tools)")
    return pool


def test_core_tools(pool):
    """Core tool'ları test et."""
    tests = [
        ("Bash", {"command": "echo 1"}, lambda r: "1" in r.output),
        ("Read", {"path": "README.md", "limit": 3}, lambda r: r.success),
        ("Glob", {"pattern": "*.py"}, lambda r: len(r.output.splitlines()) > 0),
        ("Grep", {"pattern": "class ", "path": "src/"}, lambda r: r.success),
        ("Think", {"thought": "test"}, lambda r: r.success),
        ("Task", {"description": "test"}, lambda r: r.success),
    ]
    
    print("\nCore Tools:")
    for name, inp, check in tests:
        t0 = time.time()
        r = pool.execute(name, inp)
        elapsed = time.time() - t0
        status = "✓" if check(r) else "✗"
        print(f"  {status} {name}: {elapsed:.2f}s")


def test_extended_tools(pool):
    """Extended tool'ları test et."""
    tests = [
        ("TodoWrite", {"todos": [{"status": "done", "content": "test"}]}, lambda r: r.success),
        ("Brief", {"message": "test"}, lambda r: r.success),
        ("Sleep", {"duration_ms": 100}, lambda r: r.success),
        ("ToolSearch", {"query": "bash"}, lambda r: r.success),
    ]
    
    print("\nExtended Tools:")
    for name, inp, check in tests:
        t0 = time.time()
        r = pool.execute(name, inp)
        elapsed = time.time() - t0
        status = "✓" if check(r) else "✗"
        print(f"  {status} {name}: {elapsed:.2f}s")


def test_advanced_tools(pool):
    """Advanced tool'ları test et."""
    tests = [
        ("LSP", {"operation": "documentSymbol", "file_path": "src/openclaudeclaw/tool_pool.py"}, lambda r: r.success),
        ("REPL", {"command": "eval", "code": "print(1+1)"}, lambda r: r.success and "2" in r.output),
        ("EnterPlanMode", {"mode": "plan", "description": "test"}, lambda r: r.success),
        ("PlanStatus", {}, lambda r: r.success),
        ("ExitPlanMode", {"action": "discard"}, lambda r: r.success),
        ("Skill", {"command": "list"}, lambda r: r.success),
    ]
    
    print("\nAdvanced Tools:")
    for name, inp, check in tests:
        t0 = time.time()
        r = pool.execute(name, inp)
        elapsed = time.time() - t0
        status = "✓" if check(r) else "✗"
        print(f"  {status} {name}: {elapsed:.2f}s")


def test_context_builder():
    """Context builder testi."""
    print("\nContext Builder:")
    from openclaudeclaw.context_builder import build_context
    
    t0 = time.time()
    ctx = build_context("Test görev")
    elapsed = time.time() - t0
    
    assert len(ctx.full_prompt) > 0, "Prompt boş"
    assert len(ctx.persona) > 0, "Persona boş"
    assert len(ctx.user) > 0, "User boş"
    
    print(f"  ✓ build_context: {elapsed:.2f}s ({len(ctx.full_prompt)} chars)")


def main():
    print("=" * 50)
    print("OpenClaudeClaw — Test Suite")
    print("=" * 50)
    
    # Testler
    pool = test_tool_pool_init()
    test_core_tools(pool)
    test_extended_tools(pool)
    test_advanced_tools(pool)
    test_context_builder()
    
    print("\n" + "=" * 50)
    print("Tüm testler tamamlandı!")
    print("=" * 50)


if __name__ == "__main__":
    main()

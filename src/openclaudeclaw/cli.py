"""
Harness CLI — Command Line Interface
──────────────────────────────────
Test ve yönetim için CLI.

Kullanım:
  python3 -m src.harness.cli list
  python3 -m src.harness.cli run "prompt"
  python3 -m src.harness.cli task list
  python3 -m src.harness.cli task create "task name"
  python3 -m src.harness.cli tools
"""

import sys
import json
from pathlib import Path

WORKSPACE = Path("/home/ayzek/.openclaw/workspace")
sys.path.insert(0, str(WORKSPACE))


def cmd_list():
    """Tool listesini göster."""
    from src.harness import get_tool_pool
    
    pool = get_tool_pool()
    tools = pool.list_tools()
    
    print("=" * 70)
    print("HARNESS TOOLS")
    print("=" * 70)
    print(f"Toplam: {len(tools)} tool\n")
    
    for t in tools:
        print(f"Tool: {t.name}")
        print(f"Description: {t.description.strip().split(chr(10))[0][:60]}...")
        print(f"Patterns: {', '.join(t.patterns[:5])}")
        print("-" * 40)


def cmd_tools():
    """Tool'lari detayli goster."""
    from src.harness import get_tool_pool
    
    pool = get_tool_pool()
    tools = pool.list_tools()
    
    print("=" * 70)
    print("HARNESS TOOLS - DETAYLI")
    print("=" * 70)
    
    for t in tools:
        print(f"\n## {t.name}")
        print(f"Category: {t.category}")
        print(f"Patterns: {t.patterns}")
        print(f"Readonly: {t.readonly}")
        print(f"\nDescription ({len(t.description)} chars):")
        # Show first 20 lines
        lines = t.description.strip().split('\n')[:20]
        for line in lines:
            print(f"  {line}")


def cmd_run(prompt: str):
    """Prompt calistir."""
    from src.harness import route_prompt, get_semantic_memory, get_task_pool, get_cost_tracker
    from src.harness.system_prompt import build_esra_system_prompt
    
    print("=" * 70)
    print(f"RUN: {prompt}")
    print("=" * 70)
    
    # 1. Routing
    print("\n1. Routing...")
    route = route_prompt(prompt)
    print(f"   Route: {route['route']} ({route['score']} puan)")
    print(f"   Keywords: {route.get('keywords', [])}")
    
    # 2. Memory
    print("\n2. Semantic Memory...")
    sm = get_semantic_memory()
    relevant = sm.find_relevant(prompt, use_llm=False)
    print(f"   Relevant: {len(relevant)} files")
    for f in relevant[:3]:
        print(f"   - {f.filename}")
    
    # 3. Context
    print("\n3. Context...")
    context = sm.get_context_for_task(prompt, use_llm=False)
    print(f"   Length: {len(context)} chars")
    
    # 4. Task
    print("\n4. Task Pool...")
    task_pool = get_task_pool()
    
    # Check if multi-step
    if any(kw in prompt.lower() for kw in ['plan', 'adim', 'hazirla', 'olustur', 'yap']):
        task = task_pool.task_create(
            name=prompt[:50],
            description=f"Multi-step task: {prompt}",
            priority="HIGH",
            assigned_to="esra",
        )
        print(f"   Task created: {task['task_id']}")
        
        # Mark in progress
        task_pool.task_update(task['task_id'], status="in_progress")
        print(f"   Status: in_progress")
    
    # 5. System Prompt
    print("\n5. System Prompt...")
    sys_prompt = build_esra_system_prompt()
    print(f"   Length: {len(sys_prompt)} chars")
    
    # 6. Cost
    print("\n6. Cost...")
    tracker = get_cost_tracker()
    print(f"   Summary: {tracker.get_summary()}")
    
    print("\n" + "=" * 70)
    print("TAMAMLANDI")
    print("=" * 70)


def cmd_task(args: list):
    """Task yonetimi."""
    from src.harness import get_task_pool
    
    task_pool = get_task_pool()
    
    if not args:
        print("Kullanim: harness/cli.py task [create|list|get|update|delete|stats]")
        return
    
    action = args[0]
    
    if action == "list":
        result = task_pool.task_list(status="pending")
        print(f"Pending Tasks ({result['total']}):")
        for t in result["tasks"]:
            print(f"  [{t['priority']}] {t['name']} - {t['id']}")
    
    elif action == "stats":
        stats = task_pool.task_stats()
        print(f"Tasks: {stats['total']}")
        print(f"  Pending: {stats['pending']}")
        print(f"  Done: {stats['done']}")
    
    elif action == "create" and len(args) > 1:
        name = ' '.join(args[1:])
        result = task_pool.task_create(
            name=name,
            priority="NORMAL",
            assigned_to="esra",
        )
        print(f"Created: {result['task_id']} - {name}")
    
    elif action == "update" and len(args) > 2:
        task_id = args[1]
        status = args[2]
        result = task_pool.task_update(task_id, status=status)
        print(f"Updated: {result.get('id', task_id)} -> {status}")
    
    elif action == "get" and len(args) > 1:
        task_id = args[1]
        result = task_pool.task_get(task_id)
        if result:
            print(json.dumps(result, indent=2))
        else:
            print(f"Not found: {task_id}")
    
    elif action == "delete" and len(args) > 1:
        task_id = args[1]
        result = task_pool.task_delete(task_id)
        print(f"Deleted: {result['deleted']}")
    
    else:
        print(f"Bilinmeyen action: {action}")


def main():
    args = sys.argv[1:]
    
    if not args:
        print("Harness CLI")
        print("Kullanim:")
        print("  python3 -m src.harness.cli list")
        print("  python3 -m src.harness.cli tools")
        print("  python3 -m src.harness.cli run 'prompt'")
        print("  python3 -m src.harness.cli task list")
        print("  python3 -m src.harness.cli task create 'task name'")
        return
    
    cmd = args[0]
    
    if cmd == "list":
        cmd_list()
    elif cmd == "tools":
        cmd_tools()
    elif cmd == "run":
        prompt = ' '.join(args[1:]) if len(args) > 1 else ""
        if not prompt:
            print("Kullanim: harness/cli.py run 'prompt'")
            return
        cmd_run(prompt)
    elif cmd == "task":
        cmd_task(args[1:])
    else:
        print(f"Bilinmeyen komut: {cmd}")


if __name__ == "__main__":
    main()

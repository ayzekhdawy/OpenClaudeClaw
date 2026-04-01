#!/usr/bin/env python3
"""
OpenClaudeClaw Kurulum Sihirbazı
──────────────────────────────────────────────────────────
Kullanıcıya seçmeli kurulum sunar.
"""

import os
import sys
import json
from pathlib import Path

# Renkler
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RED = "\033[91m"
RESET = "\033[0m"


def print_header():
    print(f"""
{BLUE}╔══════════════════════════════════════════════════╗
║     OpenClaudeClaw — Kurulum Sihirbazı          ║
╚══════════════════════════════════════════════════╝{RESET}
""")


def ask_question(question: str, options: list, default: int = 0) -> int:
    """Kullanıcıya soru sor, seçenek sun."""
    print(f"\n{YELLOW}? {question}{RESET}")
    for i, opt in enumerate(options):
        marker = "✓" if i == default else " "
        print(f"  [{marker}] {i+1}. {opt}")
    
    while True:
        try:
            choice = input(f"\nSeçiminiz (1-{len(options)}, varsayılan:{default+1}): ").strip()
            if not choice:
                return default
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return idx
            print(f"{RED}Geçersiz seçim, tekrar deneyin.{RESET}")
        except KeyboardInterrupt:
            print(f"\n{RED}Kurulum iptal edildi.{RESET}")
            sys.exit(1)
        except ValueError:
            print(f"{RED}Lütfen sayı girin.{RESET}")


def ask_yes_no(question: str, default: bool = True) -> bool:
    """Evet/Hayır sorusu."""
    suffix = "Y/n" if default else "y/N"
    choice = input(f"\n{YELLOW}? {question} [{suffix}]: {RESET}").strip().lower()
    if not choice:
        return default
    return choice in ("y", "yes", "e", "evet")


def select_tools():
    """Tool paketi seçimi."""
    packages = [
        ("Core Tools (8 tool)", ["Bash", "Read", "Write", "Edit", "Glob", "Grep", "Think", "Task"]),
        ("Extended Tools (19 tool)", ["TodoWrite", "WebFetch", "WebSearch", "Brief", "SendMessage", "Task CRUD", "AskUserQuestion", "ToolSearch", "Sleep", "Config", "NotebookEdit", "MCP Resources", "SyntheticOutput"]),
        ("Advanced Tools (15 tool)", ["LSP", "REPL", "Plan Mode", "Worktree", "Skill", "Agent", "Runtime", "AnalyzeContext", "MCP", "Schedule"]),
        ("Hepsi (42 tool)", "all"),
    ]
    
    print(f"\n{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"{YELLOW}Hangi tool paketlerini kurmak istiyorsunuz?{RESET}")
    
    selected = []
    for pkg_name, tools in packages:
        if ask_yes_no(f"  {pkg_name} kurulsun mu?", default=True):
            selected.append(pkg_name)
    
    return selected


def configure_state():
    """State dizini yapılandırması."""
    print(f"\n{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"{YELLOW}State dizini yapılandırması{RESET}")
    
    default_path = ".harness"
    custom_path = input(f"\nState dizini yolu (varsayılan: {default_path}): ").strip()
    state_path = custom_path or default_path
    
    # Dizin oluştur
    Path(state_path).mkdir(parents=True, exist_ok=True)
    print(f"{GREEN}✓ State dizini oluşturuldu: {state_path}{RESET}")
    
    return state_path


def configure_policy():
    """Policy engine yapılandırması."""
    print(f"\n{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"{YELLOW}Policy Engine yapılandırması{RESET}")
    
    enable_policy = ask_yes_no("Policy Engine aktif olsun mu? (tool izinleri)", default=True)
    
    if enable_policy:
        permissions = {
            "auto_approve": ["Read", "Glob", "Think", "TodoWrite", "Brief", "PlanStatus", "WorktreeList"],
            "require_approval": ["Bash", "Write", "Edit", "WebFetch", "TaskCreate", "TaskUpdate", "TaskStop"],
            "deny": [],
        }
        
        perm_file = Path(".harness/permissions.json")
        perm_file.parent.mkdir(parents=True, exist_ok=True)
        perm_file.write_text(json.dumps(permissions, indent=2))
        print(f"{GREEN}✓ Policy engine yapılandırıldı (.harness/permissions.json){RESET}")
    
    return enable_policy


def configure_cache():
    """Cache sistemi yapılandırması."""
    print(f"\n{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"{YELLOW}Cache Sistemi yapılandırması{RESET}")
    
    enable_cache = ask_yes_no("Cache sistemi aktif olsun mu? (60s TTL)", default=True)
    
    if enable_cache:
        cache_config = {
            "enabled": True,
            "ttl_seconds": 60,
            "max_entries": 100,
        }
        
        cache_file = Path(".harness/cache_config.json")
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(cache_config, indent=2))
        print(f"{GREEN}✓ Cache sistemi yapılandırıldı (.harness/cache_config.json){RESET}")
    
    return enable_cache


def create_env_file(state_path: str, policy: bool, cache: bool):
    """Environment dosyası oluştur."""
    env_content = f"""# OpenClaudeClaw Environment
OPENCLAUDECLAW_VERSION=1.0.0
STATE_DIR={state_path}
POLICY_ENGINE={'true' if policy else 'false'}
CACHE_ENABLED={'true' if cache else 'false'}
CACHE_TTL=60
LOG_LEVEL=INFO
"""
    
    env_file = Path(".openclaudeclaw.env")
    env_file.write_text(env_content)
    print(f"{GREEN}✓ Environment dosyası oluşturuldu (.openclaudeclaw.env){RESET}")


def install_packages(selected_packages: list):
    """Python paketlerini kur."""
    print(f"\n{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"{YELLOW}Python paketleri kuruluyor...{RESET}")
    
    import subprocess
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print(f"{GREEN}✓ Paketler başarıyla kuruldu{RESET}")
        else:
            print(f"{RED}✗ Paket kurulumu başarısız:{RESET}\n{result.stderr}")
    except Exception as e:
        print(f"{RED}✗ Hata: {e}{RESET}")


def copy_harness_structure():
    """Harness dizin yapısını kopyala."""
    print(f"\n{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"{YELLOW}Harness dizin yapısı oluşturuluyor...{RESET}")
    
    src_harness = Path("/home/ayzek/.openclaw/workspace/src/harness")
    dest_harness = Path("src/openclaudeclaw")
    
    if not src_harness.exists():
        print(f"{RED}✗ Kaynak harness dizini bulunamadı: {src_harness}{RESET}")
        return False
    
    # Dizinleri oluştur
    dest_harness.mkdir(parents=True, exist_ok=True)
    (dest_harness / "tools").mkdir(parents=True, exist_ok=True)
    
    # Python dosyalarını kopyala
    copied = 0
    for py_file in src_harness.glob("*.py"):
        dest_file = dest_harness / py_file.name
        dest_file.write_text(py_file.read_text())
        copied += 1
    
    for py_file in (src_harness / "tools").glob("*.py"):
        dest_file = dest_harness / "tools" / py_file.name
        dest_file.write_text(py_file.read_text())
        copied += 1
    
    print(f"{GREEN}✓ {copied} dosya kopyalandı{RESET}")
    return True


def print_summary(selected_packages: list, state_path: str, policy: bool, cache: bool):
    """Kurulum özeti."""
    print(f"""
{BLUE}╔══════════════════════════════════════════════════╗
║         Kurulum Tamamlandı!                     ║
╚══════════════════════════════════════════════════╝{RESET}

{GREEN}✓ Kurulan bileşenler:{RESET}
  • Seçilen paketler: {', '.join(selected_packages)}
  • State dizini: {state_path}
  • Policy Engine: {'Aktif' if policy else 'Pasif'}
  • Cache Sistemi: {'Aktif' if cache else 'Pasif'}

{YELLOW}Sonraki adımlar:{RESET}
  1. Environment dosyasını düzenleyin: .openclaudeclaw.env
  2. İlk çalıştırma: python3 -c "from openclaudeclaw import HarnessRuntime; r = HarnessRuntime()"
  3. Dokümantasyon: README.md

{GREEN}İyi kullanımlar! ☕{RESET}
""")


def main():
    print_header()
    
    # Seçimler
    selected_packages = select_tools()
    state_path = configure_state()
    policy = configure_policy()
    cache = configure_cache()
    
    # Kurulumlar
    install_packages(selected_packages)
    copy_harness_structure()
    create_env_file(state_path, policy, cache)
    
    # Özet
    print_summary(selected_packages, state_path, policy, cache)


if __name__ == "__main__":
    main()

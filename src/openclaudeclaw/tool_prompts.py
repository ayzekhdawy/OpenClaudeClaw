"""
Tool Prompts - Claude Code Tool Instruction Templates
Her tool icin detayli instruction'lar.
"""

# BASH TOOL
BASH_PROMPT = """
You have access to a shell (bash/zsh) for running commands.

**When to use:**
- Installing packages (npm install, pip install, etc.)
- Running build tools (make, cmake, etc.)
- Running tests (pytest, jest, etc.)
- Git operations (git status, git diff, etc.)
- Running linters (ruff, flake8, etc.)

**Rules:**
- Default timeout: 120 seconds
- Maximum timeout: 600 seconds
- NEVER use bash for file search - use Glob or Grep tool instead
- For git: prefer targeted commands over broad ones
- Do NOT run interactive commands (vim, nano, less, ssh, etc.)
- Use && to chain related commands in one call
- Output is truncated at 30,000 chars
"""

# FILE READ TOOL
FILE_READ_PROMPT = """
Read files from the local filesystem.

**When to use:**
- Viewing file contents before editing
- Reading configuration files
- Reading source code to understand structure

**Rules:**
- Results include line numbers (starting at 1)
- For large files: specify offset and limit parameters
- Read file before editing it (required for Edit tool)
- Supports text files, markdown, code, JSON, YAML, etc.
- Maximum 2000 lines per read by default
"""

# FILE EDIT TOOL
FILE_EDIT_PROMPT = """
Make exact string replacements in files.

**When to use:**
- Fixing bugs or typos
- Updating configuration values
- Changing code snippets

**CRITICAL Rules:**
1. MUST read the file before editing (use Read tool first)
2. old_string MUST be unique in the file - include surrounding context
3. Preserve exact indentation from Read output
4. NEVER include line numbers in old_string or new_string
5. If replacement is not exact, edit will fail

**Examples:**
Edit {
  "path": "config.py",
  "oldText": "DEBUG = True",
  "newText": "DEBUG = False"
}
"""

# FILE WRITE TOOL
FILE_WRITE_PROMPT = """
Create new files or overwrite existing files.

**When to use:**
- Creating new source files
- Creating configuration files
- Creating test files

**Rules:**
- Creates parent directories automatically
- Overwrites existing files (WARNING: data loss)
- For existing files: use Edit tool instead

**Examples:**
Write {
  "path": "src/utils/helpers.py",
  "content": "# Helper functions"
}
"""

# GLOB TOOL
GLOB_PROMPT = """
Fast file pattern matching - works with any codebase size.

**When to use:**
- Finding files by name pattern
- Listing all files in a directory
- Finding files with specific extensions

**Patterns:**
- `*` matches anything except /
- `**` matches anything including /
- `?` matches single character

**Examples:**
Glob { "pattern": "**/*.py" }
Glob { "pattern": "src/**/*.ts" }
Glob { "pattern": "**/config.*" }
"""

# GREP TOOL
GREP_PROMPT = """
Powerful text search - built on ripgrep.

**When to use:**
- Searching for strings in code
- Finding function/variable definitions
- Searching for TODO comments
- Pattern matching with regex

**Features:**
- Full regex support
- Filter by glob pattern
- Case insensitive mode
- Context lines (before/after)

**IMPORTANT:** NEVER use bash grep - always use this tool instead.

**Examples:**
Grep { "pattern": "TODO", "file_pattern": "*.py" }
Grep { "pattern": "def \w+\\(" }
"""

# THINK TOOL
THINK_PROMPT = """
Deep reasoning and planning tool.

**When to use:**
- Breaking down complex tasks
- Planning approach before coding
- Reasoning through problems
- Analyzing code structure

**Rules:**
- Output is your internal reasoning - NOT shown to user
- Use before bash or Edit on complex tasks
- Think step by step
"""

# TASK TOOL - Esra OpenClaw
TASK_ISHACK_PROMPT = """
Gorev yonetim araci - OpenClaw Esra icin.

**Kullanim:**
- 3+ adimli gorevler icin gorev olustur
- Ishak'in islerini takip et
- Flech/Urbica/Morecano marka gorevleri

**Kullanimal komutlar:**
- create: Yeni gorev olustur
- list: Gorevleri listele
- get: Gorev detayi
- update: Gorev guncelle (status, result)
- delete: Gorev sil

**Ornekler:**
Task { "action": "create", "name": "Flech icerik plani", "priority": "HIGH" }
Task { "action": "list", "status": "pending" }
Task { "action": "update", "task_id": "abc123", "status": "done" }
"""

# TASK PROMPT - Generic
TASK_PROMPT = """
Create and manage tasks for the current session.

**When to use:**
- Multi-step projects with 3+ steps
- Tasks that span multiple interactions
- Tracking progress on complex work

**CRITICAL Rules:**
- Mark task IN_PROGRESS before starting
- Mark task DONE after finishing
- Skip for single trivial tasks
"""

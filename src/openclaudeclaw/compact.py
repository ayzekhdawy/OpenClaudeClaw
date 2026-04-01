"""
Compact — Context Compaction Service
──────────────────────────────────
Claude Code compact/prompt.ts port.

Context 80%+ dolduğunda konuşmayı 9 başlıkla özetler:
1. Primary Request and Intent
2. Key Technical Concepts
3. Files and Code Sections
4. Errors and Fixes
5. Problem Solving
6. All User Messages
7. Pending Tasks
8. Current Work
9. Optional Next Step

<analysis> bloğunu atlar, <summary> bloğunu temizler.
"""

from __future__ import annotations

from typing import Optional


# NO_TOOLS_PREAMBLE — agent'a tool çağırmayı yasakla
NO_TOOLS_PREAMBLE = """CRITICAL: Respond with TEXT ONLY. Do NOT call any tools.

- Do NOT use Read, Bash, Grep, Glob, Edit, Write, or ANY other tool.
- You already have all the context you need in the conversation above.
- Tool calls will be REJECTED and will waste your only turn — you will fail the task.
- Your entire response must be plain text: an <analysis> block followed by a <summary> block.

"""


DETAILED_ANALYSIS_INSTRUCTION = """Before providing your final summary, wrap your analysis in <analysis> tags to organize your thoughts and ensure you've covered all necessary points. In your analysis process:

1. Chronologically analyze each message and section of the conversation. For each section thoroughly identify:
   - The user's explicit requests and intents
   - Your approach to addressing the user's requests
   - Key decisions, technical concepts and code patterns
   - Specific details like:
     - file names
     - full code snippets
     - function signatures
     - file edits
   - Errors that you ran into and how you fixed them
   - Pay special attention to specific user feedback that you received, especially if the user told you to do something differently.
2. Double-check for technical accuracy and completeness, addressing each required element thoroughly."""


BASE_COMPACT_PROMPT = f"""Your task is to create a detailed summary of the conversation so far, paying close attention to the user's explicit requests and your previous actions.
This summary should be thorough in capturing technical details, code patterns, and architectural decisions that would be essential for continuing development work without losing context.

{DETAILED_ANALYSIS_INSTRUCTION}

Your summary should include the following sections:

1. Primary Request and Intent: Capture all of the user's explicit requests and intents in detail
2. Key Technical Concepts: List all important technical concepts, technologies, and frameworks discussed.
3. Files and Code Sections: Enumerate specific files and code sections examined, modified, or created. Pay special attention to the most recent messages and include full code snippets where applicable and include a summary of why this file read or edit is important.
4. Errors and fixes: List all errors that you ran into, and how you fixed them. Pay special attention to specific user feedback that you received, especially if the user told you to do something differently.
5. Problem Solving: Document problems solved and any ongoing troubleshooting efforts.
6. All user messages: List ALL user messages that are not tool results. These are critical for understanding the users' feedback and changing intent.
7. Pending Tasks: Outline any pending tasks that you have explicitly been asked to work on.
8. Current Work: Describe in detail precisely what was being worked on immediately before this summary request, paying special attention to the most recent messages from both user and assistant. Include file names and code snippets where applicable.
9. Optional Next Step: List the next step that you will take that is related to the most recent work you were doing. IMPORTANT: ensure that this step is DIRECTLY in line with the user's most recent explicit requests, and the task you were working on immediately before this summary request. If your last task was concluded, then only list next steps if they are explicitly in line with the users request. Do not start on tangential requests or really old requests that were already completed without confirming with the user first.
   If there is a next step, include direct quotes from the most recent conversation showing exactly what task you were working on and where you left off. This should be verbatim to ensure there's no drift in task interpretation.

Here's an example of how your output should be structured:

<example>
<analysis>
[Your thought process, ensuring all points are covered thoroughly and accurately]
</analysis>

<summary>
1. Primary Request and Intent:
   [Detailed description]

2. Key Technical Concepts:
   - [Concept 1]
   - [Concept 2]
   - [...]

3. Files and Code Sections:
   - [File Name 1]
      - [Summary of why this file is important]
      - [Summary of the changes made to this file, if any]
      - [Important Code Snippet]
   - [File Name 2]
      - [Important Code Snippet]
   - [...]

4. Errors and fixes:
    - [Detailed description of error 1]:
      - [How you fixed the error]
      - [User feedback on the error if any]
    - [...]

5. Problem Solving:
   [Description of solved problems and ongoing troubleshooting]

6. All user messages: 
    - [Detailed non tool use user message]
    - [...]

7. Pending Tasks:
   - [Task 1]
   - [Task 2]
   - [...]

8. Current Work:
   [Precise description of current work]

9. Optional Next Step:
   [Optional Next step to take]

</summary>
</example>

Please provide your summary based on the conversation so far, following this structure and ensuring precision and thoroughness in your response. 

There may be additional summarization instructions provided in the included context. If so, remember to follow these instructions when creating the above summary."""


NO_TOOLS_TRAILER = """

REMINDER: Do NOT call any tools. Respond with plain text only — an <analysis> block followed by a <summary> block. Tool calls will be rejected and you will fail the task."""


def get_compact_prompt(custom_instructions: Optional[str] = None) -> str:
    """
    Base compact prompt oluştur.
    
    Claude Code getCompactPrompt port.
    
    Args:
        custom_instructions: Ek summarization talimatları
    
    Returns:
        str: Compact prompt (NO_TOOLS preamble + template + trailer)
    """
    prompt = NO_TOOLS_PREAMBLE + BASE_COMPACT_PROMPT
    
    if custom_instructions and custom_instructions.strip():
        prompt += f"\n\nAdditional Instructions:\n{custom_instructions}"
    
    prompt += NO_TOOLS_TRAILER
    
    return prompt


def get_partial_compact_prompt(
    custom_instructions: Optional[str] = None,
    direction: str = "from",
) -> str:
    """
    Partial compact prompt (sadece recent mesajları özetle).
    
    Claude Code getPartialCompactPrompt port.
    
    Args:
        custom_instructions: Ek talimatlar
        direction: 'from' = recent özetle, 'up_to' = prefix özetle
    
    Returns:
        str: Partial compact prompt
    """
    if direction == "up_to":
        template = PARTIAL_COMPACT_UP_TO_PROMPT
    else:
        template = PARTIAL_COMPACT_PROMPT
    
    prompt = NO_TOOLS_PREAMBLE + template
    
    if custom_instructions and custom_instructions.strip():
        prompt += f"\n\nAdditional Instructions:\n{custom_instructions}"
    
    prompt += NO_TOOLS_TRAILER
    
    return prompt


PARTIAL_COMPACT_PROMPT = f"""Your task is to create a detailed summary of the RECENT portion of the conversation — the messages that follow earlier retained context. The earlier messages are being kept intact and do NOT need to be summarized. Focus your summary on what was discussed, learned, and accomplished in the recent messages only.

{DETAILED_ANALYSIS_INSTRUCTION}

Your summary should include the following sections:

1. Primary Request and Intent: Capture the user's explicit requests and intents from the recent messages
2. Key Technical Concepts: List important technical concepts, technologies, and frameworks discussed recently.
3. Files and Code Sections: Enumerate specific files and code sections examined, modified, or created. Include full code snippets where applicable.
4. Errors and fixes: List errors encountered and how they were fixed.
5. Problem Solving: Document problems solved and any ongoing troubleshooting efforts.
6. All user messages: List ALL user messages from the recent portion that are not tool results.
7. Pending Tasks: Outline any pending tasks from the recent messages.
8. Current Work: Describe precisely what was being worked on immediately before this summary request.
9. Optional Next Step: List the next step related to the most recent work. Include direct quotes.

<example>
<analysis>
[Your analysis]
</analysis>

<summary>
1. Primary Request and Intent:
   [Description]

2. Key Technical Concepts:
   - [Concept 1]

3. Files and Code Sections:
   - [File Name]: [Summary]

4. Errors and fixes:
   - [Error]: [Fix]

5. Problem Solving:
   [Description]

6. All user messages:
   - [Message]

7. Pending Tasks:
   - [Task]

8. Current Work:
   [Description]

9. Optional Next Step:
   [Step]
</summary>
</example>"""


PARTIAL_COMPACT_UP_TO_PROMPT = f"""Your task is to create a detailed summary of this conversation. This summary will be placed at the start of a continuing session; newer messages that build on this context will follow after your summary. Summarize thoroughly so that someone reading only your summary and then the newer messages can fully understand what happened.

{DETAILED_ANALYSIS_INSTRUCTION}

Your summary should include the following sections:

1. Primary Request and Intent: Capture the user's explicit requests and intents in detail
2. Key Technical Concepts: List important technical concepts
3. Files and Code Sections: Files examined, modified, or created
4. Errors and fixes: Errors encountered and fixes
5. Problem Solving: Problems solved
6. All user messages: ALL non-tool user messages
7. Pending Tasks: Pending tasks
8. Work Completed: What was accomplished by end of this portion
9. Context for Continuing Work: Key context needed to continue

<example>
<analysis>
[Your analysis]
</analysis>

<summary>
1. Primary Request and Intent:
   [Description]

2. Key Technical Concepts:
   - [Concept]

3. Files and Code Sections:
   - [File]: [Summary]

4. Errors and fixes:
   - [Error]: [Fix]

5. Problem Solving:
   [Description]

6. All user messages:
   - [Message]

7. Pending Tasks:
   - [Task]

8. Work Completed:
   [Description]

9. Context for Continuing Work:
   [Key context]
</summary>
</example>"""


def format_compact_summary(summary: str) -> str:
    """
    Compact özetini formatla.
    
    Claude Code formatCompactSummary port.
    
    - <analysis> bloğunu atlar (drafting scratchpad)
    - <summary> bloğunu temizler, section headers ekler
    
    Args:
        summary: Raw summary string (<analysis> ve <summary> tag'ları içerebilir)
    
    Returns:
        str: Temizlenmiş summary
    """
    formatted = summary
    
    # Strip <analysis> section
    formatted = _strip_analysis(formatted)
    
    # Extract and format <summary> section
    formatted = _format_summary_section(formatted)
    
    # Clean up extra whitespace
    formatted = _clean_whitespace(formatted)
    
    return formatted.strip()


def _strip_analysis(text: str) -> str:
    """<analysis> bloğunu atla."""
    # Match <analysis>...</analysis> (case insensitive, dotall)
    import re
    pattern = r'<analysis>[\s\S]*?</analysis>'
    return re.sub(pattern, '', text, flags=re.IGNORECASE)


def _format_summary_section(text: str) -> str:
    """<summary> bloğunu section headers ile değiştir."""
    import re
    
    # Match <summary>...</summary>
    match = re.search(r'<summary>([\s\S]*?)</summary>', text, re.IGNORECASE)
    if match:
        content = match.group(1) or ''
        # Replace the whole <summary>...</summary> with formatted version
        formatted_content = content.strip()
        replacement = f"Summary:\n{formatted_content}"
        text = re.sub(r'<summary>[\s\S]*?</summary>', replacement, text, flags=re.IGNORECASE)
    
    return text


def _clean_whitespace(text: str) -> str:
    """Fazla whitespace temizle."""
    import re
    # 3+ newline -> 2 newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Trailin/leading whitespace
    text = text.strip()
    return text


def get_compact_user_summary_message(
    summary: str,
    suppress_follow_up: bool = False,
    transcript_path: Optional[str] = None,
    recent_messages_preserved: bool = True,
) -> str:
    """
    Compact sonrası user'a gösterilecek mesaj oluştur.
    
    Claude Code getCompactUserSummaryMessage port.
    
    Args:
        summary: format_compact_summary'dan gelen temiz özet
        suppress_follow_up: Soru sorma, devam et
        transcript_path: Detaylar için transcript yolu
        recent_messages_preserved: Recent mesajlar korundu mu
    
    Returns:
        str: User mesajı
    """
    formatted = format_compact_summary(summary)
    
    base = f"""This session is being continued from a previous conversation that ran out of context. The summary below covers the earlier portion of the conversation.

{formatted}"""
    
    if transcript_path:
        base += f"\n\nIf you need specific details from before compaction (like exact code snippets, error messages, or content you generated), read the full transcript at: {transcript_path}"
    
    if recent_messages_preserved:
        base += "\n\nRecent messages are preserved verbatim."
    
    if suppress_follow_up:
        continuation = f"""{base}

Continue the conversation from where it left off without asking the user any further questions. Resume directly — do not acknowledge the summary, do not recap what was happening, do not preface with "I'll continue" or similar. Pick up the last task as if the break never happened."""
        return continuation
    
    return base


# Token threshold constants
COMPACT_THRESHOLD_TOKENS = 200000  # 200k+ tokens -> compact
COMPACT_WARNING_TOKENS = 160000    # 160k+ tokens -> warning


def should_compact(token_count: int) -> bool:
    """
    Compact gerekli mi kontrol et.
    
    Args:
        token_count: Mevcut token sayısı
    
    Returns:
        bool: True = compact et
    """
    return token_count >= COMPACT_THRESHOLD_TOKENS


def get_token_warning_level(token_count: int) -> str:
    """
    Token durumuna göre warning level döndür.
    
    Args:
        token_count: Mevcut token sayısı
    
    Returns:
        str: 'ok', 'warning', 'critical'
    """
    if token_count >= COMPACT_THRESHOLD_TOKENS:
        return "critical"
    elif token_count >= COMPACT_WARNING_TOKENS:
        return "warning"
    return "ok"


if __name__ == "__main__":
    print("=== Compact Module Test ===\n")
    
    # Test get_compact_prompt
    cp = get_compact_prompt()
    print(f"Compact prompt: {len(cp)} chars")
    print(f"Preview:\n{cp[:300]}...")
    
    print("\n--- Partial Compact ---")
    pcp = get_partial_compact_prompt()
    print(f"Partial compact prompt: {len(pcp)} chars")
    
    # Test format_compact_summary
    print("\n--- Format Summary ---")
    raw = """
<analysis>
This is my analysis of the conversation.
I looked at everything carefully.
</analysis>

<summary>
1. Primary Request and Intent:
   User asked to create a memory extraction module.

2. Key Technical Concepts:
   - Memory types (user, feedback, project, reference)
   - Frontmatter format
   - Duplicate prevention

3. Files and Code Sections:
   - extract_memories.py: Main module for memory extraction

4. Errors and fixes:
   - None so far

5. Pending Tasks:
   - Test the module

6. Current Work:
   Creating compact.py

7. Optional Next Step:
   Integrate with runtime.py
</summary>
"""
    
    formatted = format_compact_summary(raw)
    print(f"Formatted:\n{formatted}")
    
    # Test token thresholds
    print("\n--- Token Thresholds ---")
    print(f"Warning at: {COMPACT_WARNING_TOKENS:,} tokens")
    print(f"Critical at: {COMPACT_THRESHOLD_TOKENS:,} tokens")
    
    for count in [50000, 64000, 80000]:
        level = get_token_warning_level(count)
        should = should_compact(count)
        print(f"  {count:,} tokens: {level} | compact={should}")

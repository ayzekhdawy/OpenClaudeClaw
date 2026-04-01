"""
BriefTool — User Message Delivery
──────────────────────────────────────────────────────────
Claude Code BriefTool referansı — tam özellikler.

Ana mesaj kanalı: Agent → User mesaj gönderir.
Attachments, proactive status, markdown desteği.
"""

import time
import os
import uuid
import subprocess
from pathlib import Path
from typing import Optional

from ..models import BaseTool, ToolResult, ToolCategory


class BriefTool(BaseTool):
    """
    Send message to user - Claude Code pattern.

    Bu agent'ın ana output channel'ı.
    Tüm mesajlar bu tool üzerinden gider.

    Features:
    - Markdown formatting
    - File attachments (images, docs, logs, diffs)
    - Proactive status (user beklemiyorken gönderilen)
    - Sent timestamp

    Patterns: mesaj gönder, mesaj yaz, tell user, bildirim
    """
    name = "Brief"
    category = ToolCategory.UTILITY
    patterns = ["mesaj", "bildirim", "haber ver", "tell user", "send message", "yaz"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()

        message = input_data.get("message", "")
        attachments = input_data.get("attachments", [])
        status = input_data.get("status", "normal")  # normal | proactive

        if not message and not attachments:
            return ToolResult(
                self.name, False, "",
                "message or attachments required",
                int((time.time()-start)*1000)
            )

        # Resolve attachments
        resolved = []
        for att in attachments:
            path = Path(att)
            if path.exists() and path.is_file():
                stat = path.stat()
                is_image = path.suffix.lower() in [".png", ".jpg", ".jpeg", ".gif", ".webp"]
                resolved.append({
                    "path": str(path),
                    "size": stat.st_size,
                    "isImage": is_image,
                    "file_uuid": str(uuid.uuid4())[:8]
                })

        # Format output
        sent_at = time.strftime("%Y-%m-%d %H:%M:%S")
        output = f"{message}"

        if resolved:
            att_list = []
            for r in resolved:
                size_kb = r["size"] // 1024
                att_list.append(f"  📎 {r['path']} ({size_kb}KB)")
            output += "\n\nAttachments:\n" + "\n".join(att_list)

        output += f"\n\n[Sent: {sent_at}]"
        if status == "proactive":
            output = "📬 " + output

        return ToolResult(
            self.name, True, output,
            int((time.time()-start)*1000),
            metadata={
                "sent_at": sent_at,
                "attachment_count": len(resolved),
                "status": status
            }
        )

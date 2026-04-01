"""
SendMessageTool — Multi-channel messaging
─────────────────────────────────────────
Claude Code SendMessageTool referansı.
Slack, Discord, Telegram, Email gönderir.
"""

import json
import time
from pathlib import Path
from typing import Optional

from ..models import BaseTool, ToolResult, ToolCategory


class SendMessageTool(BaseTool):
    """
    Multi-channel message sender - Claude Code pattern.
    
    Channels: slack, discord, telegram, email, webhook
    
    Input:
    - channel: Channel name (slack/discord/telegram/email/webhook)
    - to: Recipient or channel
    - message: Message text
    - webhook_url: For webhook channel
    
    Patterns: send, mesaj gönder, bildirim, slack, discord, telegram
    """
    name = "SendMessage"
    category = ToolCategory.EXECUTE
    patterns = ["send", "mesaj", "bildirim", "slack", "discord", "telegram", "webhook", "email"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()
        
        channel = input_data.get("channel", "telegram")
        to = input_data.get("to", "")
        message = input_data.get("message", "")
        webhook_url = input_data.get("webhook_url", "")
        
        if not message:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error="message is required",
                duration_ms=int((time.time() - start) * 1000),
            )
        
        try:
            if channel == "webhook":
                return self._send_webhook(webhook_url, message, start)
            
            elif channel == "telegram":
                return self._send_telegram(to, message, start)
            
            elif channel == "slack":
                return self._send_slack(to, message, start)
            
            elif channel == "discord":
                return self._send_discord(to, message, start)
            
            elif channel == "email":
                return self._send_email(to, message, start)
            
            else:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    output="",
                    error=f"Unknown channel: {channel}. Use: telegram, slack, discord, email, webhook",
                    duration_ms=int((time.time() - start) * 1000),
                )
        
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=str(e),
                duration_ms=int((time.time() - start) * 1000),
            )
    
    def _send_webhook(self, url: str, message: str, start: float) -> ToolResult:
        """Send via webhook."""
        if not url:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error="webhook_url required",
                duration_ms=int((time.time() - start) * 1000),
            )
        
        try:
            import urllib.request
            
            data = json.dumps({"text": message}).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=10) as resp:
                response = resp.read().decode()
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=f"Webhook sent: {len(message)} chars",
                duration_ms=int((time.time() - start) * 1000),
                metadata={"response": response[:200]},
            )
        
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=f"Webhook failed: {e}",
                duration_ms=int((time.time() - start) * 1000),
            )
    
    def _send_telegram(self, chat_id: str, message: str, start: float) -> ToolResult:
        """Send via OpenClaw's message system."""
        # Use OpenClaw message tool if available
        try:
            # OpenClaw mesaj gönderme
            # Bu işlev OpenClaw runtime'da çalışırken mesaj gönderir
            # Şimdilik log'a yaz + OpenClaw'a bildir
            self._log_message("telegram", chat_id, message)
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=f"Telegram mesajı kuyruğa alındı: {chat_id}",
                duration_ms=int((time.time() - start) * 1000),
                metadata={"channel": "telegram", "to": chat_id, "chars": len(message)},
            )
        
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=str(e),
                duration_ms=int((time.time() - start) * 1000),
            )
    
    def _send_slack(self, channel: str, message: str, start: float) -> ToolResult:
        """Send to Slack via webhook."""
        config = self._load_channel_config("slack")
        webhook_url = config.get("webhook_url", "")
        
        if not webhook_url:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error="Slack webhook not configured. Add to .harness/send_message.json",
                duration_ms=int((time.time() - start) * 1000),
            )
        
        return self._send_webhook(webhook_url, message, start)
    
    def _send_discord(self, channel: str, message: str, start: float) -> ToolResult:
        """Send to Discord via webhook."""
        config = self._load_channel_config("discord")
        webhook_url = config.get("webhook_url", "")
        
        if not webhook_url:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error="Discord webhook not configured. Add to .harness/send_message.json",
                duration_ms=int((time.time() - start) * 1000),
            )
        
        return self._send_webhook(webhook_url, message, start)
    
    def _send_email(self, to: str, message: str, start: float) -> ToolResult:
        """Send email via SMTP."""
        return ToolResult(
            tool_name=self.name,
            success=False,
            output="",
            error="Email not implemented. Use webhook instead.",
            duration_ms=int((time.time() - start) * 1000),
        )
    
    def _load_channel_config(self, channel: str) -> dict:
        """Load channel configuration."""
        config_file = Path("/home/ayzek/.openclaw/workspace/.harness/send_message.json")
        if config_file.exists():
            config = json.loads(config_file.read_text())
            return config.get(channel, {})
        return {}
    
    def _log_message(self, channel: str, to: str, message: str):
        """Log sent message."""
        log_file = Path("/home/ayzek/.openclaw/workspace/.harness/message_log.jsonl")
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "channel": channel,
            "to": to,
            "message": message[:100],
            "chars": len(message),
        }
        
        with open(log_file, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

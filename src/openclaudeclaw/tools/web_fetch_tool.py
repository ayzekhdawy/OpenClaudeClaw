"""
WebFetchTool — Web page content fetcher
────────────────────────────────────────
Claude Code WebFetchTool referansı.
URL'den içerik çeker, markdown/text döndürür.
"""

import urllib.request
import urllib.error
import html
import re
import time

from ..models import BaseTool, ToolResult, ToolCategory


class WebFetchTool(BaseTool):
    """
    Web page fetcher - Claude Code pattern.
    
    Input:
    - url: URL to fetch
    - max_chars: Max characters (default 5000)
    
    Patterns: fetch, web page, url content, internet
    """
    name = "WebFetch"
    category = ToolCategory.READ
    patterns = ["fetch", "web", "url", "internet", "çek", "sayfa"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        url = input_data.get("url", "")
        max_chars = input_data.get("max_chars", 5000)
        mode = input_data.get("mode", "text")  # text or markdown
        
        if not url:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error="url is required",
                duration_ms=0,
            )
        
        start = time.time()
        
        try:
            # Basic URL validation
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            
            # Fetch page
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; Esra/1.0)",
                    "Accept": "text/html,application/xhtml+xml",
                }
            )
            
            with urllib.request.urlopen(req, timeout=15) as response:
                content = response.read().decode("utf-8", errors="replace")
            
            # Extract text
            if mode == "markdown":
                text = self._to_markdown(content, url)
            else:
                text = self._extract_text(content)
            
            # Truncate
            if len(text) > max_chars:
                text = text[:max_chars] + f"\n\n[... {len(text) - max_chars} chars truncated]"
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=text,
                duration_ms=int((time.time() - start) * 1000),
                metadata={"url": url, "mode": mode},
            )
        
        except urllib.error.HTTPError as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=f"HTTP {e.code}: {e.reason}",
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
    
    def _extract_text(self, html_content: str) -> str:
        """Extract plain text from HTML."""
        # Remove scripts and styles
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', html_content)
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Clean whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _to_markdown(self, html_content: str, url: str) -> str:
        """Convert HTML to simple markdown."""
        # Remove scripts and styles
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
        
        # Headers
        html_content = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1\n', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1\n', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1\n', html_content, flags=re.DOTALL)
        
        # Links
        html_content = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', html_content, flags=re.DOTALL)
        
        # Bold/italic
        html_content = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', html_content, flags=re.DOTALL)
        
        # Paragraphs
        html_content = re.sub(r'<p[^>]*>', '\n\n', html_content)
        html_content = re.sub(r'</p>', '', html_content)
        
        # Lists
        html_content = re.sub(r'<li[^>]*>(.*?)</li>', r'\n- \1', html_content, flags=re.DOTALL)
        
        # Remove remaining tags
        html_content = re.sub(r'<[^>]+>', '', html_content)
        
        # Decode entities
        html_content = html.unescape(html_content)
        
        # Clean whitespace
        html_content = re.sub(r'\n{3,}', '\n\n', html_content)
        html_content = re.sub(r' +\n', '\n', html_content)
        
        return html_content.strip()

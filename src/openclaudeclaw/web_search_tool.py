"""
WebSearchTool — Claude Code inspired web search
────────────────────────────────────────────────────────
Cleans-room implementation of Claude Code's WebSearchTool.
Uses Brave Search API for web search functionality.
"""

import subprocess
import json
import re
import time
import os
from typing import Optional

from .models import ToolResult, ToolCategory, ToolSpec, BaseTool


class WebSearchTool(BaseTool):
    """
    Web search tool - uses Brave Search API or fallback.
    
    Claude Code pattern:
    - Input: query, optional allowed_domains, blocked_domains
    - Output: query, results[], durationSeconds
    """
    
    name = "WebSearch"
    category = ToolCategory.SEARCH
    patterns = [
        "search", "web search", "ara", "internet", "search web",
        "google", "web", "web'de ara"
    ]
    
    def execute(self, input_data: dict, context: dict = None) -> ToolResult:
        """
        Execute web search.
        
        Input:
        - query: Search query (required)
        - allowed_domains: List of domains to restrict (optional)
        - blocked_domains: List of domains to exclude (optional)
        """
        query = input_data.get("query", "")
        allowed_domains = input_data.get("allowed_domains")
        blocked_domains = input_data.get("blocked_domains")
        
        if len(query) < 2:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error="Query must be at least 2 characters"
            )
        
        start_time = time.time()
        
        # Get Brave Search API key
        api_key = os.environ.get('BRAVE_SEARCH_API_KEY')
        
        if api_key:
            result = self._search_brave(query, allowed_domains, blocked_domains, api_key)
        else:
            result = self._search_fallback(query)
        
        duration = time.time() - start_time
        
        if result["success"]:
            result["durationSeconds"] = round(duration, 2)
        
        return ToolResult(
            tool_name=self.name,
            success=result.get("success", False),
            output=json.dumps(result, indent=2),
            error=result.get("error")
        )
    
    def _search_brave(self, query: str, allowed: list, blocked: list, api_key: str) -> dict:
        """Search using Brave Search API."""
        params = [f"q={query}"]
        
        # Brave API doesn't support domain filtering in free tier
        url = f"https://api.search.brave.com/res/v1/web/search?{'&'.join(params)}"
        
        try:
            proc = subprocess.run(
                ["curl", "-s", "-L", "--max-time", "20",
                 "-H", f"X-Subscription-Token: {api_key}",
                 "-H", "Accept: application/json",
                 url],
                capture_output=True,
                text=True,
                timeout=25
            )
            
            if proc.returncode != 0:
                return {"success": False, "error": proc.stderr}
            
            data = json.loads(proc.stdout)
            results = []
            
            web_results = data.get("web", {}).get("results", [])
            for item in web_results[:10]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", "")
                })
            
            return {
                "success": True,
                "query": query,
                "results": results
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _search_fallback(self, query: str) -> dict:
        """Fallback search using DuckDuckGo HTML."""
        url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        
        try:
            proc = subprocess.run(
                ["curl", "-s", "-L", "--max-time", "15", url],
                capture_output=True,
                text=True,
                timeout=20
            )
            
            if proc.returncode != 0:
                return {"success": False, "error": proc.stderr}
            
            results = []
            pattern = r'<a class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, proc.stdout)
            
            for url, title in matches[:10]:
                clean_title = re.sub(r'<[^>]+>', '', title).strip()
                results.append({"title": clean_title, "url": url})
            
            return {
                "success": True,
                "query": query,
                "results": results
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

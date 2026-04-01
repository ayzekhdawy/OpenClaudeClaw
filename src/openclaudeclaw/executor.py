"""
Unified Executor — execution abstraction with auth, structured results, error recovery.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Optional

from .auth_manager import get_auth_manager
from .event_bus import get_event_bus
from .providers import ProviderRegistry, ProviderTarget, get_provider_registry
from .result_models import ExecutorResult
from .session_cleanup import get_cost_tracker, CostEntry


@dataclass
class ExecutionRequest:
    session_id: str
    task: str
    target: str
    prompt: str
    fallback_target: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class ProviderExecutionError(RuntimeError):
    pass


# Backward compat alias — ExecutionResult lives in result_models.py
ExecutionResult = ExecutorResult


class UnifiedExecutor:
    def __init__(self, registry: Optional[ProviderRegistry] = None):
        self.registry = registry or get_provider_registry()
        self.events = get_event_bus()
        self.auth = get_auth_manager()
        self.cost = get_cost_tracker()

    def execute(self, request: ExecutionRequest) -> ExecutorResult:
        start = time.time()
        attempts: list[dict] = []
        chain = self.registry.get_fallback_chain(request.target, request.fallback_target)

        last_error = None
        for idx, target_key in enumerate(chain):
            target = self.registry.get_target(target_key)
            try:
                self.events.publish(
                    "executor.attempt",
                    session_id=request.session_id,
                    source="executor",
                    payload={"target": target_key, "provider": target.provider, "backend": target.backend},
                )
                output, tokens_used = self._execute_target(target, request)
                duration_ms = int((time.time() - start) * 1000)
                cost = self.cost.calculate_cost(target.model, tokens_used or 0, len(output) // 4)

                # Log cost
                try:
                    self.cost.log_cost(CostEntry(
                        session_id=request.session_id,
                        model=target.model,
                        provider=target.provider,
                        input_tokens=tokens_used or 0,
                        output_tokens=len(output) // 4,
                        duration_ms=duration_ms,
                        cost=cost,
                    ))
                except Exception:
                    pass

                result = ExecutorResult(
                    ok=True,
                    session_id=request.session_id,
                    requested_target=request.target,
                    executor_target=target.key,
                    provider=target.provider,
                    model=target.model,
                    backend=target.backend,
                    output=output,
                    duration_ms=duration_ms,
                    tokens_used=tokens_used,
                    cost_estimate=cost,
                    fallback_used=idx > 0,
                    attempts=attempts + [{"target": target.key, "ok": True}],
                    metadata=request.metadata,
                )
                self.events.publish(
                    "executor.completed",
                    session_id=request.session_id,
                    source="executor",
                    payload=result.to_dict(),
                )
                return result
            except Exception as exc:
                last_error = str(exc)
                attempts.append({"target": target.key, "ok": False, "error": last_error})
                self.events.publish(
                    "executor.failed",
                    session_id=request.session_id,
                    source="executor",
                    payload={"target": target.key, "error": last_error},
                )

        duration_ms = int((time.time() - start) * 1000)
        return ExecutorResult(
            ok=False,
            session_id=request.session_id,
            requested_target=request.target,
            executor_target=chain[-1],
            provider=self.registry.get_target(chain[-1]).provider,
            model=self.registry.get_target(chain[-1]).model,
            backend=self.registry.get_target(chain[-1]).backend,
            output="",
            error=last_error or "execution failed",
            duration_ms=duration_ms,
            fallback_used=len(chain) > 1,
            attempts=attempts,
            metadata=request.metadata,
        )

    def _execute_target(self, target: ProviderTarget, request: ExecutionRequest) -> tuple[str, Optional[int]]:
        if target.backend == "local-http":
            return self._execute_ollama_http(target, request.prompt)
        if target.backend == "native-runtime":
            return self._execute_claude_cli(target, request.prompt)
        if target.backend == "cloud-api":
            return self._execute_openai_compatible_http(target, request.prompt)
        if target.backend == "command":
            return self._execute_command(target, request.prompt)
        raise ProviderExecutionError(f"Unsupported backend: {target.backend}")

    def _execute_ollama_http(self, target: ProviderTarget, prompt: str) -> tuple[str, Optional[int]]:
        url = target.endpoint.rstrip("/") + "/api/generate"
        payload = json.dumps({"model": target.model, "prompt": prompt, "stream": False}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        # Inject auth headers if configured
        auth_headers = self.auth.resolve_auth_headers(target.provider)
        headers.update(auth_headers)
        req = urllib.request.Request(url, data=payload, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise ProviderExecutionError(f"local-http unavailable: {exc}") from exc
        response = data.get("response") or data.get("message", {}).get("content")
        if not response:
            raise ProviderExecutionError("local-http returned no response")
        tokens = data.get("eval_count") or data.get("prompt_eval_count")
        return response, int(tokens) if tokens else None

    def _execute_openai_compatible_http(self, target: ProviderTarget, prompt: str) -> tuple[str, Optional[int]]:
        endpoint = target.endpoint.rstrip("/")
        if endpoint.endswith("/chat/completions"):
            url = endpoint
        else:
            url = endpoint + "/api/chat"
        payload = json.dumps({"model": target.model, "messages": [{"role": "user", "content": prompt}], "stream": False}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        auth_headers = self.auth.resolve_auth_headers(target.provider)
        headers.update(auth_headers)
        req = urllib.request.Request(url, data=payload, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise ProviderExecutionError(f"cloud-api unavailable: {exc}") from exc
        if isinstance(data.get("message"), dict):
            content = data["message"].get("content")
        else:
            choices = data.get("choices") or []
            content = choices[0].get("message", {}).get("content") if choices else None
        usage = data.get("usage", {})
        tokens = usage.get("total_tokens")
        if not content:
            raise ProviderExecutionError("cloud-api returned no content")
        return content, int(tokens) if tokens else None

    def _execute_claude_cli(self, target: ProviderTarget, prompt: str) -> tuple[str, Optional[int]]:
        if not shutil.which("claude"):
            raise ProviderExecutionError("claude CLI not installed")
        cmd = ["claude", "--permission-mode", "bypassPermissions", "--print", prompt]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if proc.returncode != 0:
            raise ProviderExecutionError(proc.stderr.strip() or "claude runtime failed")
        output = proc.stdout.strip()
        if not output:
            raise ProviderExecutionError("claude runtime returned empty output")
        return output, None

    def _execute_command(self, target: ProviderTarget, prompt: str) -> tuple[str, Optional[int]]:
        raw = self.registry.config.get("defaults", {}).get(target.key, {})
        template = raw.get("command_template")
        if not template:
            raise ProviderExecutionError("command backend missing command_template")
        command = template.replace("{prompt}", json.dumps(prompt))
        proc = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        if proc.returncode != 0:
            raise ProviderExecutionError(proc.stderr.strip() or "command backend failed")
        output = proc.stdout.strip()
        if not output:
            raise ProviderExecutionError("command backend returned empty output")
        return output, None


_EXECUTOR: Optional[UnifiedExecutor] = None


def get_unified_executor() -> UnifiedExecutor:
    global _EXECUTOR
    if _EXECUTOR is None:
        _EXECUTOR = UnifiedExecutor()
    return _EXECUTOR

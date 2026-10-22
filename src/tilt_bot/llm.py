"""Small, provider-agnostic clients for supported LLM APIs."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any, Protocol
from urllib import error, request


class LLMError(RuntimeError):
    """Raised when an LLM request cannot be completed or parsed."""


class LLMClient(Protocol):
    """Interface used by future filtering, scoring, and resume workflows."""

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> str:
        """Generate text for a prompt."""


@dataclass(frozen=True)
class LLMConfig:
    """Connection and generation defaults loaded from environment variables."""

    api_key: str
    provider: str = "openai"
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    timeout_seconds: float = 60.0
    cli_path: str = "claude"

    @classmethod
    def from_env(cls) -> "LLMConfig":
        provider = os.environ.get("LLM_PROVIDER", "openai").lower()
        if provider not in {"openai", "anthropic", "claude-cli"}:
            raise LLMError("LLM_PROVIDER must be 'openai', 'anthropic', or 'claude-cli'")
        # The Claude Code CLI authenticates with its own login, so no key is needed.
        api_key = os.environ.get("LLM_API_KEY", "")
        if not api_key and provider != "claude-cli":
            raise LLMError("LLM_API_KEY is required")

        timeout_value = os.environ.get("LLM_TIMEOUT_SECONDS", "60")
        try:
            timeout_seconds = float(timeout_value)
        except ValueError as exc:
            raise LLMError("LLM_TIMEOUT_SECONDS must be a number") from exc
        if timeout_seconds <= 0:
            raise LLMError("LLM_TIMEOUT_SECONDS must be greater than zero")

        return cls(
            api_key=api_key,
            provider=provider,
            base_url=os.environ.get(
                "LLM_BASE_URL",
                "https://api.anthropic.com/v1" if provider == "anthropic" else cls.base_url,
            ).rstrip("/"),
            # An empty model lets the Claude Code CLI use its own default.
            model=os.environ.get("LLM_MODEL", "" if provider == "claude-cli" else cls.model),
            timeout_seconds=timeout_seconds,
            cli_path=os.environ.get("LLM_CLI_PATH", cls.cli_path),
        )


class OpenAICompatibleClient:
    """Client for OpenAI and other providers with the same chat API shape."""

    def __init__(self, config: LLMConfig):
        self._config = config

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> str:
        if not prompt.strip():
            raise ValueError("prompt must not be empty")
        if not 0 <= temperature <= 2:
            raise ValueError("temperature must be between 0 and 2")
        if max_tokens is not None and max_tokens <= 0:
            raise ValueError("max_tokens must be greater than zero")

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self._config.model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        body = json.dumps(payload).encode("utf-8")
        endpoint = f"{self._config.base_url}/chat/completions"
        http_request = request.Request(
            endpoint,
            data=body,
            headers={
                "Authorization": f"Bearer {self._config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=self._config.timeout_seconds) as response:
                response_body = response.read()
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace").strip()
            raise LLMError(f"LLM request failed with HTTP {exc.code}: {detail}") from exc
        except (error.URLError, TimeoutError) as exc:
            raise LLMError(f"LLM request failed: {exc}") from exc

        try:
            decoded: Any = json.loads(response_body)
            content = decoded["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise LLMError("LLM response did not contain choices[0].message.content") from exc
        if not isinstance(content, str) or not content:
            raise LLMError("LLM response content was empty")
        return content


class AnthropicClient:
    """Client for Anthropic's native Messages API."""

    def __init__(self, config: LLMConfig):
        self._config = config

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> str:
        if not prompt.strip():
            raise ValueError("prompt must not be empty")
        if not 0 <= temperature <= 1:
            raise ValueError("Anthropic temperature must be between 0 and 1")
        if max_tokens is not None and max_tokens <= 0:
            raise ValueError("max_tokens must be greater than zero")

        payload: dict[str, Any] = {
            "model": self._config.model,
            "max_tokens": max_tokens or 1024,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }
        if system:
            payload["system"] = system

        http_request = request.Request(
            f"{self._config.base_url}/messages",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "x-api-key": self._config.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=self._config.timeout_seconds) as response:
                response_body = response.read()
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace").strip()
            raise LLMError(f"LLM request failed with HTTP {exc.code}: {detail}") from exc
        except (error.URLError, TimeoutError) as exc:
            raise LLMError(f"LLM request failed: {exc}") from exc

        try:
            decoded: Any = json.loads(response_body)
            content = decoded["content"][0]["text"]
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise LLMError("Anthropic response did not contain content[0].text") from exc
        if not isinstance(content, str) or not content:
            raise LLMError("LLM response content was empty")
        return content


class ClaudeCLIClient:
    """Client that runs prompts through the Claude Code CLI in headless mode.

    The CLI does not expose temperature or max_tokens, so those arguments are
    validated for interface compatibility but otherwise ignored.
    """

    def __init__(self, config: LLMConfig):
        self._config = config

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> str:
        if not prompt.strip():
            raise ValueError("prompt must not be empty")
        if not 0 <= temperature <= 1:
            raise ValueError("temperature must be between 0 and 1")
        if max_tokens is not None and max_tokens <= 0:
            raise ValueError("max_tokens must be greater than zero")

        executable = shutil.which(self._config.cli_path)
        if executable is None:
            raise LLMError(f"Claude Code CLI not found: {self._config.cli_path}")

        # Disable tools, MCP servers, and saved sessions so the CLI behaves like
        # a plain text-completion call.
        command = [
            executable,
            "--print",
            "--output-format",
            "json",
            "--tools",
            "",
            "--strict-mcp-config",
            "--no-session-persistence",
        ]
        if self._config.model:
            command += ["--model", self._config.model]
        if system:
            command += ["--system-prompt", system]

        try:
            # The prompt goes over stdin to avoid command-line length limits.
            completed = subprocess.run(
                command,
                input=prompt,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=self._config.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise LLMError("Claude Code CLI timed out") from exc
        except OSError as exc:
            raise LLMError(f"Claude Code CLI failed to start: {exc}") from exc

        try:
            decoded: Any = json.loads(completed.stdout)
            content = decoded["result"]
            is_error = decoded.get("is_error", False)
        except (KeyError, TypeError, AttributeError, json.JSONDecodeError) as exc:
            detail = (completed.stderr or completed.stdout).strip()
            raise LLMError(
                f"Claude Code CLI exited with code {completed.returncode}: {detail}"
            ) from exc
        if is_error or completed.returncode != 0:
            raise LLMError(f"Claude Code CLI request failed: {content}")
        if not isinstance(content, str) or not content:
            raise LLMError("LLM response content was empty")
        return content


def create_client(config: LLMConfig) -> LLMClient:
    """Create the configured provider client."""

    if config.provider == "anthropic":
        return AnthropicClient(config)
    if config.provider == "openai":
        return OpenAICompatibleClient(config)
    if config.provider == "claude-cli":
        return ClaudeCLIClient(config)
    raise LLMError(f"Unsupported LLM provider: {config.provider}")

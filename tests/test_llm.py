import json
import os
import subprocess
import unittest
from unittest.mock import patch

from tilt_bot.llm import (
    AnthropicClient,
    ClaudeCLIClient,
    LLMConfig,
    LLMError,
    OpenAICompatibleClient,
)


class LLMConfigTests(unittest.TestCase):
    def test_from_env_requires_api_key(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(LLMError, "LLM_API_KEY is required"):
                LLMConfig.from_env()

    def test_from_env_reads_provider_settings(self) -> None:
        values = {
            "LLM_API_KEY": "test-key",
            "LLM_PROVIDER": "anthropic",
            "LLM_BASE_URL": "https://example.test/v1/",
            "LLM_MODEL": "test-model",
            "LLM_TIMEOUT_SECONDS": "12.5",
        }
        with patch.dict(os.environ, values, clear=True):
            config = LLMConfig.from_env()

        self.assertEqual(config.api_key, "test-key")
        self.assertEqual(config.provider, "anthropic")
        self.assertEqual(config.base_url, "https://example.test/v1")
        self.assertEqual(config.model, "test-model")
        self.assertEqual(config.timeout_seconds, 12.5)

    def test_from_env_claude_cli_does_not_require_api_key(self) -> None:
        with patch.dict(os.environ, {"LLM_PROVIDER": "claude-cli"}, clear=True):
            config = LLMConfig.from_env()

        self.assertEqual(config.provider, "claude-cli")
        self.assertEqual(config.api_key, "")
        self.assertEqual(config.model, "")
        self.assertEqual(config.cli_path, "claude")


class ClientTests(unittest.TestCase):
    def test_complete_sends_expected_request_and_returns_content(self) -> None:
        response = {"choices": [{"message": {"content": "hello"}}]}

        class FakeResponse:
            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, *args: object) -> None:
                return None

            def read(self) -> bytes:
                return json.dumps(response).encode("utf-8")

        config = LLMConfig(
            api_key="test-key",
            base_url="https://example.test/v1",
            model="test-model",
        )
        with patch("tilt_bot.llm.request.urlopen", return_value=FakeResponse()) as urlopen:
            result = OpenAICompatibleClient(config).complete(
                "Summarize this posting",
                system="Be concise",
                max_tokens=100,
            )

        self.assertEqual(result, "hello")
        sent_request = urlopen.call_args.args[0]
        self.assertEqual(sent_request.full_url, "https://example.test/v1/chat/completions")
        self.assertEqual(sent_request.headers["Authorization"], "Bearer test-key")
        payload = json.loads(sent_request.data.decode("utf-8"))
        self.assertEqual(payload["model"], "test-model")
        self.assertEqual(payload["max_tokens"], 100)
        self.assertEqual(payload["messages"][0]["content"], "Be concise")

    def test_anthropic_complete_uses_messages_api(self) -> None:
        response = {"content": [{"type": "text", "text": "hello"}]}

        class FakeResponse:
            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, *args: object) -> None:
                return None

            def read(self) -> bytes:
                return json.dumps(response).encode("utf-8")

        config = LLMConfig(
            api_key="test-key",
            provider="anthropic",
            base_url="https://example.test/v1",
            model="claude-test",
        )
        with patch("tilt_bot.llm.request.urlopen", return_value=FakeResponse()) as urlopen:
            result = AnthropicClient(config).complete(
                "Summarize this posting",
                system="Be concise",
                max_tokens=100,
            )

        self.assertEqual(result, "hello")
        sent_request = urlopen.call_args.args[0]
        self.assertEqual(sent_request.full_url, "https://example.test/v1/messages")
        self.assertEqual(sent_request.headers["X-api-key"], "test-key")
        self.assertEqual(sent_request.headers["Anthropic-version"], "2023-06-01")
        payload = json.loads(sent_request.data.decode("utf-8"))
        self.assertEqual(payload["model"], "claude-test")
        self.assertEqual(payload["system"], "Be concise")
        self.assertEqual(payload["max_tokens"], 100)


class ClaudeCLIClientTests(unittest.TestCase):
    config = LLMConfig(api_key="", provider="claude-cli", model="sonnet")

    def run_client(self, completed: subprocess.CompletedProcess) -> tuple[str, object]:
        with patch("tilt_bot.llm.shutil.which", return_value="/bin/claude"), patch(
            "tilt_bot.llm.subprocess.run", return_value=completed
        ) as run:
            result = ClaudeCLIClient(self.config).complete(
                "Summarize this posting", system="Be concise"
            )
        return result, run

    def test_complete_runs_cli_and_returns_result(self) -> None:
        stdout = json.dumps({"type": "result", "is_error": False, "result": "hello"})
        result, run = self.run_client(subprocess.CompletedProcess([], 0, stdout, ""))

        self.assertEqual(result, "hello")
        command = run.call_args.args[0]
        self.assertEqual(command[0], "/bin/claude")
        self.assertIn("--print", command)
        self.assertEqual(command[command.index("--model") + 1], "sonnet")
        self.assertEqual(command[command.index("--system-prompt") + 1], "Be concise")
        self.assertEqual(run.call_args.kwargs["input"], "Summarize this posting")

    def test_complete_raises_when_cli_reports_error(self) -> None:
        stdout = json.dumps({"type": "result", "is_error": True, "result": "Not logged in"})
        with self.assertRaisesRegex(LLMError, "Not logged in"):
            self.run_client(subprocess.CompletedProcess([], 1, stdout, ""))

    def test_complete_raises_when_cli_output_is_not_json(self) -> None:
        with self.assertRaisesRegex(LLMError, "exited with code 2: boom"):
            self.run_client(subprocess.CompletedProcess([], 2, "", "boom"))

    def test_complete_raises_when_cli_missing(self) -> None:
        with patch("tilt_bot.llm.shutil.which", return_value=None):
            with self.assertRaisesRegex(LLMError, "not found"):
                ClaudeCLIClient(self.config).complete("hi")


if __name__ == "__main__":
    unittest.main()

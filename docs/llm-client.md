# LLM Client

The LLM client provides a reusable interface for communicating with supported
LLM APIs.

## Components

- `LLMClient` defines the interface that future job-posting filters, scoring
  logic, and resume tailoring can depend on.
- `LLMConfig` stores connection settings and loads them from environment
  variables.
- `OpenAICompatibleClient` sends prompts and returns generated text.
- `AnthropicClient` sends prompts to Anthropic's native Messages API.
- `ClaudeCLIClient` runs prompts through the local Claude Code CLI.
- `create_client` selects the implementation from `LLMConfig.provider`.
- `LLMError` provides explicit errors for missing configuration, failed
  requests, and malformed responses.

## Supported providers

The client supports OpenAI or another provider exposing a compatible
`/chat/completions` endpoint, and Anthropic's native `/messages` endpoint.
Set `LLM_PROVIDER=anthropic` to use Anthropic; the default is `openai`.

Set `LLM_PROVIDER=claude-cli` to use the Claude Code CLI (`claude -p`). It
uses the CLI's own login (a Claude subscription or its configured key), so
`LLM_API_KEY` is not required. `LLM_MODEL` is optional (for example `sonnet`
or `opus`), and `LLM_CLI_PATH` can point at the executable if `claude` is not
on `PATH`. The CLI ignores `temperature` and `max_tokens`, and each call
starts a new process, so it is slower than the HTTP clients. Raise
`LLM_TIMEOUT_SECONDS` for long scraped pages.

## Example

```python
from tilt_bot.llm import LLMConfig, OpenAICompatibleClient

client = OpenAICompatibleClient(LLMConfig.from_env())
answer = client.complete(
    "Summarize this job posting.",
    system="Be concise and factual.",
)
```

See [the implementation](../src/tilt_bot/llm.py) for the request and response
handling.

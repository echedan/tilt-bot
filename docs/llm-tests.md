# LLM Tests

The tests verify the LLM integration without making a real network request or
incurring provider charges.

## Coverage

- Missing API keys are rejected.
- Environment settings are loaded and normalized correctly.
- The request endpoint, authorization header, model, prompts, and token limit
  are constructed correctly.
- A valid chat-completions response is parsed into returned text.
- The Anthropic client calls the Messages API with the expected headers and
  payload.
- The `claude-cli` provider loads without an API key.
- The Claude Code CLI client builds the expected command, passes the prompt
  over stdin, and parses the JSON result. CLI-reported errors, non-JSON
  output, and a missing executable raise `LLMError`. `subprocess.run` is
  mocked, so the CLI is never actually invoked.

Run the tests with:

```powershell
python -m unittest discover -s tests -v
```

The tests are in [tests/test_llm.py](../tests/test_llm.py).

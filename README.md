# tilt-bot

LLM-assisted tooling for filtering job postings, tailoring resumes, and applying.

## LLM integration

The integration supports OpenAI-compatible chat-completions providers,
Anthropic's native Messages API, and the local Claude Code CLI. Select the
provider with `LLM_PROVIDER` (`openai`, `anthropic`, or `claude-cli`).

1. Create and activate a virtual environment.
2. Install the package:

   ```powershell
   python -m pip install -e .
   ```

3. Set the variables shown in [.env.example](.env.example) in your shell.
   Keep the API key out of source control. The `claude-cli` provider needs
   no API key; it uses your Claude Code login instead.
4. Send a test prompt:

   ```powershell
   tilt-llm "Explain what makes a software engineering job posting a good match."
   ```

The reusable client is in [src/tilt_bot/llm.py](src/tilt_bot/llm.py).
Future posting filters and resume generation should depend on the `LLMClient`
interface rather than a specific provider.

## Documentation

- [LLM client](docs/llm-client.md)
- [LLM CLI](docs/llm-cli.md)
- [Project setup and configuration](docs/project-setup.md)
- [LLM tests](docs/llm-tests.md)

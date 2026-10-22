# tilt-bot

LLM-assisted tooling for filtering job postings, tailoring resumes, and applying.

## LLM integration

The integration supports OpenAI-compatible chat-completions providers,
Anthropic's native Messages API, and the local Claude Code CLI. Select the
provider with `LLM_PROVIDER` (`openai`, `anthropic`, or `claude-cli`).

### macOS / Linux

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   Your prompt shows `(.venv)` while it is active. Run `deactivate` to turn it
   off, or just close the terminal.

2. Install the package:

   ```bash
   python -m pip install -e .
   ```

3. Set the variables shown in [.env.example](.env.example) in your shell. For
   example, to use the Claude Code CLI (no API key needed):

   ```bash
   export LLM_PROVIDER=claude-cli
   export LLM_MODEL=haiku          # optional: haiku, sonnet, or opus
   export LLM_TIMEOUT_SECONDS=120
   ```

   For an API provider, set `LLM_PROVIDER`, `LLM_API_KEY`, and `LLM_MODEL`
   instead. Keep the API key out of source control.

4. Send a test prompt:

   ```bash
   tilt-llm "Reply with exactly: connection ok"
   ```

5. Run the unit tests (no LLM connection needed):

   ```bash
   python -m unittest discover -s tests
   ```

### Windows (PowerShell)

1. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

2. Install the package:

   ```powershell
   python -m pip install -e .
   ```

3. Set the variables shown in [.env.example](.env.example) in your shell:

   ```powershell
   $env:LLM_PROVIDER = "claude-cli"
   $env:LLM_TIMEOUT_SECONDS = "120"
   ```

4. Send a test prompt:

   ```powershell
   tilt-llm "Reply with exactly: connection ok"
   ```

5. Run the unit tests:

   ```powershell
   python -m unittest discover -s tests
   ```

### Expected result

A successful connection prints the model's reply. A configuration or
connection problem prints `Error: ...` and exits with a non-zero code. The
`claude-cli` provider needs [Claude Code](https://docs.claude.com/en/docs/claude-code)
installed and logged in (run `claude` once to sign in).

The reusable client is in [src/tilt_bot/llm.py](src/tilt_bot/llm.py).
Future posting filters and resume generation should depend on the `LLMClient`
interface rather than a specific provider.

## Documentation

- [LLM client](docs/llm-client.md)
- [LLM CLI](docs/llm-cli.md)
- [Project setup and configuration](docs/project-setup.md)
- [LLM tests](docs/llm-tests.md)

# Project Setup

The project uses Python packaging metadata in `pyproject.toml` and a `src`
layout.

## Installation

Create and activate a virtual environment, then install the package in
editable mode:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
```

The project currently uses only Python's standard library, so no third-party
runtime dependency is required. The optional `claude-cli` provider also needs
[Claude Code](https://docs.claude.com/en/docs/claude-code) installed and logged
in (run `claude` once interactively to sign in).

## Configuration

Copy the values from `.env.example` into the shell or environment manager used
to run the application:

```powershell
$env:LLM_API_KEY = "replace-me"
$env:LLM_BASE_URL = "https://api.openai.com/v1"
$env:LLM_MODEL = "gpt-4o-mini"
$env:LLM_TIMEOUT_SECONDS = "60"
```

To use the Claude Code CLI instead, no API key or base URL is needed:

```powershell
$env:LLM_PROVIDER = "claude-cli"
$env:LLM_MODEL = "sonnet"            # optional: haiku, sonnet, or opus
$env:LLM_CLI_PATH = "claude"         # optional: path to the executable
$env:LLM_TIMEOUT_SECONDS = "120"
```

| Variable | Used by | Default |
| --- | --- | --- |
| `LLM_PROVIDER` | all | `openai` |
| `LLM_API_KEY` | `openai`, `anthropic` | required |
| `LLM_BASE_URL` | `openai`, `anthropic` | provider's public API |
| `LLM_MODEL` | all | `gpt-4o-mini`; CLI default for `claude-cli` |
| `LLM_TIMEOUT_SECONDS` | all | `60` |
| `LLM_CLI_PATH` | `claude-cli` | `claude` |

Do not commit API keys. The `.gitignore` file excludes local `.env` files.

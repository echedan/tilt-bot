# LLM CLI

The `tilt-llm` command is a small smoke-test interface for sending a prompt to
the configured LLM.

## Usage

After installing the project:

```powershell
python -m pip install -e .
tilt-llm "Explain what makes a software engineering job posting a good match."
```

The command reads configuration from the environment, sends one prompt, and
prints the generated response. It returns a non-zero exit code and prints an
error to stderr when configuration or the request is invalid.

To try the Claude Code provider:

```powershell
$env:LLM_PROVIDER = "claude-cli"
tilt-llm "Extract the job title and company as JSON: 'Acme Corp is hiring a Senior Data Engineer.'"
```

The command is implemented in
[src/tilt_bot/cli.py](../src/tilt_bot/cli.py).

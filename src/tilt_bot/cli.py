"""Command-line entry point for testing the LLM integration."""

from __future__ import annotations

import argparse
import sys

from .llm import LLMConfig, LLMError, create_client


def main() -> int:
    parser = argparse.ArgumentParser(description="Send a prompt to the configured LLM.")
    parser.add_argument("prompt", help="Prompt to send")
    args = parser.parse_args()

    try:
        client = create_client(LLMConfig.from_env())
        print(client.complete(args.prompt))
    except (LLMError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Wrapper for CLI to ensure error messages are visible."""

import os


def main():
    """Entry point wrapper that ensures error messages are visible."""
    # Force unbuffered output
    os.environ["PYTHONUNBUFFERED"] = "1"

    # Import after setting env var
    from data4ai.cli import app

    # Just run the app normally - typer handles its own errors
    app()


if __name__ == "__main__":
    main()

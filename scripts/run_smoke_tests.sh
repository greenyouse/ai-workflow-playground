#!/usr/bin/env bash
set -euo pipefail

# Run the smoke tests against the `src` package
PYTHONPATH=src pytest -q "$@"

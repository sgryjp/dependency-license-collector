# Dependency License Collector

> A command which collects license data of dependency packages.

Supported input files:

1. Python
   - requirements.txt
2. Node.js
   - package.json

## Example Usage

```sh
export GITHUB_TOKEN=__TOKEN__
pip freeze | uv run dlc -f requirements_txt -o out
```

This command support reading environment variable from `.env`.

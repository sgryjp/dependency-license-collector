# license-lister

Command to download license files of dependency packages

## Example Usage

```sh
export GITHUB_TOKEN=__TOKEN__
pip freeze | uv run license-lister --format requirements_txt --output out
```

This command support reading environment variable from `.env`.

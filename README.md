<!-- markdownlint-disable no-inline-html -->

# Dependency License Collector

> A command which collects license data of dependency packages.

## Supported Inputs

1. Python
   - requirements.txt
   <!-- 2. Node.js ()
   - package.json -->

## Command Usage

```text
Usage: dlc [OPTIONS] FILENAME

  Collect OSS license data of dependency packages.

  DLC (Dependency License Collector) collects dependency packages' license
  data, download license file content, and generate an HTML report.

  Use a special value "-" as FILENAME to read data from standard input.

  For Python, a subset of "requirements.txt" is supported. Strictly writing,
  only the dependency specifier using `==` is supported.

Options:
  -f, --format [requirements_txt]
                                  Input data format.  [required]
  -o, --outdir DIRECTORY          Directory to store generated report files.
  -v, --verbose                   Log more verbose message.
  -q, --quiet                     Log less verbose message.
  --help                          Show this message and exit.
```

## Configurations (Environment Variables)

- `GITHUB_TOKEN`
  - GitHub Personal Token for API access.
- `MAX_WORKERS`
  - Number of worker threads to use.

> [!TIP]
> This command can read environment variables from `.env` file at the current directory.

## Example Usage (Python)

- [uv]

  ```sh
  uv export --no-hashes | dlc -f requirements_txt -
  ```

- [Poetry] (with poetry-plugin-export)

  ```sh
  poetry export --without-hashes | dlc -f requirements_txt -
  ```

- [Pipenv]

  ```sh
  pipenv requirements | dlc -f requirements_txt -
  ```

- [pip]

  ```sh
  pip freeze | dlc -f requirements_txt -
  ```

[pip]: https://pip.pypa.io/
[Pipenv]: https://pipenv.pypa.io/en/latest/
[Poetry]: https://python-poetry.org/
[uv]: https://docs.astral.sh/uv/

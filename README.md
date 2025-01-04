<!-- markdownlint-disable no-inline-html -->

# Dependency License Collector

[![Test](https://github.com/sgryjp/dependency-license-collector/actions/workflows/ci.yaml/badge.svg)](https://github.com/sgryjp/dependency-license-collector/actions/workflows/ci.yaml)
[![Coverage Status](https://coveralls.io/repos/github/sgryjp/dependency-license-collector/badge.svg?branch=ci/use-coveralls)](https://coveralls.io/github/sgryjp/dependency-license-collector?branch=ci/use-coveralls)

> A tool for collecting dependency licenses in software projects.

## Supported Inputs

1. Python
   - requirements.txt
   <!-- 2. Node.js ()
   - package.json -->

## Command Usage

```text
Usage: dlc [OPTIONS] FILENAME

  A tool for collecting dependency licenses in software projects.

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

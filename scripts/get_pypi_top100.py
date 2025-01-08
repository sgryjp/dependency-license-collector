"""Script to create requirements-100.txt which contains PyPI top 100 packages.

This script must be run in a virtual environment where dlc is installed.
"""  # noqa: INP001

import logging
from concurrent.futures import Executor, ThreadPoolExecutor
from pathlib import Path

import click
import requests
import rich.logging

from dlc.models.pypi import PyPIPackage, PyPIStats
from dlc.settings import SETTINGS

_logger = logging.getLogger(__name__)


@click.command
def main() -> None:
    """Collect PyPI top 100 package data."""
    logging.basicConfig(handlers=[rich.logging.RichHandler()])

    with ThreadPoolExecutor() as executor:
        packages = _collect(executor)
        Path("requirements-100.txt").write_text(
            "\n".join(
                [f"{package.info.name}=={package.info.version}" for package in packages]
            ),
            encoding="utf-8",
        )


def _collect(executor: Executor) -> list[PyPIPackage]:
    # https://docs.pypi.org/api/stats/#project-stats
    headers = {}
    headers["Accept"] = "application/json"
    response = requests.get(
        "https://pypi.org/stats/", headers=headers, timeout=SETTINGS.timeout
    )
    if response.status_code != 200:
        msg = f"Failed to get PyPI statistics data. status_code={response.status_code}"
        _logger.error(msg)
        raise Exception(msg)
    stats = PyPIStats.model_validate(response.json())

    # https://docs.pypi.org/api/json/#get-a-project
    headers = {}
    headers["Accept"] = "application/json"
    urls = [f"https://pypi.org/pypi/{name}/json" for name in stats.top_packages]
    responses = list(
        executor.map(
            lambda x: requests.get(x, headers=headers, timeout=SETTINGS.timeout), urls
        )
    )
    package_data: list[PyPIPackage] = []
    for package_name, response in zip(stats.top_packages, responses):
        if response.status_code != 200:
            _logger.warning("Failed to get PyPI package data for %s.", package_name)
        package_data.append(PyPIPackage.model_validate(response.json()))

    return package_data


if __name__ == "__main__":
    main()

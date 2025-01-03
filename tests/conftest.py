"""Test configuration."""

import logging
import time
from collections.abc import Iterator
from concurrent.futures import Executor, ThreadPoolExecutor
from pathlib import Path

import httpx
import pytest

from dlc.models.pypi import PyPIPackage, PyPIStats
from dlc.settings import SETTINGS

_logger = logging.getLogger()
_workspace_path = Path(__file__).parents[1]
_cache_path = _workspace_path.joinpath(".cache_pypi_top100.jsonl")
_cache_expiry = 24 * 3600  # 1 day


@pytest.fixture
def package_info_logger() -> logging.Logger:
    formatter = logging.Formatter("%(asctime)s %(message)s")

    handler = logging.FileHandler("test_package_info.log", encoding="utf-8")
    handler.formatter = formatter

    logger = logging.getLogger("tests.package_info")
    logger.propagate = False
    logger.setLevel("DEBUG")
    logger.handlers = [handler]

    return logger


@pytest.fixture
def executor() -> Iterator[Executor]:
    with ThreadPoolExecutor(SETTINGS.max_workers) as executor:
        yield executor


@pytest.fixture
def pypi_top100(executor: Executor) -> Iterator[list[PyPIPackage]]:
    expired = (
        not _cache_path.exists()
        or time.time() - _cache_expiry > _cache_path.stat().st_mtime
    )
    if not expired:
        yield [
            PyPIPackage.model_validate_json(s)
            for s in _cache_path.read_text().splitlines()
        ]
    else:
        # https://docs.pypi.org/api/stats/#project-stats
        headers = {}
        headers["Accept"] = "application/json"
        response = httpx.get("https://pypi.org/stats/", headers=headers)
        if response.status_code != 200:
            msg = f"Failed to get PyPI statistics data. status_code={response.status_code}"
            pytest.fail(msg)
        stats = PyPIStats.model_validate(response.json())

        # https://docs.pypi.org/api/json/#get-a-project
        headers = {}
        headers["Accept"] = "application/json"
        urls = [f"https://pypi.org/pypi/{name}/json" for name in stats.top_packages]
        responses = list(executor.map(lambda x: httpx.get(x, headers=headers), urls))
        package_data: list[PyPIPackage] = []
        for package_name, response in zip(stats.top_packages, responses):
            if response.status_code != 200:
                _logger.warning("Failed to get PyPI package data for %s.", package_name)
            package_data.append(PyPIPackage.model_validate(response.json()))
        _cache_path.write_text("\n".join([p.model_dump_json() for p in package_data]))

        yield package_data

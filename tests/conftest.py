"""Test configuration."""

import logging
import pickle
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
_cache_path = _workspace_path.joinpath(".cache_pypi_top100.pkl")
_cache_expiry = 24 * 3600  # 1 day


@pytest.fixture
def executor() -> Iterator[Executor]:
    with ThreadPoolExecutor(SETTINGS.max_workers) as executor:
        yield executor


@pytest.fixture
def pypi_top100(executor: Executor) -> Iterator[list[PyPIPackage]]:
    expired = (
        not _cache_path.exists()
        or time.time() - _cache_expiry > _cache_path.stat().st_ctime
    )
    if not expired:
        yield pickle.loads(_cache_path.read_bytes())  # noqa: S301
    else:
        _cache_path.unlink(missing_ok=True)

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
        _cache_path.write_bytes(pickle.dumps(package_data, 5))

        yield package_data

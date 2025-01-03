"""Test configuration."""

import logging
from collections.abc import Iterator
from concurrent.futures import Executor, ThreadPoolExecutor

import pytest

from dlc.settings import SETTINGS


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


@pytest.fixture(scope="session")
def executor() -> Iterator[Executor]:
    with ThreadPoolExecutor(SETTINGS.max_workers) as executor:
        yield executor

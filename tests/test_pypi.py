import logging
from concurrent.futures import Executor

import pytest

from dlc.registries.pypi import PyPIPackage, collect_package_metadata

_logger = logging.getLogger(__name__)


def test_can_get_pypi_top100(executor: Executor, pypi_top100: list[PyPIPackage]):
    dependency_specifiers = [f"{p.info.name}=={p.info.version}" for p in pypi_top100]
    packages = collect_package_metadata(executor, dependency_specifiers)
    _logger.info("Collected %d packages", len(packages))

    num_failures = 0
    for package in packages:
        try:
            assert (
                package.raw_license_data is not None
            ), f"{package.name} {package.version}"
            assert package.license_file is not None, f"{package.name} {package.version}"
        except AssertionError as exc:
            _logger.error("%s %s: %s", package.name, package.version, exc)
            num_failures += 1
    assert num_failures == 0


@pytest.mark.parametrize(
    ("name", "version"),
    [
        ("libdeeplake", "0.0.153"),  # "Source" URL returns 404
    ],
)
def test_pypi_past_cases(executor: Executor, name: str, version: str):
    dependency_specifier = f"{name}=={version}"
    packages = collect_package_metadata(executor, [dependency_specifier])
    assert len(packages) == 1
    package = packages[0]

    assert package.license_file is not None, f"{package.name} {package.version}"

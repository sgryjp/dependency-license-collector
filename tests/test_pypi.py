import logging
from concurrent.futures import Executor

import pytest

from dlc.registries.pypi import PyPIPackage, collect_package_metadata

_logger = logging.getLogger(__name__)
_p = pytest.param


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
        _p("click", "8.1.8", id="normal"),
        _p(
            "libdeeplake",
            "0.0.153",
            id="PyPI.info.project_urls['Source'] is 404",
            marks=pytest.mark.xfail,
        ),
        _p(
            "apache-flink",
            "1.20.0",
            id="PyPI.info.license is URL",
            marks=pytest.mark.xfail,
        ),
    ],
)
def test_collect_package_metadata(
    executor: Executor, package_info_logger: logging.Logger, name: str, version: str
) -> None:
    package = None
    try:
        dependency_specifier = f"{name}=={version}"
        packages = collect_package_metadata(executor, [dependency_specifier])
        assert len(packages) == 1
        package = packages[0]

        license_file = package.license_file
        assert license_file is not None, f"{package.name} {package.version}"
    except AssertionError:
        package_info_logger.info("********** %s %s", name, version)
        package_info_logger.info(
            'To test this package: echo "%s==%s" | uv run dlc -f requirements_txt -o report -',
            name,
            version,
        )
        if package is not None:
            package_info_logger.info(
                "Package Data:\n```json\n%s\n```", package.model_dump_json(indent=2)
            )
        raise

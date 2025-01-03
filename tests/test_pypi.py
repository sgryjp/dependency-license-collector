import logging
from concurrent.futures import Executor

import pytest

from dlc.registries.pypi import collect_package_metadata

_p = pytest.param


@pytest.mark.parametrize(
    ("name", "version"),
    [
        _p("click", "8.1.8", id="PyPI.info.project_urls['Source'] is GitHub"),
        _p(
            "libdeeplake",
            "0.0.153",
            id="PyPI.info.project_urls['Source'] is 404",
            marks=pytest.mark.xfail,
        ),
        _p("apache-flink", "1.20.0", id="PyPI.info.license is URL"),
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

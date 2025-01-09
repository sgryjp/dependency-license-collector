import logging
from concurrent.futures import Executor
from typing import Optional
from warnings import warn

import pytest

from dlc.registries.pypi import collect_package_metadata
from dlc.settings import SETTINGS

_p = pytest.param


@pytest.mark.parametrize(
    ("name", "version", "project_urls_key"),
    [
        _p("click", "8.1.8", "Source", id="PyPI.info.project_urls['Source'] is GitHub"),
        _p(
            "sqlalchemy",
            "2.0.36",
            "Issue Tracker",
            id="PyPI.info.project_urls['Issue Tracker'] is GitHub",
        ),
        _p(
            "libdeeplake",
            "0.0.153",
            "Source",
            id="PyPI.info.project_urls['Source'] is 404",
            marks=pytest.mark.xfail,
        ),
        _p("apache-flink", "1.20.0", None, id="PyPI.info.license is URL"),
    ],
)
def test_collect_package_metadata(  # noqa: PLR0913
    monkeypatch: pytest.MonkeyPatch,
    executor: Executor,
    package_info_logger: logging.Logger,
    name: str,
    version: str,
    project_urls_key: Optional[str],
) -> None:
    monkeypatch.setattr(SETTINGS, "max_workers", 1)

    package = None
    try:
        dependency_specifier = f"{name}=={version}"
        packages = collect_package_metadata(executor, [dependency_specifier])
        assert len(packages) == 1
        package = packages[0]

        if project_urls_key is not None:
            assert package is not None
            assert package.registry_data is not None
            assert package.registry_data.info.project_urls is not None
            if project_urls_key not in package.registry_data.info.project_urls:
                warn(
                    f"Expected key of `project_urls` was not found. key={project_urls_key}",
                    stacklevel=1,
                )

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

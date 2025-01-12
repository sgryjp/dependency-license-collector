import io
import logging
from concurrent.futures import Executor
from textwrap import dedent
from typing import Optional
from warnings import warn

import pytest

from dlc.registries.pypi import _read_requirements_txt, collect_package_metadata
from dlc.settings import SETTINGS

_p = pytest.param


@pytest.mark.parametrize(
    ("requirements_txt", "expected"),
    [
        _p("# foo==1.0.0\nbar==2.0.0", ["bar==2.0.0"], id="comment"),
        _p("-e .\nfoo==1.0.0", ["foo==1.0.0"], id="-e"),
        _p("-r requirements.txt\nfoo==1.0.0", ["foo==1.0.0"], id="-r"),
        _p(
            dedent(
                """\
                typing-extensions==4.12.2 \\
                --hash=sha256:04e5ca0351e0f3f85c6853954072df659d0d13fac324d0072316b67d7794700d \\
                --hash=sha256:1a7ead55c7e559dd4dee8856e3a88b41225abfe1ce8df57b7c13915fe121ffb8
                """
            ),
            ["typing-extensions==4.12.2"],
            marks=pytest.mark.xfail,
            id="--hash",
        ),
    ],
)
def test_extract_requirements(requirements_txt: str, expected: str):
    with io.StringIO(requirements_txt) as f:
        requirements = _read_requirements_txt(f)
    actual = [str(r) for r in requirements]
    assert actual == expected


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

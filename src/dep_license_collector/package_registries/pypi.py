from __future__ import annotations

from concurrent.futures import Executor

import httpx
import pydantic
import structlog
from typing_extensions import Literal

from dep_license_collector.models import Package, PackageLicense
from dep_license_collector.source_repositories.github import (
    GitHubLicenseContent,
    get_license_data,
)


class _PyPIPackageInfo(pydantic.BaseModel):
    author: str | None
    classifiers: list[str] | None
    license: str | None
    name: str
    project_urls: dict[str, str] | None
    release_url: pydantic.HttpUrl | None
    version: str


class PyPIPackage(pydantic.BaseModel):
    info: _PyPIPackageInfo


class PyPIStatData(pydantic.BaseModel):
    top_packages: dict[str, dict[Literal["size"], int]]
    total_packages_size: int


log = structlog.get_logger()


def collect_package_metadata(
    executor: Executor, dependency_specifiers: list[str]
) -> list[Package]:
    # Extract package name and version number
    name_and_version_tuples = [
        (tup[0].strip(), tup[1].strip())
        for specifier in dependency_specifiers
        if "==" in specifier
        if len(tup := specifier.split("==")) == 2
    ]

    # Get package metadata from PyPI
    log.info(
        "Start fetching %d package metadata from PyPI...", len(name_and_version_tuples)
    )
    responses = list(
        executor.map(
            lambda x: _get_pypi_package_data(x[0], x[1]), name_and_version_tuples
        )
    )

    # Find source repository URL in the PyPI metadata
    pypi_records: dict[tuple[str, str], PyPIPackage] = {}
    repos_urls: dict[tuple[str, str], str | None] = {}
    for name, version, response in responses:
        if response.status_code != 200:
            log.warning("Failed to get package data for %s %s", name, version)
            continue

        package_data = PyPIPackage.model_validate(response.json())
        pypi_records[(name, version)] = package_data

        # Try getting source repository URL
        repos_urls[(name, version)] = _guess_repository_url(package_data)

    # Get license information from source repository
    license_contents = list(executor.map(_get_license_file, repos_urls.values()))

    return [
        _merge_package_metadata(name, version, pypi_record, license_content)
        for ((name, version), pypi_record), license_content in zip(
            pypi_records.items(), license_contents
        )
    ]


def _guess_repository_url(package_data: PyPIPackage) -> str | None:
    if package_data.info.project_urls is None:
        return None

    for key in ("github", "repository", "source", "homepage"):
        for k, v in package_data.info.project_urls.items():
            if k.lower().startswith(key):
                return v

    return None


def _get_pypi_package_data(name: str, version: str) -> tuple[str, str, httpx.Response]:
    return name, version, httpx.get(f"https://pypi.org/pypi/{name}/{version}/json")


def _get_license_file(repos_url: str | None) -> GitHubLicenseContent | None:
    if repos_url is None:
        return None

    if (license_content := get_license_data(repos_url)) is not None:
        return license_content
    else:
        return None


def _merge_package_metadata(
    package_name: str,
    package_version: str,
    pypi_record: PyPIPackage,
    license_content: GitHubLicenseContent | None,
) -> Package:
    if license_content is not None:
        package_license = PackageLicense(
            name=license_content.license.name,
            spdx_id=license_content.license.spdx_id,
            content=license_content.decode_content(),
        )
    else:
        if pypi_record.info.license is not None and len(pypi_record.info.license) < 36:
            package_license = PackageLicense(
                name=pypi_record.info.license, spdx_id=None, content=None
            )
        else:
            package_license = None

    return Package(
        name=package_name,
        version=package_version,
        release_url=pypi_record.info.release_url,
        license=package_license,
    )

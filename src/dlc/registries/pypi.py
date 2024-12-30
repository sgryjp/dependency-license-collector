"""Functions related to PyPI package registry."""

import logging
from concurrent.futures import Executor
from time import monotonic
from typing import Optional

import httpx

from dlc.models.common import Package, PackageLicense
from dlc.models.github import GitHubLicenseContent
from dlc.models.pypi import PyPIPackage
from dlc.repositories.github import (
    get_license_data_from_github,
)

_logger = logging.getLogger(__name__)


def collect_package_metadata(
    executor: Executor,
    dependency_specifiers: list[str],
) -> list[Package]:
    n_packages = len(dependency_specifiers)
    _logger.info(
        "Start collecting license data of %d package(s) from PyPI.",
        n_packages,
    )

    # Extract package name and version number
    name_and_version_tuples = [
        (tup[0].strip(), tup[1].strip())
        for specifier in dependency_specifiers
        if "==" in specifier
        if len(tup := specifier.split("==")) == 2
    ]
    _logger.debug("Target packages: %s", name_and_version_tuples)

    # Get package metadata from PyPI
    _logger.info("Fetching package metadata from PyPI.")
    t0 = monotonic()
    responses = list(
        executor.map(
            lambda x: _get_pypi_package_data(x[0], x[1]),
            name_and_version_tuples,
        ),
    )
    elapsed_seconds = monotonic() - t0
    _logger.info("Fetched in %.3g seconds.", elapsed_seconds)

    # Find source repository URL in the PyPI metadata
    pypi_records: dict[tuple[str, str], PyPIPackage] = {}
    repos_urls: dict[tuple[str, str], Optional[str]] = {}
    for name, version, response in responses:
        if response.status_code != 200:
            _logger.warning("Failed to get package data for %s %s", name, version)
            continue

        package_data = PyPIPackage.model_validate(response.json())
        pypi_records[(name, version)] = package_data

        # Try getting source repository URL
        repo_url = _guess_repository_url(package_data)
        _logger.debug(
            "Resolved source repository URL for %s %s as %s", name, version, repo_url
        )
        repos_urls[(name, version)] = repo_url

    # Get license information from source repository
    _logger.info("Fetching license information from source repository.")
    t0 = monotonic()
    license_contents = list(executor.map(_get_license_file, repos_urls.values()))
    elapsed_seconds = monotonic() - t0
    _logger.info("Fetched in %.3g seconds.", elapsed_seconds)

    return [
        _merge_package_metadata(name, version, pypi_record, license_content)
        for ((name, version), pypi_record), license_content in zip(
            pypi_records.items(),
            license_contents,
        )
    ]


def _guess_repository_url(package_data: PyPIPackage) -> Optional[str]:
    if package_data.info.project_urls is None:
        return None

    for key in ("github", "repository", "source", "homepage"):
        for k, v in package_data.info.project_urls.items():
            if k.lower().startswith(key):
                return v

    return None


def _get_pypi_package_data(name: str, version: str) -> tuple[str, str, httpx.Response]:
    url = f"https://pypi.org/pypi/{name}/{version}/json"
    _logger.debug("GET %s", url)
    return name, version, httpx.get(url)


def _get_license_file(repos_url: Optional[str]) -> Optional[GitHubLicenseContent]:
    if repos_url is None:
        return None

    if (license_content := get_license_data_from_github(repos_url)) is not None:
        return license_content
    return None


def _merge_package_metadata(
    package_name: str,
    package_version: str,
    pypi_record: PyPIPackage,
    license_content: Optional[GitHubLicenseContent],
) -> Package:
    if license_content is not None:
        package_license = PackageLicense(
            name=license_content.license.name,
            spdx_id=license_content.license.spdx_id,
            content=license_content.decode_content(),
        )
    elif pypi_record.info.license is not None and len(pypi_record.info.license) < 36:
        package_license = PackageLicense(
            name=pypi_record.info.license,
            spdx_id=None,
            content=None,
        )
    else:
        package_license = None

    return Package(
        name=package_name,
        version=package_version,
        release_url=pypi_record.info.release_url,
        license=package_license,
    )

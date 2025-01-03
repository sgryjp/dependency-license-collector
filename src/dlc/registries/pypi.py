"""Functions related to PyPI package registry."""

import logging
from concurrent.futures import Executor
from pathlib import Path
from time import monotonic
from typing import Optional

import httpx

from dlc.exceptions import LicenseDataUnavailableError
from dlc.models.common import Package
from dlc.models.github import GitHubLicenseContent
from dlc.models.pypi import PyPIPackage
from dlc.repositories.github import (
    get_file_list_from_github,
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
    license_contents = list(
        executor.map(
            lambda x: _get_license_info(x[0][0], x[0][1], x[1]), repos_urls.items()
        )
    )
    elapsed_seconds = monotonic() - t0
    _logger.info("Fetched in %.3g seconds.", elapsed_seconds)

    return [
        Package(
            name=name,
            version=version,
            registry_data=pypi_record,
            license_data=license_content,
        )
        for ((name, version), pypi_record), license_content in zip(
            pypi_records.items(),
            license_contents,
        )
    ]


def _guess_repository_url(package_data: PyPIPackage) -> Optional[str]:
    if package_data.info.project_urls is None:
        return None

    for key in ("github", "repository", "source", "homepage", "download"):
        for k, v in package_data.info.project_urls.items():
            if (
                k.lower().startswith(key)
                and "github" in str(v).lower()  # TODO: Support GitLab etc.
            ):
                return str(v)

    return None


def _get_pypi_package_data(name: str, version: str) -> tuple[str, str, httpx.Response]:
    url = f"https://pypi.org/pypi/{name}/{version}/json"
    _logger.debug("GET %s", url)
    return name, version, httpx.get(url)


def _get_license_info(
    name: str, version: str, repos_url: Optional[str]
) -> Optional[GitHubLicenseContent]:
    if repos_url is None:
        return None

    # Try getting license data from GitHub
    try:
        if (license_content := get_license_data_from_github(repos_url)) is not None:
            return license_content
    except LicenseDataUnavailableError:
        _logger.warning("License data not found. package=%s version=%s", name, version)
        try:
            # Try searching for a license file in its source tree
            tree_data = get_file_list_from_github(repos_url)
            if tree_data is not None:
                scored_file_paths = sorted(
                    [
                        (score, item.path, item.url)
                        for item in tree_data.tree
                        if item.path is not None and item.type == "blob"
                        if (score := _license_file_likelihood(item.path)) >= 0
                    ]
                )
                if len(scored_file_paths) > 0:
                    _, _, url = scored_file_paths[0]
                    # TODO: Fetch the URL and parse response in form {sha, node_id, size, url, content, encoding}
                    _logger.critical("### url=%s", url)
        except Exception:
            _logger.warning(
                "Failed to get file list. package=%s version=%s repos_url=%s",
                name,
                version,
                repos_url,
            )

    _logger.warning(
        "Unsupported source repository. package=%s, version=%s, repos_url=%s",
        name,
        version,
        repos_url,
    )

    return None


def _license_file_likelihood(name: str) -> int:
    license_filenames = [
        "LICENSE",
        "LICENSE.md",
        "LICENSE.txt",
        "LICENSE.rst",
        "COPYING",
        "COPYING.md",
        "COPYING.txt",
        "COPYING.rst",
    ]

    path = Path(name)

    for i, s in enumerate(license_filenames):
        if s.lower() == path.name.lower():
            return (i + 1) + len(path.parts) * 1000
    return -1

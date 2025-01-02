from typing import Any, Optional

from pydantic import BaseModel, HttpUrl
from typing_extensions import Literal

from dlc.models.version import Version


class PyPIPackageInfo(BaseModel):
    """Package information.

    Response of "Get a project" JSON API
    (`https://pypi.org/pypi/{project}/json`).

    References
    ----------
    https://docs.pypi.org/api/json/#get-a-project

    """

    author: Optional[str]
    author_email: Optional[str]
    bugtrack_url: Optional[str]
    classifiers: Optional[list[str]]
    description: Optional[str]
    description_content_type: Optional[str]
    docs_url: Optional[str]
    download_url: Optional[str]
    downloads: dict[Literal["last_day", "last_month", "last_week"], int]
    dynamic: Optional[list[str]]
    home_page: Optional[str]
    keywords: Optional[str]
    license: Optional[str]
    maintainer: Optional[str]
    maintainer_email: Optional[str]
    name: str
    package_url: Optional[HttpUrl]
    platform: Optional[str]
    project_url: Optional[HttpUrl]  # URL of PyPI Project
    project_urls: Optional[dict[str, HttpUrl]]
    provides_extra: Optional[list[str]]
    release_url: Optional[HttpUrl]
    requires_dist: Optional[list[str]]
    requires_python: Optional[str]
    summary: Optional[str]
    version: str
    yanked: Optional[bool]
    yanked_reason: Optional[str]


class PyPIPackage(BaseModel):
    """PyPI package data.

    Response of "Get a release" JSON API
    (`https://pypi.org/pypi/{project}/{version}/json`).

    References
    ----------
    https://docs.pypi.org/api/json/#get-a-project

    """

    _tag: Literal["pypi"] = "pypi"
    info: PyPIPackageInfo
    last_serial: int
    releases: Optional[dict[Version, list[dict[str, Any]]]] = None
    urls: list[dict[str, Any]]
    vulnerabilities: list[Any]


class PyPIStats(BaseModel):
    """PyPI statistics.

    References
    ----------
    https://docs.pypi.org/api/stats/

    """

    top_packages: dict[str, dict[Literal["size"], int]]
    total_packages_size: int

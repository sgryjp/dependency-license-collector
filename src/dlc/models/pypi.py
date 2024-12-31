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
    classifiers: Optional[list[str]]
    license: Optional[str]
    name: str
    project_urls: Optional[dict[str, str]]
    release_url: Optional[HttpUrl]
    version: str


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

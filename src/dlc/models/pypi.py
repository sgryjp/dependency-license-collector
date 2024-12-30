from typing import Optional

from pydantic import BaseModel, HttpUrl
from typing_extensions import Literal


class PyPIPackageInfo(BaseModel):
    """Package information.

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

    References
    ----------
    https://docs.pypi.org/api/json/#get-a-project

    """

    info: PyPIPackageInfo


class PyPIStats(BaseModel):
    """PyPI statistics.

    References
    ----------
    https://docs.pypi.org/api/stats/

    """

    top_packages: dict[str, dict[Literal["size"], int]]
    total_packages_size: int

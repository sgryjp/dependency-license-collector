from typing import Literal, Optional

from pydantic import BaseModel, HttpUrl
from typing_extensions import TypeAlias

InputFormat: TypeAlias = Literal["requirements_txt"]
# RegistryName: TypeAlias = Literal["PyPI"]  # noqa: ERA001
# RepositoryName: TypeAlias = Literal["GitHub"]  # noqa: ERA001


class PackageLicense(BaseModel):
    name: str
    spdx_id: Optional[str]
    content: Optional[bytes]


class Package(BaseModel):
    name: str
    version: str
    release_url: Optional[HttpUrl]
    license: Optional[PackageLicense]

import pydantic
from typing_extensions import Literal

InputFormat = Literal["requirements_txt"]


class PackageLicense(pydantic.BaseModel):
    name: str
    spdx_id: str | None
    content: bytes | None


class Package(pydantic.BaseModel):
    name: str
    version: str
    release_url: pydantic.HttpUrl | None
    license: PackageLicense | None

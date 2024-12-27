import pydantic
from typing_extensions import Literal

Language = Literal["python"]


class PackageLicense(pydantic.BaseModel):
    name: str
    spdx_id: str | None
    content: bytes | None


class Package(pydantic.BaseModel):
    name: str
    version: str
    url: pydantic.HttpUrl | None
    license: PackageLicense | None

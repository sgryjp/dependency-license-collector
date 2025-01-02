from typing import Literal, Optional, Union

from pydantic import BaseModel
from typing_extensions import TypeAlias, assert_never

from dlc.models.github import GitHubLicenseContent
from dlc.models.pypi import PyPIPackage
from dlc.models.version import Version

InputFormat: TypeAlias = Literal["requirements_txt"]


class Package(BaseModel):
    name: str
    version: Version
    package_data: Union[PyPIPackage, None]
    raw_license_data: Union[GitHubLicenseContent, None]

    @property
    def license_name(self) -> Optional[str]:
        if self.raw_license_data is None:
            return None

        if self.raw_license_data._tag == "github":
            name = self.raw_license_data.license.spdx_id
            if name is None or name == "NOASSERTION":
                name = self.raw_license_data.license.name
            return name
        else:
            assert_never(self.raw_license_data._tag)
            raise AssertionError()

    @property
    def license_file(self) -> Optional[bytes]:
        if self.raw_license_data is None:
            return None

        if self.raw_license_data._tag == "github":
            return self.raw_license_data.decode_content()
        elif self.raw_license_data._tag == "null":
            return None
        else:
            assert_never(self.raw_license_data._tag)
            raise AssertionError()

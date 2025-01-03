import re
from typing import Literal, Optional, Union

import httpx
from pydantic import BaseModel, computed_field
from typing_extensions import TypeAlias, assert_never

from dlc.models.github import GitHubLicenseContent
from dlc.models.pypi import PyPIPackage
from dlc.models.version import Version

InputFormat: TypeAlias = Literal["requirements_txt"]
_re_http_url = re.compile(r"^https?://")


class Package(BaseModel):
    name: str
    version: Version
    registry_data: Union[PyPIPackage, None]
    license_data: Union[GitHubLicenseContent, None]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def license_name(self) -> Optional[str]:
        if self.license_data is None:
            return None

        if self.license_data._tag == "github":
            name = self.license_data.license.spdx_id
            if name is None or name == "NOASSERTION":
                name = self.license_data.license.name
            return name
        else:
            assert_never(self.license_data._tag)
            raise AssertionError()

    @property
    def license_file(self) -> Optional[bytes]:
        if self.license_data is None:
            # Try using package registry data
            if (
                self.registry_data is not None
                and self.registry_data._tag == "pypi"
                and self.registry_data.info.license is not None
                and _re_http_url.match(self.registry_data.info.license)
            ):
                resp = httpx.get(
                    self.registry_data.info.license, headers={"Accept": "text/plain"}
                )
                return resp.content

            return None

        elif self.license_data._tag == "github":
            return self.license_data.decode_content()

        else:
            assert_never(self.license_data._tag)
            raise AssertionError()

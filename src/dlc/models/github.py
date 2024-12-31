import logging
from base64 import b64decode
from typing import Literal, Optional

from pydantic import AnyUrl, BaseModel, HttpUrl

_logger = logging.getLogger(__name__)


class GitHubLicenseSimple(BaseModel):
    key: str
    name: str
    url: Optional[HttpUrl]
    spdx_id: Optional[str]
    node_id: str


# https://docs.github.com/ja/rest/licenses/licenses?apiVersion=2022-11-28#get-the-license-for-a-repository
class GitHubLicenseContent(BaseModel):
    _tag: Literal["github"] = "github"
    name: str
    size: int
    url: AnyUrl
    download_url: HttpUrl
    content: str
    encoding: str
    license: GitHubLicenseSimple

    def decode_content(self) -> Optional[bytes]:
        if self.encoding == "base64":
            return b64decode(self.content)
        _logger.warning("Unsupported encoding: %s", self.encoding)
        return None

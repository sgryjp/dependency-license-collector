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

    _decode_content: Optional[bytes] = None

    def decode_content(self) -> Optional[bytes]:
        if self._decode_content is not None:
            return self._decode_content

        if self.encoding == "base64":
            return b64decode(self.content)
        _logger.warning("Unsupported encoding: %s", self.encoding)
        return None


class GitHubTreeItem(BaseModel):
    path: Optional[str] = None
    mode: Optional[str] = None
    type: Optional[str] = None
    sha: Optional[str] = None
    size: Optional[int] = None
    url: Optional[str] = None


class GitHubGitTree(BaseModel):
    sha: str
    url: AnyUrl
    truncated: bool
    tree: list[GitHubTreeItem]

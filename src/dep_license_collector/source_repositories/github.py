import re
from base64 import b64decode

import httpx
import structlog
from pydantic import AnyUrl, BaseModel, HttpUrl
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from dep_license_collector.settings import SETTINGS

log = structlog.get_logger()
_re_github_url = re.compile(r"https?://github.com/([^/]+)/([^/]+)")


class RateLimitError(Exception):
    pass


class GitHubLicenseSimple(BaseModel):
    key: str
    name: str
    url: HttpUrl | None
    spdx_id: str | None
    node_id: str


# https://docs.github.com/ja/rest/licenses/licenses?apiVersion=2022-11-28#get-the-license-for-a-repository
class GitHubLicenseContent(BaseModel):
    name: str
    size: int
    url: AnyUrl
    download_url: HttpUrl
    content: str
    encoding: str
    license: GitHubLicenseSimple

    def decode_content(self) -> bytes | None:
        if self.encoding == "base64":
            return b64decode(self.content)
        else:
            log.warning("Unsupported encoding: %s", self.encoding)
            return None


@retry(
    retry=retry_if_exception_type(),
    wait=wait_exponential_jitter(4, max=64),
    stop=stop_after_attempt(3),
)
def get_license_data(repos_url: str) -> GitHubLicenseContent | None:
    match = _re_github_url.match(repos_url)
    if match is None:
        return None
    owner, repo = match.groups()

    url = f"https://api.github.com/repos/{owner}/{repo}/license"
    headers = _make_headers_for_github_api() | {"accept": "application/vnd.github+json"}
    resp = httpx.get(url, headers=headers)
    if resp.status_code == 403:
        log.warning("Hit rate limit of GitHub API", url=repos_url)
        raise RateLimitError()
    return GitHubLicenseContent.model_validate(resp.json())


def _make_headers_for_github_api() -> dict[str, str]:
    headers = {"X-GitHub-Api-Version": "2022-11-28"}
    if SETTINGS.github_token is not None:
        headers["Authorization"] = f"Bearer {SETTINGS.github_token}"
    return headers

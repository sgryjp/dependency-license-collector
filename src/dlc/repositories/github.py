import logging
import re
from typing import Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from dlc.exceptions import (
    ApiRateLimitError,
    LicenseDataUnavailableError,
)
from dlc.models.github import GitHubLicenseContent
from dlc.settings import SETTINGS

_logger = logging.getLogger(__name__)
_re_github_url = re.compile(r"https?://github.com/([^/]+)/([^/]+)")


@retry(
    retry=retry_if_exception_type(ApiRateLimitError),
    wait=wait_exponential_jitter(4, max=64),
    stop=stop_after_attempt(3),
)
def get_license_data_from_github(
    repos_url: str,
) -> Optional[GitHubLicenseContent]:
    match = _re_github_url.match(repos_url)
    if match is None:
        return None  # Not GitHub
    owner = match.group(1)
    repo = re.sub(r"\.git$", "", match.group(2))

    url = f"https://api.github.com/repos/{owner}/{repo}/license"
    headers = _make_headers_for_github_api() | {"accept": "application/vnd.github+json"}
    _logger.debug("Fetching %s", url)
    resp = httpx.get(url, headers=headers)
    if resp.status_code == 403:
        _logger.warning("Hit rate limit of GitHub API. repos_url=%s", repos_url)
        raise ApiRateLimitError()
    if resp.status_code != 200:
        _logger.warning(
            "Failed to fetch license data of `%s/%s`. repos_url=%s",
            owner,
            repo,
            repos_url,
        )
        raise LicenseDataUnavailableError(repos_url)
    return GitHubLicenseContent.model_validate(resp.json())


def _make_headers_for_github_api() -> dict[str, str]:
    headers = {"X-GitHub-Api-Version": "2022-11-28"}
    if SETTINGS.github_token is not None:
        headers["Authorization"] = f"Bearer {SETTINGS.github_token}"
    return headers

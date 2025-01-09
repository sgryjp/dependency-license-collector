import logging
import re
from collections.abc import Sequence
from typing import Optional, Union

import requests
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from dlc.exceptions import (
    ApiRateLimitError,
    LicenseDataUnavailableError,
)
from dlc.models.github import GitHubGitTree, GitHubLicenseContent
from dlc.settings import SETTINGS

_logger = logging.getLogger(__name__)
_re_github_url = re.compile(r"https?://github.com/([^/]+)/([^/]+)")


@retry(  # Retries on API rate limit error with sleep duration: 4, 8, 16, 32, 64
    retry=retry_if_exception_type(ApiRateLimitError),
    wait=wait_exponential_jitter(initial=4),
    stop=stop_after_attempt(6),
    before_sleep=before_sleep_log(_logger, logging.WARNING),
    reraise=True,
)
def get_license_data_from_github(
    repos_url: str,
) -> Optional[GitHubLicenseContent]:
    owner, repo = _get_owner_and_repo_from_url(repos_url)
    if owner is None or repo is None:
        return None  # Not GitHub

    url = f"https://api.github.com/repos/{owner}/{repo}/license"
    headers = _make_headers_for_github_api() | {"accept": "application/vnd.github+json"}
    _logger.debug("Fetching %s", url)
    resp = requests.get(url, headers=headers, timeout=SETTINGS.timeout)
    if resp.status_code == 403:
        _logger.warning("Hit rate limit of GitHub API. repos_url=%s", repos_url)
        raise ApiRateLimitError()
    elif resp.status_code != 200:
        _logger.warning(
            "Failed to fetch license data of `%s/%s`. status_code=%d repos_url=%s",
            owner,
            repo,
            resp.status_code,
            repos_url,
        )
        raise LicenseDataUnavailableError(resp.status_code, repos_url)
    return GitHubLicenseContent.model_validate(resp.json())


def get_file_list_from_github(
    repos_url: str, sha_list: Sequence[str] = ("main", "master")
) -> Optional[GitHubGitTree]:
    owner, repo = _get_owner_and_repo_from_url(repos_url)
    if owner is None or repo is None:
        return None  # Not GitHub

    for tree_sha in sha_list:
        url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{tree_sha}"
        headers = _make_headers_for_github_api() | {
            "accept": "application/vnd.github+json",
        }
        _logger.debug("Fetching %s", url)
        resp = requests.get(
            url, params={"recursive": "true"}, headers=headers, timeout=SETTINGS.timeout
        )
        if resp.status_code == 404:
            continue
        elif resp.status_code == 403:
            _logger.warning("Hit rate limit of GitHub API. repos_url=%s", repos_url)
            raise ApiRateLimitError()
        elif resp.status_code != 200:
            _logger.warning(
                "Failed to get file list from GitHub. status_code=%d repos_url=%s",
                resp.status_code,
                repos_url,
            )
            raise NotImplementedError()  # TODO: Implement

        return GitHubGitTree.model_validate(resp.json())

    raise NotImplementedError()  # TODO: Implement


def _get_owner_and_repo_from_url(
    repos_url: str,
) -> Union[tuple[str, str], tuple[None, None]]:
    match = _re_github_url.match(repos_url)
    if match is None:
        return None, None  # Not GitHub
    owner = match.group(1)
    repo = re.sub(r"\.git$", "", match.group(2))

    return owner, repo


def _make_headers_for_github_api() -> dict[str, str]:
    headers = {"X-GitHub-Api-Version": "2022-11-28"}
    if SETTINGS.github_token is not None:
        headers["Authorization"] = f"Bearer {SETTINGS.github_token}"
    return headers

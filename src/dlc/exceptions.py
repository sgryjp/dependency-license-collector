"""Package specific exception types."""

from abc import ABC


class DependencyLicenseCollectorError(Exception, ABC):
    """Base class of dependency-license-collector errors."""


class ApiRateLimitError(DependencyLicenseCollectorError):
    """Raised when encountered API rate limit."""


class PackageNotFoundError(DependencyLicenseCollectorError):
    """Raised when the specified package was not found."""

    def __init__(self, registry_name: str, package_name: str, version: str) -> None:
        super().__init__(f"{package_name} {version} was not found in {registry_name}")


class LicenseDataUnavailableError(DependencyLicenseCollectorError):
    """Raised when license data was not available."""

    def __init__(self, hint: str) -> None:
        msg = f"License data not available: {hint}"
        super().__init__(msg)

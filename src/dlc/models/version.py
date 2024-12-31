from typing import Annotated

from pydantic import AfterValidator
from typing_extensions import TypeAlias


def _validate_version_string(version: str) -> str:
    import packaging.version

    try:
        packaging.version.Version(version)
        return version
    except packaging.version.InvalidVersion:
        msg = f"'{version}' is not a valid version string."
        raise ValueError(msg) from None


# TODO: Use packaging.version.Version as the actual type
Version: TypeAlias = Annotated[str, AfterValidator(_validate_version_string)]

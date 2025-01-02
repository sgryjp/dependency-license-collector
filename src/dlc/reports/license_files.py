import logging
from pathlib import Path

from dlc.models.common import Package

_logger = logging.getLogger(__name__)


def generate(outdir: Path, packages: list[Package]) -> None:
    assert outdir.is_dir()

    # Write package data as JSON Lines
    for i, package in enumerate(packages):
        license_file = package.license_file
        if license_file is not None:
            license_file_path = outdir.joinpath(package.name).with_suffix(
                ".txt",
            )
            license_file_path.write_bytes(license_file)
            _logger.debug("(%3d) Wrote %s.", i, license_file_path)
        else:
            _logger.debug("Skip %s %s", package.name, package.version)

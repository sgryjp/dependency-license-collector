import logging
from pathlib import Path

from dlc.models.common import Package

_logger = logging.getLogger(__name__)


def generate(outdir: Path, packages: list[Package]) -> None:
    assert outdir.is_dir()

    # Write package data as JSON Lines
    filepath = outdir.joinpath("license.jsonl")
    with filepath.open("wt", encoding="utf-8") as f:
        f.writelines([pkg.model_dump_json() + "\n" for pkg in packages])
        _logger.info("Wrote %s.", filepath)

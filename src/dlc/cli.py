"""Command line interface."""

import concurrent
import logging
import logging.config
import sys
from concurrent.futures import ThreadPoolExecutor
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import TextIO

import click
import pydantic
import tenacity
from rich.logging import RichHandler
from typing_extensions import assert_never

from dlc.registries.pypi import collect_package_metadata
from dlc.settings import SETTINGS

from .models.common import InputFormat

_logger = logging.getLogger(__name__)


@click.command
@click.option(
    "-f",
    "--format",
    type=click.Choice(["requirements_txt"], case_sensitive=False),
    required=True,
    help="Input data format.",
)
@click.option(
    "-o",
    "--outdir",
    type=click.Path(file_okay=False, writable=True, path_type=Path),
    default=Path(),
    help="Target programming language.",
)
@click.option("-v", "--verbose", is_flag=True, help="Log more verbose message.")
@click.option("-q", "--quiet", is_flag=True, help="Log less verbose message.")
@click.argument("input_file", metavar="FILENAME", type=click.File("rt"))
def main(
    *,
    format: InputFormat,  # noqa: A002
    outdir: Path,
    verbose: bool,
    quiet: bool,
    input_file: TextIO,
) -> None:
    """Create list and download OSS license files.

    Use a special value "-" as FILENAME to read data from standard input.

    For Python, a subset of "requirements.txt" is supported.
    Strictly writing, only the dependency specifier using `==` is supported.
    Example command is: `pip freeze | dlc -l python`.
    """
    _setup_logging(int(verbose) - int(quiet))
    try:
        # Collect package metadata and license data
        if format == "requirements_txt":
            with ThreadPoolExecutor(SETTINGS.max_workers) as executor:
                packages = collect_package_metadata(executor, input_file.readlines())
        else:
            assert_never(format)
        n_packages = len(packages)
        _logger.info("Collected license data of %d packages.", n_packages)

        # Save the result
        outdir.mkdir(parents=True, exist_ok=True)
        license_jsonl_path = outdir.joinpath("license.jsonl")
        with license_jsonl_path.open("wt", encoding="utf-8") as f:
            f.writelines([pkg.model_dump_json() + "\n" for pkg in packages])
            _logger.info("Wrote %s.", license_jsonl_path)
        if n_packages > 0:
            for i, package in enumerate(packages):
                if (license_file := package.license_file) is not None:
                    license_file_path = outdir.joinpath(package.name).with_suffix(
                        ".txt",
                    )
                    license_file_path.write_bytes(license_file)
                    _logger.debug("(%3d) Wrote %s.", i, license_file_path)
                else:
                    _logger.debug("Skip %s %s", package.name, package.version)
    except Exception:
        _logger.exception("Unexpected error")
        sys.exit(1)


def _setup_logging(verbosity: int) -> None:
    level = {-1: logging.WARNING, 1: logging.DEBUG}.get(verbosity, logging.INFO)
    file_formatter = logging.Formatter(
        "%(asctime)s %(levelname)-7s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_formatter.default_msec_format = "%s.%03d"
    file_handler = RotatingFileHandler(
        filename="dlc.log", maxBytes=1024 * 1024, backupCount=1
    )
    file_handler.setFormatter(file_formatter)
    logging.basicConfig(
        format="%(message)s",
        handlers=[
            RichHandler(
                omit_repeated_times=False,
                show_path=False,
                rich_tracebacks=True,
                tracebacks_suppress=[click, concurrent, logging, pydantic, tenacity],
            ),
            file_handler,
        ],
    )
    logging.getLogger(__name__.split(".")[0]).setLevel(level)


if __name__ == "__main__":
    main()

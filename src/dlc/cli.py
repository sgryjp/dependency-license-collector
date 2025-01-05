"""Command line interface."""

import concurrent
import logging
import logging.config
import pathlib
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, TextIO

import click
import jinja2
import pydantic
import tenacity
from click_help_colors import HelpColorsCommand
from rich.logging import RichHandler
from typing_extensions import assert_never

from dlc.models.common import InputFormat
from dlc.registries.pypi import collect_package_metadata
from dlc.reports.html_report import write_html_report
from dlc.reports.report_params import ReportParams
from dlc.settings import SETTINGS

_logger = logging.getLogger(__name__)


@click.command(
    cls=HelpColorsCommand,
    help_headers_color="yellow",
    help_options_color="blue",
)
@click.option(
    "-f",
    "--format",
    type=click.Choice(["requirements_txt"], case_sensitive=False),
    required=True,
    help="Input data format.",
)
@click.option(
    "--target-name",
    metavar="NAME",
    help="Name of the target software project. This will be used in the report.",
)
@click.option(
    "-o",
    "--outdir",
    type=click.Path(file_okay=False, writable=True, path_type=Path),
    default=Path("report"),
    help="Directory to store generated report files.",
)
@click.option("-v", "--verbose", is_flag=True, help="Log more verbose message.")
@click.option("-q", "--quiet", is_flag=True, help="Log less verbose message.")
@click.argument("input_file", metavar="FILENAME", type=click.File("rt"))
def main(  # noqa: PLR0913
    *,
    format: InputFormat,  # noqa: A002
    target_name: Optional[str],
    outdir: Path,
    verbose: bool,
    quiet: bool,
    input_file: TextIO,
) -> None:
    """A tool for collecting dependency licenses in software projects.

    DLC (Dependency License Collector) collects dependency packages' license data,
    download license file content, and generate an HTML report.

    Use a special value "-" as FILENAME to read data from standard input.

    For Python, a subset of "requirements.txt" is supported.
    Strictly writing, only the dependency specifier using `==` is supported.
    Note that majority of project management tools such as Pipenv, Poetry, and
    uv supports exporting list of dependencies in this format.
    """
    _setup_logging(outdir, int(verbose) - int(quiet))

    start_time = datetime.now(tz=timezone.utc)
    try:
        input_content = input_file.read()

        # Collect package metadata and license data
        if format == "requirements_txt":
            with ThreadPoolExecutor(SETTINGS.max_workers) as executor:
                packages = collect_package_metadata(
                    executor, input_content.splitlines()
                )
        else:
            assert_never(format)
            msg = f"Unsupported input format: {format}"
            raise AssertionError(msg)
        n_packages = len(packages)
        _logger.info("Collected license data of %d packages.", n_packages)

        # Save the result
        report_params = ReportParams(
            input_format=format,
            input_source=input_content,
            target_name=target_name,
            outdir=outdir,
            start_time=start_time,
            packages=packages,
        )
        write_html_report(report_params)
    except Exception:
        _logger.exception("Unexpected error")
        sys.exit(1)


def _setup_logging(outdir: Path, verbosity: int) -> None:
    outdir.mkdir(parents=True, exist_ok=True)

    level = {-1: logging.WARNING, 1: logging.DEBUG}.get(verbosity, logging.INFO)
    file_formatter = logging.Formatter(
        "%(asctime)s %(levelname)-7s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_formatter.default_msec_format = "%s.%03d"
    file_handler = RotatingFileHandler(
        filename=outdir.joinpath("dlc.log"), maxBytes=1024 * 1024, backupCount=1
    )
    file_handler.setFormatter(file_formatter)
    logging.basicConfig(
        format="%(message)s",
        handlers=[
            RichHandler(
                omit_repeated_times=False,
                show_path=False,
                rich_tracebacks=True,
                tracebacks_suppress=[
                    click,
                    concurrent,
                    jinja2,
                    logging,
                    pathlib,
                    pydantic,
                    tenacity,
                ],
            ),
            file_handler,
        ],
    )
    logging.getLogger(__name__.split(".")[0]).setLevel(level)


if __name__ == "__main__":
    main()

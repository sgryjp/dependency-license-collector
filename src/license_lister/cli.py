import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TextIO

import click
import structlog
from typing_extensions import assert_never

from license_lister.package_registries.pypi import collect_package_metadata

from .models import Language

log = structlog.get_logger()


@click.command
@click.option(
    "-l",
    "--language",
    type=click.Choice(["python"], case_sensitive=False),
    required=True,
    help="Target programming language.",
)
@click.option(
    "-o",
    "--outdir",
    type=click.Path(file_okay=False, writable=True, path_type=Path),
    default=Path(),
    help="Target programming language.",
)
@click.argument("f", metavar="FILENAME", type=click.File("rt"))
def main(language: Language, outdir: Path, f: TextIO):
    """Create list and download OSS license files.

    Use a special value "-" as FILENAME to read data from standard input.

    For Python, a subset of "requirements.txt" is supported.
    Strictly writing, only the dependency specifier using `==` is supported.
    Example command is: `pip freeze | license-lister -l python`.
    """
    try:
        # Collect package metadata and license data
        if language == "python":
            with ThreadPoolExecutor() as executor:
                packages = collect_package_metadata(executor, f.readlines())
        else:
            assert_never(language)

        # Save the result
        outdir.mkdir(parents=True, exist_ok=True)
        with outdir.joinpath("license.jsonl").open("wt", encoding="utf-8") as f:
            f.writelines([pkg.model_dump_json() + "\n" for pkg in packages])
        for package in packages:
            if package.license is not None and package.license.content is not None:
                outdir.joinpath(package.name).with_suffix(".txt").write_bytes(
                    package.license.content
                )
    except Exception:
        log.exception("Unexpected error")
        sys.exit(1)


if __name__ == "__main__":
    main()

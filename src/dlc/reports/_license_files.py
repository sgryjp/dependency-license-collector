import logging

from dlc.reports.report_params import ReportParams

_logger = logging.getLogger(__name__)


def generate(params: ReportParams) -> None:
    outdir = params.outdir.joinpath("license_files")
    outdir.mkdir(parents=True, exist_ok=True)

    for i, package in enumerate(params.packages):
        license_file = package.license_file
        if license_file is not None:
            license_file_path = outdir.joinpath(package.name).with_suffix(".txt")
            license_file_path.write_bytes(license_file)
            _logger.debug("(%3d) Wrote %s.", i + 1, license_file_path)
        else:
            _logger.debug("(%3d) Skip %s %s", i + 1, package.name, package.version)

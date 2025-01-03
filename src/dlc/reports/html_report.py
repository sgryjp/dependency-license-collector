import logging

from jinja2 import Environment, PackageLoader

from dlc.reports import _license_files
from dlc.reports.report_params import ReportParams

_logger = logging.getLogger(__name__)


def write_html_report(params: ReportParams) -> None:
    params.outdir.mkdir(parents=True, exist_ok=True)

    environment = Environment(loader=PackageLoader("dlc"), autoescape=True)
    template = environment.get_template("index.html")
    rendered = template.render(**params.model_dump())
    params.outdir.joinpath("index.html").write_text(rendered, encoding="utf-8")

    _license_files.generate(params)

    # Generate raw API response from package registry
    outdir = params.outdir.joinpath("registry_data")
    outdir.mkdir(parents=True, exist_ok=True)
    for package in params.packages:
        if package.registry_data is not None:
            filepath = outdir.joinpath(package.name).with_suffix(".json")
            filepath.write_text(
                package.registry_data.model_dump_json(indent=2), encoding="utf-8"
            )
            _logger.debug("Wrote %s.", filepath)

    # Generate raw API response
    outdir = params.outdir.joinpath("registry_data")
    outdir.mkdir(parents=True, exist_ok=True)
    for package in params.packages:
        if package.registry_data is not None:
            filepath = outdir.joinpath(package.name).with_suffix(".json")
            filepath.write_text(
                package.registry_data.model_dump_json(indent=2), encoding="utf-8"
            )
            _logger.debug("Wrote %s.", filepath)

    # Generate machine readable license data in a single file
    filepath = params.outdir.joinpath("license.jsonl")
    with filepath.open("wt", encoding="utf-8") as f:
        f.writelines([pkg.model_dump_json() + "\n" for pkg in params.packages])
    _logger.info("Wrote %s.", filepath)

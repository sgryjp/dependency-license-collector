from datetime import datetime
from pathlib import Path

from jinja2 import Environment, PackageLoader

from dlc.models.common import Package


def generate(outdir: Path, start_time: datetime, packages: list[Package]) -> None:
    assert outdir.is_dir()
    assert start_time.tzinfo is not None

    environment = Environment(loader=PackageLoader("dlc"), autoescape=True)
    template = environment.get_template("report.html")
    rendered = template.render(start_time=start_time, packages=packages)
    outdir.joinpath("report.html").write_text(rendered, encoding="utf-8")

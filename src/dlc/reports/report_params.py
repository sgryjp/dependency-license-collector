import importlib.metadata
from datetime import datetime
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field, computed_field
from typing_extensions import assert_never

from dlc.models.common import InputFormat, Package


class Dlc(BaseModel):
    version: str = Field(
        default=importlib.metadata.version("dependency_license_collector")
    )


class ReportParams(BaseModel):
    dlc: Dlc = Field(default_factory=Dlc)
    input_format: InputFormat
    input_source: str
    outdir: Annotated[Path, lambda p: p.is_dir()]
    start_time: Annotated[datetime, lambda dt: dt.tzinfo is not None]
    packages: list[Package]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def num_failures(self) -> int:
        return sum(package.license_file is None for package in self.packages)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def language(self) -> str:
        if self.input_format == "requirements_txt":
            return "Python"
        else:
            assert_never(self.input_format)
            msg = f"Unsupported input format: {self.input_format}"
            raise AssertionError(msg)

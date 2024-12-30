from concurrent.futures import Executor

import pytest

from dlc.registries.pypi import (
    PyPIPackage,
    collect_package_metadata,
)


@pytest.mark.xfail
def test_can_get_pypi_top100(executor: Executor, pypi_top100: list[PyPIPackage]):
    dependency_specifiers = [f"{p.info.name}=={p.info.version}" for p in pypi_top100]
    dependency_specifiers = dependency_specifiers[:10]  ################################
    packages = collect_package_metadata(executor, dependency_specifiers)
    print(f"{len(packages)=}")  # noqa: T201
    for package in packages:
        assert package.license is not None, f"{package.name} {package.version}"
        assert package.license.content is not None, f"{package.name} {package.version}"
        print(package.license)  # noqa: T201
    pytest.fail("!")  ########################################################

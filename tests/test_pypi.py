from concurrent.futures import Executor

from license_lister.package_registries.pypi import PyPIPackage, collect_package_metadata


def test_can_get_pypi_top100(executor: Executor, pypi_top100: list[PyPIPackage]):
    dependency_specifiers = [f"{p.info.name}=={p.info.version}" for p in pypi_top100]
    dependency_specifiers = dependency_specifiers[:3]
    packages = collect_package_metadata(executor, dependency_specifiers)
    for package in packages:
        assert package.license is not None, f"{package.name} {package.version}"

<!-- markdownlint-disable no-emphasis-as-heading -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Option to show name of the target software in the report
  ([#5](https://github.com/sgryjp/dependency-license-collector/issues/5))
- Support additionally reading environment variables with prefix `DLC_`
  ([#9](https://github.com/sgryjp/dependency-license-collector/issues/9))
- Highlight if failed to get license data or there was no license data available.

### Fixed

- Fail if launched in a different app source tree which uses .env
  ([#7](https://github.com/sgryjp/dependency-license-collector/issues/7))

## [0.1.0] - 2025-01-05

_First release_

[0.1.0]: https://github.com/sgryjp/dependency-license-collector/releases/tag/v0.1.0

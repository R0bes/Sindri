# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions CI/CD workflows
- Support for configuration in `pyproject.toml` under `[tool.sindri]`
- Automatic version tagging workflow
- PyPI release workflow

### Changed
- `pytest` is now called as `python -m pytest` to ensure project modules can be imported

## [0.1.3] - 2024-XX-XX

### Fixed
- Fixed pytest execution to use `python -m pytest` instead of direct `pytest` call
- This ensures project modules (e.g., `hexswitch`) can be imported in `conftest.py`

## [0.1.2] - 2024-XX-XX

### Added
- Initial release

[Unreleased]: https://github.com/yourusername/sindri/compare/v0.1.3...HEAD
[0.1.3]: https://github.com/yourusername/sindri/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/yourusername/sindri/releases/tag/v0.1.2


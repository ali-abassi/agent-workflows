# Changelog

All notable changes to Pi Graph Core are documented here.

The project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed

- Failed durable runs now print the documented `piw resume` remedy instead of
  an internal `run_steps.py` invocation with undocumented flags.
- A run missing its required `--input` now fails before creating a run
  directory instead of leaving an empty `initialized` bundle behind.

### Documentation

- Documented concurrent node dispatch (`workers:`), the run directory
  location, `judge`, `qa`, `cwd`, `preview`, `retry_jitter`,
  `retry_max_delay_seconds`, and the `input.description` requirement.
- Added a positioning comparison (LangGraph/Temporal/Prefect/Make) and a real
  run-bundle evidence sample to the README.

## [0.1.0] - 2026-08-23

Initial public alpha release.

### Added

- Validated YAML DAG authoring contract.
- Command, completion, allowlisted-tool, and agent node runtimes.
- Deterministic gates, typed routing, retries, timeouts, caching, and QA.
- Immutable input and frozen workflow snapshots.
- Atomic run state, append-only trace, one-writer locks, and durable resume.
- Run inspection, ledgers, artifacts, produced files, and per-step Git history.
- `piw` commands for create, validate, graph, run, resume, inspect, configure,
  doctor, and version reporting.
- Zero-cost shell, branching, recovery, and model-backed examples.
- Linux/macOS CI across Python 3.10 and 3.14 with clean-wheel installation.

[0.1.0]: https://github.com/ali-abassi/pi-graph-core/releases/tag/v0.1.0

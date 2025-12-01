# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2025-12-01
### Added
- Initial public release of **Sync Offset Tool**.
- Core functionality to measure audio sync offsets between two MKV files.
- FFT‑based correlation (default mode) for fast performance.
- Direct correlation option with safe worker process and Ctrl+C handling.
- Output reporting of best alignment offset (ms) and peak correlation strength (0–1).
- README with usage instructions, examples, interpretation guide, and troubleshooting.
- MIT License file.
- Requirements file (`numpy`, `scipy`).

### Changed
- Direct correlation prompt threshold lowered to 60 s for safer performance.
- Expanded documentation with multiple examples and practical tips.

---

## [Unreleased]
- Potential support for automatic correction/remuxing of audio tracks.
- Additional language detection and track selection improvements.
- More visualization options for correlation results.

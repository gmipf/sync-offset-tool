# Changelog

All notable changes to this project will be documented in this file.

## [1.3.0] - 2025-12-07
### Added
- Extended container delay detection to cover four flavours:
  - Stream `start_time`
  - `codec_delay` field
  - Tag-based delays (`delay_relative_to_video`, `delay`)
  - Packet timestamp offsets (`first_packet_pts`)
- Prints all non-zero delay fields with clear labels.

### Changed
- Effective offset calculation now subtracts detected container delays, ensuring only the true sync difference remains.
- Delay reporting is consistent across muxing styles:
  - Some tracks use `start_time` or tags.
  - Others (e.g., EAC3) use shifted packet timestamps.

## [1.2.1] - 2025-12-07
### Fixed
- Corrected effective offset calculation: now uses `raw_offset - async_delay + orig_delay` instead of adding delays.

## [1.2.0] - 2025-12-06
### Added
- Detection and reporting of MKV container audio track delays (`start_time` metadata).
- Output includes both raw correlation offset and effective offset (including container delays).
- Clear reporting of container delay values for both original and async tracks.
- Clear error messages when requested language tags are not found in MKV files.

## [1.1.1] - 2025-12-03
### Added
- `--version` option to display the tool’s version string.

### Removed
- `--test` and `--debug` options for simplicity.

## [1.1.0] - 2025-12-03
### Added
- Runtime reporting for both MKV files (formatted as hh:mm:ss.mmm).
- FPS reporting for the primary video stream of both MKV files.

### Changed
- Output section now includes runtime and FPS alongside alignment offset and correlation strength.

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
- Documentation expanded with multiple examples and practical tips.

## [Unreleased]
- Potential support for automatic correction/remuxing of audio tracks.
- Additional language detection and track selection improvements.
- More visualization options for correlation results.

# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-10-20

### Added

- Nine challenge types: `text`, `noise`, `image`, `word`, `math`, `slider`,
  `click`, `pattern`, and `rotate`.
- A typed facade: `Captcha(...)`, `CaptchaConfig`, and `CaptchaResult`.
- Result metadata and assets, including slider piece images and click/pattern
  solution geometry.
- Optional deterministic output through `seed=...`.
- CLI: `captcha-forge list`, `info`, `generate`, and `gallery`, plus
  `python -m captcha_forge`.
- Custom generator registry through `@register` and `BaseGenerator`.
- Fast vectorised mask compositing and a glyph cache.
- Export to PNG, JPEG, GIF, animated WebP, and MP4, plus in-memory PNG/GIF/WebP
  bytes.
- Src-layout packaging with `pyproject.toml`, `py.typed`, bundled word list, and
  a console-script entry point.
- MkDocs Material documentation, examples, gallery generation, benchmark
  script, tests, CI, and PyPI trusted-publishing workflow.

### Changed

- The package is now `captcha-forge` with the import name `captcha_forge`
  (previously `captcha.captcha`).
- `Captcha.generate()` returns `CaptchaResult` instead of a bare frame list.
  The result is sequence-like, so iteration and indexing still work.
- Exporting is explicit: call `result.save(path)` instead of passing export
  settings to the constructor.
- Default animation duration is 3 seconds (previously 10).
- The default foreground text uses a larger, more legible font and background
  glyphs are drawn at a lower opacity.
- Noise rendering reuses a single noise field instead of resizing a large
  texture every frame.

### Fixed

- `color_mode="ligth"` is normalized to `"light"`; the old default silently
  selected the dark theme.
- Output directories are created automatically.
- Zero-size noise viewports no longer divide by zero.
- Text and options are validated with actionable error messages.
- Non-ASCII text is rejected for OpenCV Hershey fonts.

### Removed

- The legacy `captcha/captcha.py` module and the `trial.py` script. See
  [README.md](README.md#migration-from-the-original-module) for the migration
  table.

[1.0.0]: https://github.com/shalonjovan/Captcha/releases/tag/v1.0.0

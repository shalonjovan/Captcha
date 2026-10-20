# Contributing

Thanks for your interest in Captcha Forge. The full contributor guide lives in
[docs/contributing.md](docs/contributing.md).

Quick version:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,docs]"
pytest
ruff check .
ruff format --check .
mkdocs build --strict
```

- Add tests for new behaviour.
- Add documentation for new options or challenge types.
- Use Python 3.9-compatible syntax and formatting.
- Keep runtime dependencies limited to NumPy, headless OpenCV, and Pillow unless
  discussed first.
- Report security issues privately per [SECURITY.md](SECURITY.md).

New challenge types should subclass `BaseGenerator`, register with `@register`,
validate their options, and return a `CaptchaResult` with a clear answer and
metadata. See [docs/extending.md](docs/extending.md).

The release process (versioning, tagging, and PyPI publishing) is documented in
[docs/contributing.md](docs/contributing.md#releasing).

By contributing, you agree that your contributions are licensed under the MIT
License.

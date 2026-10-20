# Contributing

Thanks for helping improve Captcha Forge. This project aims to keep a small,
typed API and a fast, portable renderer.

## Development setup

```bash
git clone https://github.com/shalonjovan/Captcha.git
cd Captcha
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,docs]"
```

On Windows, use `.venv\Scripts\activate`.

## Checks

```bash
pytest
ruff check .
ruff format --check .
mkdocs build --strict
python -m build
twine check dist/*
```

Run the full suite before opening a pull request. New behaviour should include
tests and documentation.

## Code style

- Python 3.9+ syntax and typing.
- Format with `ruff format`; lint with `ruff check`.
- Keep lines readable (the formatter is configured for 100 columns).
- Prefer small, composable rendering helpers over large generator methods.
- Do not add a runtime dependency without discussing it first. The core
  dependencies are NumPy, headless OpenCV, and Pillow.

## Adding a challenge type

1. Create a module under `src/captcha_forge/generators/`.
2. Subclass `BaseGenerator` and decorate it with `@register`.
3. Declare `name`, `description`, `default_size`, `default_format`, and
   `option_defaults`; add human-readable `option_docs`.
4. Validate option values in `_validate_options`.
5. Use `self.rng` / `self.np_rng` so `seed` remains deterministic.
6. Return `self._result(...)` with a meaningful `answer`, `text`, `metadata`,
   and `assets` where applicable.
7. Export the class from `generators/__init__.py`.
8. Add tests covering frame shape, answer format, metadata, and determinism.
9. Add a section to `docs/captcha-types.md` and regenerate the gallery with
   `python scripts/generate_gallery.py`.
10. Update `README.md` and `CHANGELOG.md` if the public surface changes.

See [Extending Captcha Forge](https://shalonjovan.github.io/Captcha/extending/)
for a complete example.

## Documentation

The docs are Markdown under `docs/` with MkDocs Material and mkdocstrings.
Docstrings should use Google style. Build with:

```bash
mkdocs serve
```

## Commits and pull requests

- Keep commits focused and describe the user-visible change.
- Include a migration note for breaking API changes.
- Link the issue being fixed.
- Do not include generated images unless they are documentation assets.
- Be respectful and constructive in reviews.

## Security issues

Do not open a public issue for a vulnerability. Follow
[SECURITY.md](https://github.com/shalonjovan/Captcha/blob/main/SECURITY.md).

## License

By contributing, you agree that your contributions are licensed under the MIT
License.

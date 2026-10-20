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

## Releasing

1. Bump the version in `pyproject.toml` and add a `CHANGELOG.md` entry.
2. Commit, tag, and push:

   ```bash
   git tag -a v1.2.3 -m "Release 1.2.3"
   git push origin main --tags
   ```

3. Create a GitHub release for the tag. The `Publish` workflow then builds the
   distributions and uploads them to PyPI with trusted publishing.
4. Trusted publishing needs a publisher entry in the PyPI account
   (`shalonjovan`) that trusts:
   - repository `shalonjovan/Captcha`,
   - workflow `publish.yml`,
   - environment `pypi`.

   For a brand-new project, register it as a **pending** publisher on the PyPI
   account page; the first successful publish creates the project.
5. If OIDC is unavailable, add a `PYPI_API_TOKEN` repository secret and run the
   `Publish (API token)` workflow manually.

The documentation site is published by the `Docs` workflow to
<https://shalonjovan.github.io/Captcha/> on every push to `main` that touches
the documentation or the package.

## Security issues

Do not open a public issue for a vulnerability. Follow
[SECURITY.md](https://github.com/shalonjovan/Captcha/blob/main/SECURITY.md).

## License

By contributing, you agree that your contributions are licensed under the MIT
License.

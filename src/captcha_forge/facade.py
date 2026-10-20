"""High-level facade for creating CAPTCHA challenges."""

from __future__ import annotations

import dataclasses
from typing import Any, Dict

from .config import CaptchaConfig
from .registry import available_types, get_generator_class, resolve_type
from .result import CaptchaResult


class Captcha:
    """Create and render a CAPTCHA challenge.

    Parameters
    ----------
    captcha_type:
        One of the registered type names, for example ``"text"``, ``"noise"``,
        ``"image"``, ``"math"``, ``"word"``, ``"slider"``, ``"click"``,
        ``"pattern"``, or ``"rotate"``.
    config:
        An optional :class:`~captcha_forge.config.CaptchaConfig`. Keyword
        arguments override individual fields.
    **kwargs:
        Common configuration fields and type-specific options. Unknown options
        are rejected with a helpful error.

    Examples
    --------
    >>> from captcha_forge import Captcha
    >>> result = Captcha("image", seed=42, length=5).generate()
    >>> result.answer  # doctest: +SKIP
    'K7M2Q'
    >>> result.save("challenge.png")  # doctest: +SKIP
    PosixPath('challenge.png')
    """

    def __init__(
        self,
        captcha_type: str = "text",
        *,
        config: CaptchaConfig | None = None,
        **kwargs: Any,
    ) -> None:
        self.captcha_type = resolve_type(captcha_type)
        self.generator_class = get_generator_class(self.captcha_type)
        if config is None:
            self.config = CaptchaConfig.from_kwargs(kwargs)
        else:
            if not isinstance(config, CaptchaConfig):
                raise TypeError("config must be a CaptchaConfig instance or None")
            fields = {field.name for field in dataclasses.fields(CaptchaConfig)} - {"options"}
            common = {key: value for key, value in kwargs.items() if key in fields}
            extra = {key: value for key, value in kwargs.items() if key not in fields}
            options = dict(config.options)
            options.update(extra)
            self.config = config.replace(options=options, **common)
        self.options = dict(self.config.options)
        self.generator_class.validate_option_names(self.options)

    def generate(self) -> CaptchaResult:
        """Render one challenge and return a :class:`~captcha_forge.result.CaptchaResult`."""

        generator = self.generator_class(self.config, **self.config.options)
        return generator.generate()

    @classmethod
    def available_types(cls) -> Dict[str, str]:
        """Return ``{name: description}`` for every registered generator."""

        return available_types()

    @classmethod
    def describe(cls, captcha_type: str) -> Dict[str, Any]:
        """Return metadata and supported options for one type."""

        generator_class = get_generator_class(captcha_type)
        return {
            "name": generator_class.name,
            "description": generator_class.description,
            "default_size": generator_class.default_size,
            "default_format": generator_class.default_format,
            "animated": generator_class.animated,
            "options": generator_class.describe_options(),
        }

    def __repr__(self) -> str:
        width, height = self.config.resolved_size(self.generator_class.default_size)
        return f"Captcha(type={self.captcha_type!r}, size={width}x{height})"


def create(captcha_type: str = "text", **kwargs: Any) -> CaptchaResult:
    """One-shot convenience wrapper around :class:`Captcha`.

    >>> from captcha_forge import create
    >>> result = create("math", seed=7)  # doctest: +SKIP
    """

    return Captcha(captcha_type, **kwargs).generate()


__all__ = ["Captcha", "create"]

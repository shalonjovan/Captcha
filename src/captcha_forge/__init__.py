"""Captcha Forge: a modern, extensible CAPTCHA generator.

The package exposes a small facade plus a registry for custom generators::

    from captcha_forge import Captcha

    result = Captcha("text", seed=42, duration=2).generate()
    print(result.answer)
    result.save("challenge.gif")

See the documentation for all nine built-in challenge types, configuration
options, and extension points.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

# Importing the built-in generators populates the registry as a side effect.
from . import generators as _generators  # noqa: E402,F401
from .config import DEFAULT_ALPHABET, CaptchaConfig
from .exceptions import (
    CaptchaError,
    ConfigurationError,
    ExportError,
    GeneratorError,
    UnknownCaptchaType,
)
from .facade import Captcha, create
from .registry import available_types, get_generator_class, register, resolve_type
from .result import CaptchaResult

try:
    __version__ = version("captcha-forge")
except PackageNotFoundError:  # pragma: no cover - source checkout without installation
    __version__ = "1.0.0"

__all__ = [
    "Captcha",
    "CaptchaConfig",
    "CaptchaError",
    "CaptchaResult",
    "ConfigurationError",
    "DEFAULT_ALPHABET",
    "ExportError",
    "GeneratorError",
    "UnknownCaptchaType",
    "__version__",
    "available_types",
    "create",
    "get_generator_class",
    "register",
    "resolve_type",
]

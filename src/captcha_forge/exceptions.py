"""Exception hierarchy for :mod:`captcha_forge`."""

from __future__ import annotations


class CaptchaError(Exception):
    """Base class for every error raised by Captcha Forge."""


class ConfigurationError(CaptchaError, ValueError):
    """Raised when a configuration value or generator option is invalid."""


class UnknownCaptchaType(CaptchaError, ValueError):
    """Raised when a requested CAPTCHA type is not registered."""


class ExportError(CaptchaError, RuntimeError):
    """Raised when frames cannot be encoded or written to disk."""


class GeneratorError(CaptchaError, RuntimeError):
    """Raised when a generator cannot produce a challenge."""

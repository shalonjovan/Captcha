"""Built-in CAPTCHA generators.

Importing this package registers every built-in generator in the global
registry. Plugin authors can subclass :class:`~captcha_forge.generators.base.BaseGenerator`
and decorate the class with :func:`~captcha_forge.registry.register`.
"""

from __future__ import annotations

from .base import BaseGenerator
from .click import ClickCaptcha
from .image import ImageCaptcha
from .math import MathCaptcha
from .noise import NoiseCaptcha
from .pattern import PatternCaptcha
from .rotate import RotateCaptcha
from .slider import SliderCaptcha
from .text import TextCaptcha
from .word import WordCaptcha

__all__ = [
    "BaseGenerator",
    "ClickCaptcha",
    "ImageCaptcha",
    "MathCaptcha",
    "NoiseCaptcha",
    "PatternCaptcha",
    "RotateCaptcha",
    "SliderCaptcha",
    "TextCaptcha",
    "WordCaptcha",
]

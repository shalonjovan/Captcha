"""Shared test helpers."""

from __future__ import annotations

from typing import Any, Dict

import pytest

from captcha_forge import Captcha, available_types

CAPTCHA_TYPES = sorted(available_types())


def fast_kwargs(captcha_type: str, **overrides: Any) -> Dict[str, Any]:
    """Small, fast settings for the animated generators."""

    info = Captcha.describe(captcha_type)
    kwargs: Dict[str, Any] = {"seed": 1234}
    if info["animated"]:
        kwargs.update({"duration": 0.2, "fps": 5})
    kwargs.update(overrides)
    return kwargs


@pytest.fixture()
def quick_generate():
    def generate(captcha_type: str, **overrides: Any):
        return Captcha(captcha_type, **fast_kwargs(captcha_type, **overrides)).generate()

    return generate

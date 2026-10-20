"""Configuration and validation tests."""

from __future__ import annotations

import pytest

from captcha_forge import Captcha, CaptchaConfig, ConfigurationError
from captcha_forge.fonts import FONT_FACES


def test_defaults_and_legacy_aliases() -> None:
    config = CaptchaConfig.from_kwargs(
        {
            "frame_size": (320, 120),
            "captcha_text": "ABC123",
            "font": "simplex",
            "color_mode": "ligth",
            "max_rotation": 20,
        }
    )
    assert config.width == 320
    assert config.height == 120
    assert config.text == "ABC123"
    assert config.font_face == FONT_FACES["simplex"]
    assert config.color_mode == "light"
    assert config.options["max_rotation"] == 20


def test_custom_colours_require_both_values() -> None:
    with pytest.raises(ConfigurationError):
        CaptchaConfig(color_mode="custom", background="white")


def test_custom_colours_are_accepted() -> None:
    config = CaptchaConfig(
        color_mode="custom",
        background="#101820",
        foreground=(240, 240, 240),
    )
    assert config.color_mode == "custom"


def test_invalid_dimensions() -> None:
    with pytest.raises(ConfigurationError):
        CaptchaConfig(width=10)


def test_invalid_fps_and_duration() -> None:
    with pytest.raises(ConfigurationError):
        CaptchaConfig(fps=0)
    with pytest.raises(ConfigurationError):
        CaptchaConfig(duration=0)


def test_invalid_text() -> None:
    with pytest.raises(ConfigurationError):
        CaptchaConfig(text="")
    with pytest.raises(ConfigurationError):
        CaptchaConfig(text="HÉLLO")


def test_unknown_generator_option_has_helpful_message() -> None:
    with pytest.raises(ConfigurationError) as error:
        Captcha("text", does_not_exist=True)
    message = str(error.value)
    assert "does_not_exist" in message
    assert "Supported options" in message


def test_option_validation() -> None:
    with pytest.raises(ConfigurationError):
        Captcha("text", min_spacing=10, max_spacing=1).generate()
    with pytest.raises(ConfigurationError):
        Captcha("click", target_count=0).generate()
    with pytest.raises(ConfigurationError):
        Captcha("pattern", grid=9).generate()
    with pytest.raises(ConfigurationError):
        Captcha("rotate", direction="sideways").generate()


def test_empty_alphabet() -> None:
    with pytest.raises(ConfigurationError):
        CaptchaConfig(alphabet="")


def test_config_replace_revalidates() -> None:
    config = CaptchaConfig()
    with pytest.raises(ConfigurationError):
        config.replace(fps=0)

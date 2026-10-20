"""Package-level API tests."""

from __future__ import annotations

import pytest

from captcha_forge import (
    Captcha,
    CaptchaConfig,
    CaptchaResult,
    UnknownCaptchaType,
    __version__,
    available_types,
    create,
    get_generator_class,
    resolve_type,
)
from captcha_forge.generators import (
    ClickCaptcha,
    ImageCaptcha,
    MathCaptcha,
    NoiseCaptcha,
    PatternCaptcha,
    RotateCaptcha,
    SliderCaptcha,
    TextCaptcha,
    WordCaptcha,
)

EXPECTED_TYPES = {
    "click",
    "image",
    "math",
    "noise",
    "pattern",
    "rotate",
    "slider",
    "text",
    "word",
}


def test_version_is_a_string() -> None:
    assert isinstance(__version__, str)
    assert __version__


def test_available_types() -> None:
    types = available_types()
    assert set(types) == EXPECTED_TYPES
    assert all(description for description in types.values())


def test_generator_classes_are_registered() -> None:
    classes = [
        ClickCaptcha,
        ImageCaptcha,
        MathCaptcha,
        NoiseCaptcha,
        PatternCaptcha,
        RotateCaptcha,
        SliderCaptcha,
        TextCaptcha,
        WordCaptcha,
    ]
    for cls in classes:
        assert get_generator_class(cls.name) is cls
        assert Captcha.describe(cls.name)["name"] == cls.name


def test_type_aliases() -> None:
    assert resolve_type("arithmetic") == "math"
    assert resolve_type("puzzle") == "slider"
    assert resolve_type("Words") == "word"


def test_unknown_type_raises() -> None:
    with pytest.raises(UnknownCaptchaType):
        Captcha("does-not-exist")


def test_create_convenience() -> None:
    result = create("image", seed=1)
    assert isinstance(result, CaptchaResult)
    assert result.captcha_type == "image"
    assert result.answer


def test_captcha_config_object_is_merged() -> None:
    config = CaptchaConfig(seed=2, color_mode="dark")
    result = Captcha("image", config=config, length=4).generate()
    assert result.metadata["seed"] == 2
    assert result.metadata["color_mode"] == "dark"
    assert result.text is not None
    assert len(result.text) == 4


def test_describe_contains_options() -> None:
    info = Captcha.describe("text")
    assert info["animated"] is True
    assert info["default_format"] == "gif"
    names = {option["name"] for option in info["options"]}
    assert {"max_rotation", "bg_spawn_rate", "fg_wave_amplitude"} <= names


def test_repr() -> None:
    captcha = Captcha("text", width=320, height=120)
    assert "text" in repr(captcha)
    assert "320" in repr(captcha)

"""Rendering primitive tests."""

from __future__ import annotations

import numpy as np
import pytest

from captcha_forge.colors import blend, parse_color, to_bgr
from captcha_forge.config import CaptchaConfig
from captcha_forge.exceptions import ConfigurationError
from captcha_forge.export import encode_animation_bytes, normalise_format
from captcha_forge.fonts import FONT_FACES, fit_font_scale, measure_text, resolve_font_face
from captcha_forge.rendering import (
    GlyphCache,
    add_noise,
    apply_wave,
    blit_image_mask,
    blit_mask,
    blit_mask_onto,
    draw_shape,
    make_gradient,
    make_puzzle_mask,
    new_frame,
    rotate_mask,
    shape_points,
)
from captcha_forge.theme import resolve_theme


def test_new_frame_shape_and_colour() -> None:
    frame = new_frame(20, 10, (255, 0, 0))
    assert frame.shape == (10, 20, 3)
    assert tuple(frame[0, 0]) == (0, 0, 255)


def test_blit_mask_opaque_and_alpha() -> None:
    frame = new_frame(10, 10, (0, 0, 0))
    mask = np.full((4, 4), 255, dtype=np.uint8)
    blit_mask(frame, mask, (255, 0, 0), 3, 3)
    assert tuple(frame[4, 4]) == (0, 0, 255)

    half = new_frame(10, 10, (0, 0, 0))
    blit_mask(half, mask, (255, 255, 255), 3, 3, alpha=0.5)
    assert 120 <= int(half[4, 4, 0]) <= 135


def test_blit_mask_clips_negative_coordinates() -> None:
    frame = new_frame(5, 5, (0, 0, 0))
    mask = np.full((4, 4), 255, dtype=np.uint8)
    blit_mask(frame, mask, (0, 255, 0), -2, -2)
    assert tuple(frame[0, 0]) == (0, 255, 0)
    assert tuple(frame[3, 3]) == (0, 0, 0)


def test_blit_image_mask() -> None:
    frame = new_frame(10, 10, (0, 0, 0))
    image = np.full((4, 4, 3), (0, 0, 255), dtype=np.uint8)
    mask = np.full((4, 4), 255, dtype=np.uint8)
    blit_image_mask(frame, image, mask, 2, 2)
    assert tuple(frame[3, 3]) == (0, 0, 255)


def test_blit_mask_onto_uses_maximum() -> None:
    target = np.zeros((10, 10), dtype=np.uint8)
    blit_mask_onto(target, np.full((4, 4), 100, dtype=np.uint8), 2, 2)
    blit_mask_onto(target, np.full((4, 4), 200, dtype=np.uint8), 2, 2)
    assert target[3, 3] == 200


def test_apply_wave_keeps_shape() -> None:
    image = np.zeros((30, 40), dtype=np.uint8)
    image[10:20, 10:30] = 255
    waved = apply_wave(image, 3.0, 12.0, phase=0.5)
    assert waved.shape == image.shape
    assert waved.dtype == np.uint8
    assert waved.max() > 0


def test_rotate_mask_expands_canvas() -> None:
    mask = np.zeros((10, 20), dtype=np.uint8)
    mask[2:8, 4:16] = 255
    rotated = rotate_mask(mask, 45)
    assert rotated.shape[0] > mask.shape[0]
    assert rotated.shape[1] > mask.shape[1]


def test_make_puzzle_mask() -> None:
    rng = np.random.default_rng(1)
    mask = make_puzzle_mask(60, 8, rng)
    assert mask.ndim == 2
    assert mask.min() == 0
    assert mask.max() == 255
    assert int((mask > 0).sum()) > 0


def test_colours() -> None:
    assert parse_color("#ff0000") == (255, 0, 0)
    assert parse_color("#f00") == (255, 0, 0)
    assert parse_color("red")[0] > 150
    assert parse_color((1, 2, 3)) == (1, 2, 3)
    with pytest.raises(ConfigurationError):
        parse_color("not-a-colour")
    with pytest.raises(ConfigurationError):
        parse_color((0, 0, 300))
    assert blend((0, 0, 0), (255, 255, 255), 0.5) == (128, 128, 128)
    assert to_bgr((1, 2, 3)) == (3, 2, 1)


def test_fonts_and_glyph_cache() -> None:
    assert resolve_font_face("duplex") == FONT_FACES["duplex"]
    with pytest.raises(ConfigurationError):
        resolve_font_face("not-a-font")
    width, height, baseline = measure_text("ABC", FONT_FACES["duplex"], 1.0, 2)
    assert width > 0 and height > 0 and baseline >= 0
    fitted = fit_font_scale("A VERY LONG STRING", FONT_FACES["duplex"], 2.0, 2, 80, 40)
    assert 0 < fitted < 2.0
    cache = GlyphCache(FONT_FACES["duplex"], 1.0, 2)
    first = cache.get("A", rotation=10)
    second = cache.get("A", rotation=10)
    assert first is second
    assert first.ndim == 2


def test_theme_resolution() -> None:
    light = resolve_theme(CaptchaConfig(color_mode="light"))
    dark = resolve_theme(CaptchaConfig(color_mode="dark"))
    assert not light.is_dark
    assert dark.is_dark
    assert light.background != dark.background
    custom = resolve_theme(
        CaptchaConfig(color_mode="custom", background="#101010", foreground="#eeeeee")
    )
    assert custom.background == (16, 16, 16)
    assert custom.foreground == (238, 238, 238)


def test_theme_colour_overrides_apply_to_light_and_dark_modes() -> None:
    overridden = resolve_theme(
        CaptchaConfig(color_mode="light", background="#101010", foreground="#eeeeee")
    )
    assert overridden.background == (16, 16, 16)
    assert overridden.foreground == (238, 238, 238)
    assert overridden.is_dark
    assert overridden.muted == blend((16, 16, 16), (238, 238, 238), 0.34)


@pytest.mark.parametrize(
    "shape,count",
    [("square", 4), ("triangle", 3), ("diamond", 4), ("star", 10), ("hexagon", 6)],
)
def test_shape_points(shape: str, count: int) -> None:
    points = shape_points(shape, (50, 50), 20, angle=15)
    assert len(points) == count


def test_draw_shape_modifies_frame() -> None:
    frame = new_frame(60, 60, (255, 255, 255))
    draw_shape(frame, "circle", (30, 30), 20, (255, 0, 0), outline=(0, 0, 0))
    assert tuple(frame[30, 30]) != (255, 255, 255)


def test_add_noise() -> None:
    frame = np.zeros((20, 20, 3), dtype=np.uint8)
    add_noise(frame, 0.2, np.random.default_rng(1))
    assert frame.max() > 0


def test_gradient() -> None:
    frame = make_gradient(20, 10, (255, 255, 255), (0, 0, 0))
    assert frame.shape == (10, 20, 3)
    assert frame[0, 0].mean() > frame[-1, 0].mean()


def test_export_helpers() -> None:
    assert normalise_format("JPG") == "jpeg"
    assert normalise_format(".gif") == "gif"
    frames = [np.zeros((8, 8, 3), dtype=np.uint8), np.ones((8, 8, 3), dtype=np.uint8) * 255]
    data = encode_animation_bytes(frames, fps=10, format="gif")
    assert data.startswith(b"GIF8")

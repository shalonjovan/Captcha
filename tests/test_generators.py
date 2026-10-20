"""Behavioural tests for every built-in generator."""

from __future__ import annotations

import numpy as np
import pytest

from captcha_forge import Captcha, available_types

TYPES = sorted(available_types())


@pytest.mark.parametrize("captcha_type", TYPES)
def test_every_generator_produces_valid_frames(quick_generate, captcha_type: str) -> None:
    result = quick_generate(captcha_type)
    assert result.captcha_type == captcha_type
    assert len(result) >= 1
    assert result.answer is not None
    width, height = result.size
    assert width >= 32 and height >= 32
    assert result.metadata["width"] == width
    assert result.metadata["height"] == height
    for frame in result:
        assert frame.dtype == np.uint8
        assert frame.shape == (height, width, 3)


def test_text_challenge(quick_generate) -> None:
    result = quick_generate("text", text="HELLO", duration=0.4, fps=10)
    assert result.text == "HELLO"
    assert result.answer == "HELLO"
    assert len(result) == 4
    assert result.suggested_format == "gif"


def test_noise_challenge(quick_generate) -> None:
    result = quick_generate("noise", text="NOISE", duration=0.4, fps=10)
    assert result.text == "NOISE"
    assert result.answer == "NOISE"
    assert len(result) == 4


def test_noise_grain_changes_texture() -> None:
    fine = Captcha("noise", text="ABC", seed=7, duration=0.2, fps=5, grain=1).generate()
    blocky = Captcha("noise", text="ABC", seed=7, duration=0.2, fps=5, grain=4).generate()
    assert not np.array_equal(fine.image, blocky.image)


def test_image_challenge(quick_generate) -> None:
    result = quick_generate("image", text="ABCD")
    assert result.text == "ABCD"
    assert result.answer == "ABCD"
    assert len(result) == 1
    assert result.suggested_format == "png"


def test_word_challenge(quick_generate) -> None:
    result = quick_generate("word")
    assert result.answer == result.text
    assert result.answer.isalpha()
    assert result.answer.isupper()
    assert 4 <= len(result.answer) <= 8
    assert result.metadata["wordlist_size"] > 0


def test_word_custom_list(quick_generate) -> None:
    result = quick_generate("word", wordlist=["tiger", "zebra"], min_length=4, max_length=5)
    assert result.answer in {"TIGER", "ZEBRA"}


def test_math_answer_matches_expression(quick_generate) -> None:
    for _ in range(10):
        result = quick_generate("math", min_operand=1, max_operand=9, operands=3)
        assert result.text is not None
        assert result.text.endswith(" = ?")
        expression = result.text[: -len(" = ?")]
        value = eval(expression, {"__builtins__": {}}, {})  # noqa: S307 - test-only, restricted input
        assert int(result.answer) == value


def test_math_custom_expression_has_no_answer(quick_generate) -> None:
    result = quick_generate("math", text="2 + 3 = ?")
    assert result.text == "2 + 3 = ?"
    assert result.answer is None


def test_slider_metadata(quick_generate) -> None:
    result = quick_generate("slider")
    target_x = result.answer
    gap_x, gap_y, gap_w, gap_h = result.metadata["gap_box"]
    assert target_x == gap_x
    assert 0 <= gap_x <= result.size[0] - gap_w
    assert 0 <= gap_y <= result.size[1] - gap_h
    piece = result.assets["piece"]
    assert piece.ndim == 3 and piece.shape[2] == 4
    assert result.metadata["tolerance"] >= 0


def test_slider_fixed_target(quick_generate) -> None:
    result = quick_generate("slider", target_x=200, gap_y=100)
    assert result.answer == 200
    assert result.metadata["gap_y"] == 100


def test_click_metadata(quick_generate) -> None:
    result = quick_generate("click", target_count=2, decoy_count=4)
    targets = result.metadata["targets"]
    assert len(result.answer) == 2
    assert len(targets) == 2
    assert result.metadata["target_shape"] in {"circle", "square", "triangle", "diamond", "star"}
    assert result.metadata["target_color"] in {"red", "blue", "green", "orange", "purple"}
    for x, y in result.answer:
        assert 0 <= x <= result.size[0]
        assert 0 <= y <= result.size[1]


def test_click_fixed_target(quick_generate) -> None:
    result = quick_generate(
        "click",
        shapes=("circle", "square"),
        colors=("red", "blue"),
        target_shape="circle",
        target_color="red",
        target_count=2,
        decoy_count=2,
    )
    assert result.metadata["instruction"] == "Click every red circle"
    assert all(target["shape"] == "circle" for target in result.metadata["targets"])
    assert all(target["color"] == "red" for target in result.metadata["targets"])


def test_pattern_sequence(quick_generate) -> None:
    result = quick_generate("pattern", grid=3, path_length=5)
    assert len(result.answer) == 5
    indices = result.metadata["answer_indices"]
    labels = result.metadata["labels"]
    assert labels == sorted(labels)
    nodes = {node["index"]: node for node in result.metadata["nodes"]}
    for index, (x, y) in zip(indices, result.answer):
        assert (nodes[index]["x"], nodes[index]["y"]) == (x, y)
        assert nodes[index]["selected"] is True


def test_rotate_answer(quick_generate) -> None:
    result = quick_generate("rotate", direction="up")
    assert 0 <= result.answer < 360
    angle = result.metadata["angle"]
    target = result.metadata["target_angle"]
    assert result.answer == round((target - angle) % 360.0, 1)
    assert result.metadata["direction"] == "up"


def test_reproducible_with_seed() -> None:
    first = Captcha("text", seed=99, duration=0.4, fps=10).generate()
    second = Captcha("text", seed=99, duration=0.4, fps=10).generate()
    assert len(first) == len(second)
    assert all(np.array_equal(a, b) for a, b in zip(first, second))


def test_different_seeds_differ() -> None:
    first = Captcha("image", seed=1).generate()
    second = Captcha("image", seed=2).generate()
    assert not np.array_equal(first.image, second.image)


def test_light_dark_and_custom_themes() -> None:
    light = Captcha("image", seed=5, color_mode="light").generate()
    dark = Captcha("image", seed=5, color_mode="dark").generate()
    custom = Captcha(
        "image",
        seed=5,
        color_mode="custom",
        background="#fff4e0",
        foreground="#223344",
    ).generate()
    assert not np.array_equal(light.image, dark.image)
    assert not np.array_equal(light.image, custom.image)


def test_frame_size_and_option_passthrough() -> None:
    result = Captcha(
        "text",
        seed=3,
        duration=0.2,
        fps=5,
        frame_size=(320, 120),
        max_rotation=0,
        min_spacing=0,
        max_spacing=0,
    ).generate()
    assert result.size == (320, 120)
    assert result.metadata["font_scale"] > 0


def test_alias_generates_math(quick_generate) -> None:
    result = quick_generate("arithmetic")
    assert result.captcha_type == "math"
    assert result.answer is not None

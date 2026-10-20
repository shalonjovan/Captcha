"""Colour parsing and small colour helpers.

Public colour values use RGB triples or hexadecimal strings. OpenCV frames use
BGR internally; conversion happens at the rendering boundary.
"""

from __future__ import annotations

import re
from typing import Sequence, Tuple, Union

from .exceptions import ConfigurationError

RGB = Tuple[int, int, int]
ColorLike = Union[str, Sequence[int]]

_HEX_RE = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

COLOR_NAMES = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "red": (220, 50, 50),
    "green": (40, 160, 90),
    "blue": (45, 90, 220),
    "yellow": (240, 200, 40),
    "orange": (240, 140, 40),
    "purple": (135, 80, 200),
    "pink": (235, 105, 160),
    "teal": (30, 155, 155),
    "cyan": (40, 190, 220),
    "magenta": (205, 60, 180),
    "gray": (128, 128, 128),
    "grey": (128, 128, 128),
    "silver": (190, 190, 195),
    "navy": (30, 45, 110),
    "lime": (130, 200, 50),
    "brown": (140, 90, 55),
    "gold": (215, 170, 45),
}


def parse_color(value: ColorLike, name: str = "color") -> RGB:
    """Parse a colour into an ``(r, g, b)`` tuple.

    Parameters
    ----------
    value:
        A named colour (``"tomato"`` is not supported), a hex string such as
        ``"#ff8800"``, or a sequence of three integers in ``0..255``.
    name:
        Used in error messages.

    Raises
    ------
    ConfigurationError
        If the value is not a valid colour.
    """

    if isinstance(value, str):
        text = value.strip().lower()
        if text in COLOR_NAMES:
            return COLOR_NAMES[text]
        match = _HEX_RE.match(text)
        if match:
            digits = match.group(1)
            if len(digits) == 3:
                digits = "".join(ch * 2 for ch in digits)
            return (
                int(digits[0:2], 16),
                int(digits[2:4], 16),
                int(digits[4:6], 16),
            )
        raise ConfigurationError(
            f"{name} must be a colour name, a hex string such as '#1a2b3c', "
            f"or an (r, g, b) tuple; got {value!r}"
        )

    if isinstance(value, (tuple, list)) and len(value) == 3:
        try:
            channels = tuple(int(channel) for channel in value)
        except (TypeError, ValueError) as exc:
            raise ConfigurationError(f"{name} channels must be integers") from exc
        if any(channel < 0 or channel > 255 for channel in channels):
            raise ConfigurationError(f"{name} channels must be between 0 and 255")
        return channels  # type: ignore[return-value]

    raise ConfigurationError(
        f"{name} must be a colour name, a hex string, or an (r, g, b) tuple; got {value!r}"
    )


def to_bgr(color: RGB) -> Tuple[int, int, int]:
    """Convert an RGB tuple to OpenCV's BGR order."""

    return (color[2], color[1], color[0])


def blend(first: RGB, second: RGB, amount: float) -> RGB:
    """Linearly blend two colours. ``amount=0`` returns ``first``."""

    amount = max(0.0, min(1.0, amount))
    return tuple(  # type: ignore[return-value]
        int(round(a + (b - a) * amount)) for a, b in zip(first, second)
    )


def luminance(color: RGB) -> float:
    """Return perceptual luminance in the range ``0..1``."""

    r, g, b = color
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0


def contrasting_text(
    background: RGB, light: RGB = (255, 255, 255), dark: RGB = (20, 20, 24)
) -> RGB:
    """Pick a readable text colour for a background."""

    return dark if luminance(background) > 0.55 else light

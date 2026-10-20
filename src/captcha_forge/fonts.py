"""OpenCV Hershey font helpers."""

from __future__ import annotations

from typing import Dict, Tuple, Union

import cv2

from .exceptions import ConfigurationError

FontLike = Union[int, str]

FONT_FACES: Dict[str, int] = {
    "simplex": cv2.FONT_HERSHEY_SIMPLEX,
    "plain": cv2.FONT_HERSHEY_PLAIN,
    "duplex": cv2.FONT_HERSHEY_DUPLEX,
    "complex": cv2.FONT_HERSHEY_COMPLEX,
    "triplex": cv2.FONT_HERSHEY_TRIPLEX,
    "complex_small": cv2.FONT_HERSHEY_COMPLEX_SMALL,
    "script_simplex": cv2.FONT_HERSHEY_SCRIPT_SIMPLEX,
    "script_complex": cv2.FONT_HERSHEY_SCRIPT_COMPLEX,
    "italic": cv2.FONT_HERSHEY_SIMPLEX | cv2.FONT_ITALIC,
}

_FACE_NAMES = {value: key for key, value in FONT_FACES.items()}


def resolve_font_face(value: FontLike) -> int:
    """Resolve a friendly font name or an OpenCV font constant."""

    if isinstance(value, str):
        key = value.strip().lower().replace("-", "_").replace(" ", "_")
        if key in FONT_FACES:
            return FONT_FACES[key]
        raise ConfigurationError(
            f"Unknown font {value!r}. Choose one of: {', '.join(sorted(FONT_FACES))}"
        )
    if isinstance(value, int):
        return value
    raise ConfigurationError(
        f"font_face must be a name or an OpenCV integer constant; got {value!r}"
    )


def font_name(value: int) -> str:
    """Return a friendly name for an OpenCV font constant, if known."""

    return _FACE_NAMES.get(value, str(value))


def measure_text(
    text: str,
    font_face: int,
    font_scale: float,
    font_thickness: int,
) -> Tuple[int, int, int]:
    """Return ``(width, height, baseline)`` for a string."""

    if not text:
        return (0, 0, 0)
    (width, height), baseline = cv2.getTextSize(text, font_face, font_scale, font_thickness)
    return int(width), int(height), int(baseline)


def fit_font_scale(
    text: str,
    font_face: int,
    font_scale: float,
    font_thickness: int,
    max_width: int,
    max_height: int,
    min_scale: float = 0.35,
) -> float:
    """Shrink ``font_scale`` until the rendered text fits the given box."""

    scale = float(font_scale)
    if not text:
        return scale
    for _ in range(80):
        width, height, baseline = measure_text(text, font_face, scale, font_thickness)
        if width <= max_width and height + baseline <= max_height:
            break
        scale *= 0.94
        if scale <= min_scale:
            return min_scale
    return max(scale, min_scale)

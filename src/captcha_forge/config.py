"""Configuration objects shared by every CAPTCHA generator."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Tuple

import cv2

from .colors import ColorLike, parse_color
from .exceptions import ConfigurationError
from .fonts import FontLike, resolve_font_face

DEFAULT_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
"""Characters that avoid visually ambiguous glyphs such as 0/O and 1/I."""

_COLOR_MODES = {"light", "dark", "custom"}


@dataclass
class CaptchaConfig:
    """Common configuration for every challenge type.

    Values that are specific to one generator (for example ``max_rotation``
    for the ``text`` type) are passed through ``options``. The :class:`Captcha`
    facade splits known common fields from generator options automatically.
    """

    width: int | None = None
    height: int | None = None
    fps: int = 30
    duration: float = 3.0
    seed: int | None = None
    color_mode: str = "light"
    background: ColorLike | None = None
    foreground: ColorLike | None = None
    font_face: FontLike = cv2.FONT_HERSHEY_DUPLEX
    font_scale: float = 2.5
    font_thickness: int = 2
    alphabet: str = DEFAULT_ALPHABET
    text: str | None = None
    length: int = 6
    options: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.font_face = resolve_font_face(self.font_face)
        self.validate()

    def validate(self) -> None:
        """Validate every common field and raise :class:`ConfigurationError`."""

        if self.width is not None and self.width < 32:
            raise ConfigurationError("width must be at least 32 pixels")
        if self.height is not None and self.height < 32:
            raise ConfigurationError("height must be at least 32 pixels")
        if not 1 <= self.fps <= 120:
            raise ConfigurationError("fps must be between 1 and 120")
        if not 0.05 <= self.duration <= 120:
            raise ConfigurationError("duration must be between 0.05 and 120 seconds")
        if self.seed is not None and not isinstance(self.seed, int):
            raise ConfigurationError("seed must be an integer or None")
        if self.color_mode == "ligth":
            # Common typo in the original project; keep it working.
            self.color_mode = "light"
        if self.color_mode not in _COLOR_MODES:
            raise ConfigurationError(
                f"color_mode must be one of {sorted(_COLOR_MODES)}; got {self.color_mode!r}"
            )
        if self.color_mode == "custom" and (self.background is None or self.foreground is None):
            raise ConfigurationError(
                "color_mode='custom' requires both background and foreground colours"
            )
        if self.background is not None:
            parse_color(self.background, "background")
        if self.foreground is not None:
            parse_color(self.foreground, "foreground")
        if not self.alphabet:
            raise ConfigurationError("alphabet must contain at least one character")
        if len(self.alphabet) > 256:
            raise ConfigurationError("alphabet must contain at most 256 characters")
        if not 1 <= self.length <= 32:
            raise ConfigurationError("length must be between 1 and 32")
        if self.font_scale <= 0:
            raise ConfigurationError("font_scale must be positive")
        if self.font_thickness <= 0:
            raise ConfigurationError("font_thickness must be positive")
        if self.text is not None:
            if not self.text:
                raise ConfigurationError("text cannot be empty")
            if len(self.text) > 64:
                raise ConfigurationError("text cannot be longer than 64 characters")
            try:
                self.text.encode("ascii")
            except UnicodeEncodeError as exc:
                raise ConfigurationError(
                    "text must contain printable ASCII characters because OpenCV Hershey "
                    "fonts do not support Unicode glyphs"
                ) from exc
            if any(ord(ch) < 32 or ord(ch) > 126 for ch in self.text):
                raise ConfigurationError("text must contain printable ASCII characters")

        for key, value in self.options.items():
            if not isinstance(key, str) or not key:
                raise ConfigurationError("option names must be non-empty strings")
            if key.startswith("_"):
                raise ConfigurationError(f"option {key!r} is reserved for internal use")
            if value is None:
                continue

    @property
    def font_face_id(self) -> int:
        """The resolved OpenCV font constant after ``__post_init__``."""

        return int(self.font_face)

    def resolved_size(self, default: Tuple[int, int]) -> Tuple[int, int]:
        """Return configured dimensions, falling back to a generator default."""

        width = default[0] if self.width is None else self.width
        height = default[1] if self.height is None else self.height
        return int(width), int(height)

    def replace(self, **changes: Any) -> CaptchaConfig:
        """Return a copy with selected fields replaced."""

        return dataclasses.replace(self, **changes)

    @classmethod
    def from_kwargs(cls, kwargs: Mapping[str, Any]) -> CaptchaConfig:
        """Split ``kwargs`` into common fields and generator options.

        Legacy names from the original project are accepted for a smooth
        migration: ``frame_size``, ``captcha_text``, ``font`` and the
        ``"ligth"`` colour-mode typo.
        """

        data = dict(kwargs)

        frame_size = data.pop("frame_size", None)
        if frame_size is not None:
            if not isinstance(frame_size, (tuple, list)) or len(frame_size) != 2:
                raise ConfigurationError("frame_size must be a (width, height) pair")
            data.setdefault("width", int(frame_size[0]))
            data.setdefault("height", int(frame_size[1]))

        if "captcha_text" in data:
            data.setdefault("text", data.pop("captcha_text"))
        if "font" in data:
            data.setdefault("font_face", data.pop("font"))

        options = dict(data.pop("options", {}) or {})
        fields = {field.name for field in dataclasses.fields(cls)} - {"options"}
        common = {key: value for key, value in data.items() if key in fields}
        extra = {key: value for key, value in data.items() if key not in fields}
        options.update(extra)
        return cls(options=options, **common)


__all__ = ["CaptchaConfig", "DEFAULT_ALPHABET"]

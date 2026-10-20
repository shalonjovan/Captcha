"""Theme resolution for light, dark, and custom colour modes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .colors import RGB, blend, luminance, parse_color
from .config import CaptchaConfig

RGB_TUPLE = Tuple[int, int, int]

DEFAULT_PALETTE: Tuple[RGB, ...] = (
    (220, 50, 50),
    (45, 90, 220),
    (40, 160, 90),
    (240, 140, 40),
    (135, 80, 200),
    (30, 155, 155),
    (235, 105, 160),
    (215, 170, 45),
)

_LIGHT = {
    "background": (248, 248, 244),
    "foreground": (24, 24, 28),
    "muted": (168, 168, 174),
    "accent": (37, 99, 235),
    "noise": (202, 202, 208),
    "line": (118, 118, 126),
}

_DARK = {
    "background": (16, 16, 20),
    "foreground": (242, 242, 246),
    "muted": (92, 92, 102),
    "accent": (96, 165, 250),
    "noise": (54, 54, 64),
    "line": (145, 145, 155),
}


@dataclass(frozen=True)
class Theme:
    """Resolved colours for a rendering pass, stored as RGB triples."""

    background: RGB
    foreground: RGB
    muted: RGB
    accent: RGB
    noise: RGB
    line: RGB
    palette: Tuple[RGB, ...]
    mode: str

    @property
    def background_bgr(self) -> RGB:
        return (self.background[2], self.background[1], self.background[0])

    @property
    def foreground_bgr(self) -> RGB:
        return (self.foreground[2], self.foreground[1], self.foreground[0])

    @property
    def is_dark(self) -> bool:
        return luminance(self.background) < 0.5


def resolve_theme(config: CaptchaConfig) -> Theme:
    """Build a :class:`Theme` from a configuration object."""

    mode = config.color_mode
    values = dict(_DARK) if mode == "dark" else dict(_LIGHT)

    if mode == "custom":
        assert config.background is not None and config.foreground is not None
        background = parse_color(config.background, "background")
        foreground = parse_color(config.foreground, "foreground")
    else:
        background = (
            parse_color(config.background, "background")
            if config.background is not None
            else values["background"]
        )
        foreground = (
            parse_color(config.foreground, "foreground")
            if config.foreground is not None
            else values["foreground"]
        )

    values["background"] = background
    values["foreground"] = foreground
    if mode == "custom" or config.background is not None or config.foreground is not None:
        values["muted"] = blend(background, foreground, 0.34)
        values["noise"] = blend(background, foreground, 0.14)
        values["line"] = blend(background, foreground, 0.46)
    values["accent"] = (37, 99, 235) if luminance(background) > 0.5 else (96, 165, 250)

    return Theme(
        background=values["background"],
        foreground=values["foreground"],
        muted=values["muted"],
        accent=values["accent"],
        noise=values["noise"],
        line=values["line"],
        palette=DEFAULT_PALETTE,
        mode=mode,
    )


__all__ = ["Theme", "resolve_theme", "DEFAULT_PALETTE"]

"""Animated foreground text with drifting background characters."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

import numpy as np

from ..exceptions import ConfigurationError
from ..registry import register
from ..rendering import GlyphCache, add_noise, blit_mask
from ..result import CaptchaResult
from .base import BaseGenerator


@register
class TextCaptcha(BaseGenerator):
    """Animated CAPTCHA with stable foreground text over floating letters."""

    name = "text"
    description = "Animated characters over drifting, semi-transparent background letters."
    default_size = (500, 160)
    default_format = "gif"
    animated = True

    option_defaults = {
        "max_rotation": 15.0,
        "min_spacing": 2,
        "max_spacing": 6,
        "bg_spawn_rate": 10.0,
        "bg_speed_min": 0.6,
        "bg_speed_max": 2.0,
        "initial_bg_count": 25,
        "max_bg_count": 80,
        "bg_alpha": 0.26,
        "bg_scale": 0.55,
        "fg_wave_amplitude": 0.0,
        "fg_wave_speed": 2.0,
        "shadow_offset": 2,
        "margin": 24,
        "noise": 0.012,
    }
    option_docs = {
        "max_rotation": "Maximum foreground and background glyph rotation in degrees.",
        "min_spacing": "Minimum pixel spacing between foreground characters.",
        "max_spacing": "Maximum pixel spacing between foreground characters.",
        "bg_spawn_rate": "New background glyphs spawned per second.",
        "bg_speed_min": "Minimum background glyph speed in pixels per frame.",
        "bg_speed_max": "Maximum background glyph speed in pixels per frame.",
        "initial_bg_count": "Background glyphs visible on the first frame.",
        "max_bg_count": "Hard limit on simultaneous background glyphs.",
        "bg_alpha": "Background glyph opacity (0-1).",
        "bg_scale": "Background glyph size relative to the foreground font.",
        "fg_wave_amplitude": "Vertical foreground wave amplitude in pixels.",
        "fg_wave_speed": "Foreground wave speed in cycles per second.",
        "shadow_offset": "Foreground drop-shadow offset in pixels; 0 disables it.",
        "margin": "Horizontal and vertical safe margin in pixels.",
        "noise": "Fine grain noise amount (0-1).",
    }

    def _validate_options(self) -> None:
        opts = self.options
        if not 0 <= opts["max_rotation"] <= 180:
            raise ConfigurationError("max_rotation must be between 0 and 180")
        if opts["min_spacing"] < 0 or opts["max_spacing"] < opts["min_spacing"]:
            raise ConfigurationError("spacing values must satisfy 0 <= min_spacing <= max_spacing")
        if opts["bg_spawn_rate"] < 0:
            raise ConfigurationError("bg_spawn_rate must be non-negative")
        if opts["bg_speed_min"] < 0 or opts["bg_speed_max"] < opts["bg_speed_min"]:
            raise ConfigurationError("bg speeds must satisfy 0 <= bg_speed_min <= bg_speed_max")
        if opts["initial_bg_count"] < 0 or opts["max_bg_count"] < opts["initial_bg_count"]:
            raise ConfigurationError("background counts must satisfy 0 <= initial <= max")
        if not 0 <= opts["bg_alpha"] <= 1:
            raise ConfigurationError("bg_alpha must be between 0 and 1")
        if opts["bg_scale"] <= 0:
            raise ConfigurationError("bg_scale must be positive")
        if opts["fg_wave_amplitude"] < 0:
            raise ConfigurationError("fg_wave_amplitude must be non-negative")
        if opts["shadow_offset"] < 0:
            raise ConfigurationError("shadow_offset must be non-negative")
        if opts["margin"] < 0:
            raise ConfigurationError("margin must be non-negative")
        if not 0 <= opts["noise"] <= 1:
            raise ConfigurationError("noise must be between 0 and 1")

    def _make_background_char(self, initial: bool) -> Dict[str, Any]:
        opts = self.options
        angle = self.rng.uniform(-opts["max_rotation"], opts["max_rotation"])
        if initial:
            x = self.rng.randint(-30, self.width)
            y = self.rng.randint(-30, self.height)
        else:
            x = self.rng.randint(-20, self.width + 20)
            y = self.height + self.rng.randint(4, 60)
        return {
            "char": self.rng.choice(self.config.alphabet),
            "x": float(x),
            "y": float(y),
            "vx": self.rng.uniform(-0.45, 0.45),
            "vy": -self.rng.uniform(opts["bg_speed_min"], opts["bg_speed_max"]),
            "angle": angle,
            "scale": opts["bg_scale"] * self.rng.uniform(0.75, 1.2),
            "alpha": opts["bg_alpha"] * self.rng.uniform(0.65, 1.0),
        }

    def _spawn_background(self, count: int, current: int) -> int:
        if current >= self.options["max_bg_count"]:
            return 0
        return min(count, self.options["max_bg_count"] - current)

    def _draw_background(
        self,
        frame: np.ndarray,
        chars: List[Dict[str, Any]],
        cache: GlyphCache,
    ) -> List[Dict[str, Any]]:
        alive: List[Dict[str, Any]] = []
        for item in chars:
            item["x"] += item["vx"]
            item["y"] += item["vy"]
            if item["y"] < -90 or item["x"] < -120 or item["x"] > self.width + 120:
                continue
            mask = cache.get(item["char"], rotation=item["angle"], scale=item["scale"])
            blit_mask(
                frame,
                mask,
                self.theme.foreground,
                int(item["x"]),
                int(item["y"]),
                alpha=item["alpha"],
            )
            alive.append(item)
        return alive

    def _prepare_foreground(self, text: str) -> Tuple[List[np.ndarray], List[int], int, float]:
        opts = self.options
        face = self.font_face
        thickness = self.config.font_thickness
        margin = int(opts["margin"])
        angles = [self.rng.uniform(-opts["max_rotation"], opts["max_rotation"]) for _ in text]
        phases = [self.rng.uniform(0.0, math.tau) for _ in text]
        spacings = [
            self.rng.randint(int(opts["min_spacing"]), int(opts["max_spacing"]))
            for _ in range(max(0, len(text) - 1))
        ]

        scale = float(self.config.font_scale)
        masks: List[np.ndarray] = []
        total_width = 0
        max_height = 0
        for _ in range(80):
            cache = GlyphCache(face, scale, thickness, padding=4)
            masks = [cache.get(char, rotation=angle) for char, angle in zip(text, angles)]
            total_width = sum(mask.shape[1] for mask in masks) + sum(spacings)
            max_height = max((mask.shape[0] for mask in masks), default=0)
            if total_width <= self.width - margin * 2 and max_height <= self.height - margin:
                break
            scale *= 0.93
            if scale < 0.35:
                break
        self._foreground_phases = phases
        return masks, spacings, total_width, scale

    def generate(self) -> CaptchaResult:
        text = self._text()
        masks, spacings, total_width, font_scale = self._prepare_foreground(text)
        phases = getattr(self, "_foreground_phases", [0.0] * len(text))
        opts = self.options
        fps = self.config.fps
        total_frames = self._frame_count()

        bg_cache = GlyphCache(
            self.font_face,
            self.config.font_scale * float(opts["bg_scale"]),
            self.config.font_thickness,
            padding=2,
        )
        background = [
            self._make_background_char(initial=True) for _ in range(int(opts["initial_bg_count"]))
        ]
        frames: List[np.ndarray] = []

        for frame_index in range(total_frames):
            frame = self._new_frame()

            expected = float(opts["bg_spawn_rate"]) / fps
            spawn_count = int(expected) + (1 if self.rng.random() < expected - int(expected) else 0)
            spawn_count = self._spawn_background(spawn_count, len(background))
            for _ in range(spawn_count):
                background.append(self._make_background_char(initial=False))
            background = self._draw_background(frame, background, bg_cache)

            x = (self.width - total_width) // 2
            time = frame_index / float(fps)
            for index, (mask, spacing) in enumerate(zip(masks, spacings + [0])):
                wave = 0.0
                if opts["fg_wave_amplitude"]:
                    wave = float(opts["fg_wave_amplitude"]) * math.sin(
                        math.tau * float(opts["fg_wave_speed"]) * time + phases[index]
                    )
                y = (self.height - mask.shape[0]) // 2 + int(round(wave))
                if opts["shadow_offset"]:
                    offset = int(opts["shadow_offset"])
                    blit_mask(
                        frame,
                        mask,
                        self.theme.muted,
                        x + offset,
                        y + offset,
                        alpha=0.5,
                    )
                blit_mask(frame, mask, self.theme.foreground, x, y)
                x += mask.shape[1] + int(spacing)

            if opts["noise"]:
                add_noise(frame, float(opts["noise"]), self.np_rng, monochrome=True)
            frames.append(frame)

        return self._result(
            frames,
            answer=text,
            text=text,
            metadata={
                "font_scale": font_scale,
                "characters": len(text),
                "background_glyphs": len(background),
                "background_spawn_rate": opts["bg_spawn_rate"],
            },
        )


__all__ = ["TextCaptcha"]

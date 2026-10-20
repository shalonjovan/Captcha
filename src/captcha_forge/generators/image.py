"""Static distorted-text CAPTCHA shared by the image, word, and math types."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

import numpy as np

from ..exceptions import ConfigurationError
from ..registry import register
from ..rendering import (
    GlyphCache,
    add_lines,
    add_noise,
    add_speckles,
    add_vignette,
    apply_wave,
    blit_mask,
    blit_mask_onto,
    make_gradient,
    shear_mask,
)
from ..result import CaptchaResult
from .base import BaseGenerator


@register
class ImageCaptcha(BaseGenerator):
    """Static text challenge with rotation, shear, wave, and interference."""

    name = "image"
    description = "Static distorted characters with noise, speckles, and interference lines."
    default_size = (500, 180)
    default_format = "png"

    option_defaults = {
        "max_rotation": 12.0,
        "letter_spacing": 4,
        "char_jitter": 2,
        "char_scale": 0.08,
        "shear": 0.12,
        "wave_amplitude": 3.5,
        "wave_wavelength": 70.0,
        "noise": 0.045,
        "line_count": 4,
        "dot_count": 120,
        "shadow_offset": 2,
        "margin": 30,
        "vignette": 0.18,
    }
    option_docs = {
        "max_rotation": "Maximum per-character rotation in degrees.",
        "letter_spacing": "Extra spacing between characters in pixels.",
        "char_jitter": "Random vertical jitter in pixels.",
        "char_scale": "Per-character random scale variation (0-0.5).",
        "shear": "Maximum per-character shear.",
        "wave_amplitude": "Global wave distortion amplitude in pixels.",
        "wave_wavelength": "Global wave wavelength in pixels.",
        "noise": "Fine grain noise amount (0-1).",
        "line_count": "Number of interference lines.",
        "dot_count": "Number of interference speckles.",
        "shadow_offset": "Drop-shadow offset in pixels; 0 disables it.",
        "margin": "Safe margin around the text in pixels.",
        "vignette": "Edge darkening strength (0-1).",
    }

    def _validate_options(self) -> None:
        opts = self.options
        if not 0 <= opts["max_rotation"] <= 180:
            raise ConfigurationError("max_rotation must be between 0 and 180")
        if opts["letter_spacing"] < 0:
            raise ConfigurationError("letter_spacing must be non-negative")
        if opts["char_jitter"] < 0:
            raise ConfigurationError("char_jitter must be non-negative")
        if not 0 <= opts["char_scale"] <= 0.5:
            raise ConfigurationError("char_scale must be between 0 and 0.5")
        if not 0 <= opts["shear"] <= 1:
            raise ConfigurationError("shear must be between 0 and 1")
        if opts["wave_amplitude"] < 0 or opts["wave_wavelength"] <= 0:
            raise ConfigurationError("wave values must be non-negative with a positive wavelength")
        if not 0 <= opts["noise"] <= 1:
            raise ConfigurationError("noise must be between 0 and 1")
        if opts["line_count"] < 0 or opts["dot_count"] < 0:
            raise ConfigurationError("interference counts must be non-negative")
        if opts["shadow_offset"] < 0:
            raise ConfigurationError("shadow_offset must be non-negative")
        if opts["margin"] < 0:
            raise ConfigurationError("margin must be non-negative")
        if not 0 <= opts["vignette"] <= 1:
            raise ConfigurationError("vignette must be between 0 and 1")

    def _make_problem(self) -> Tuple[str, Any, Dict[str, Any]]:
        text = self._text()
        return text, text, {}

    def _background(self) -> np.ndarray:
        colours = [
            self.theme.background,
            self.theme.noise,
            self.theme.muted,
        ]
        frame = make_gradient(
            self.width,
            self.height,
            self.theme.background,
            colours[1],
            rng=self.np_rng,
            blob_count=2,
            blob_alpha=0.10,
        )
        return frame

    def _text_mask(self, text: str) -> Tuple[np.ndarray, float]:
        opts = self.options
        face = self.font_face
        thickness = self.config.font_thickness
        margin = int(opts["margin"])
        angles = [self.rng.uniform(-opts["max_rotation"], opts["max_rotation"]) for _ in text]
        shears = [self.rng.uniform(-opts["shear"], opts["shear"]) for _ in text]
        scales = [1.0 + self.rng.uniform(-opts["char_scale"], opts["char_scale"]) for _ in text]
        jitters = [
            self.rng.randint(-int(opts["char_jitter"]), int(opts["char_jitter"])) for _ in text
        ]

        base_scale = float(self.config.font_scale)
        masks: List[np.ndarray] = []
        total_width = 0
        max_height = 0
        for _ in range(80):
            cache = GlyphCache(face, base_scale, thickness, padding=4)
            masks = []
            for char, angle, shear, scale in zip(text, angles, shears, scales):
                mask = cache.get(char, rotation=angle, scale=scale)
                if abs(shear) > 1e-6:
                    mask = shear_mask(mask, shear_x=shear)
                masks.append(mask)
            spacing = int(opts["letter_spacing"])
            total_width = sum(mask.shape[1] for mask in masks) + spacing * max(0, len(text) - 1)
            max_height = max((mask.shape[0] for mask in masks), default=0)
            if total_width <= self.width - margin * 2 and max_height <= self.height - margin * 2:
                break
            base_scale *= 0.93
            if base_scale < 0.35:
                break

        canvas = np.zeros((self.height, self.width), dtype=np.uint8)
        x = (self.width - total_width) // 2
        for mask, jitter in zip(masks, jitters):
            y = (self.height - mask.shape[0]) // 2 + jitter
            blit_mask_onto(canvas, mask, x, y)
            x += mask.shape[1] + int(opts["letter_spacing"])

        if opts["wave_amplitude"]:
            canvas = apply_wave(
                canvas,
                float(opts["wave_amplitude"]),
                float(opts["wave_wavelength"]),
                phase=self.rng.uniform(0.0, math.tau),
                axis="horizontal",
                border_value=0,
            )
        return canvas, base_scale

    def generate(self) -> CaptchaResult:
        opts = self.options
        text, answer, extra_metadata = self._make_problem()
        frame = self._background()
        mask, font_scale = self._text_mask(text)

        if opts["shadow_offset"]:
            offset = int(opts["shadow_offset"])
            blit_mask(frame, mask, self.theme.muted, offset, offset, alpha=0.45)
        blit_mask(frame, mask, self.theme.foreground, 0, 0)

        add_lines(
            frame,
            int(opts["line_count"]),
            self.theme.line,
            self.np_rng,
            thickness=(1, 2),
            alpha=0.45,
        )
        add_speckles(
            frame,
            int(opts["dot_count"]),
            self.theme.foreground,
            self.np_rng,
            radius=(1, 2),
            alpha=0.35,
        )
        add_noise(frame, float(opts["noise"]), self.np_rng, monochrome=True)
        add_vignette(frame, float(opts["vignette"]))

        metadata = {
            "font_scale": font_scale,
            "characters": len(text),
            "distortion": "rotation+shear+wave",
        }
        metadata.update(extra_metadata)
        return self._result([frame], answer=answer, text=text, metadata=metadata)


__all__ = ["ImageCaptcha"]

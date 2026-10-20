"""Animated noise-texture CAPTCHA."""

from __future__ import annotations

import math
from typing import List, Tuple

import cv2
import numpy as np

from ..exceptions import ConfigurationError
from ..registry import register
from ..rendering import GlyphCache, blit_mask_onto
from ..result import CaptchaResult
from .base import BaseGenerator


@register
class NoiseCaptcha(BaseGenerator):
    """Moving static field with glyphs carved out of noise."""

    name = "noise"
    description = "Animated moving static with characters rendered as noise texture."
    default_size = (500, 160)
    default_format = "gif"
    animated = True

    option_defaults = {
        "noise_scale": 8,
        "grain": 1,
        "speed_x": 1.0,
        "speed_y": 0.0,
        "bounce_amplitude": 8.0,
        "bounce_speed": 2.0,
        "max_rotation": 12.0,
        "min_spacing": 2,
        "max_spacing": 8,
        "margin": 24,
        "contrast": 1.15,
    }
    option_docs = {
        "noise_scale": "Size multiplier for the reusable noise field (2-32).",
        "grain": "Pixel block size of the noise texture.",
        "speed_x": "Horizontal noise panning speed in pixels per frame.",
        "speed_y": "Vertical noise panning speed in pixels per frame.",
        "bounce_amplitude": "Vertical character bounce in pixels.",
        "bounce_speed": "Character bounce speed in cycles per second.",
        "max_rotation": "Maximum character rotation in degrees.",
        "min_spacing": "Minimum character spacing in pixels.",
        "max_spacing": "Maximum character spacing in pixels.",
        "margin": "Horizontal safe margin in pixels.",
        "contrast": "Noise-text contrast multiplier.",
    }

    def _validate_options(self) -> None:
        opts = self.options
        if not 2 <= int(opts["noise_scale"]) <= 32:
            raise ConfigurationError("noise_scale must be between 2 and 32")
        if not 1 <= int(opts["grain"]) <= 16:
            raise ConfigurationError("grain must be between 1 and 16")
        if opts["min_spacing"] < 0 or opts["max_spacing"] < opts["min_spacing"]:
            raise ConfigurationError("spacing values must satisfy 0 <= min <= max")
        if opts["bounce_amplitude"] < 0:
            raise ConfigurationError("bounce_amplitude must be non-negative")
        if opts["margin"] < 0:
            raise ConfigurationError("margin must be non-negative")
        if opts["contrast"] <= 0:
            raise ConfigurationError("contrast must be positive")

    def _prepare_glyphs(self, text: str) -> Tuple[List[np.ndarray], List[int], int, int]:
        opts = self.options
        face = self.font_face
        thickness = self.config.font_thickness
        margin = int(opts["margin"])
        angles = [self.rng.uniform(-opts["max_rotation"], opts["max_rotation"]) for _ in text]
        spacings = [
            self.rng.randint(int(opts["min_spacing"]), int(opts["max_spacing"]))
            for _ in range(max(0, len(text) - 1))
        ]

        scale = float(self.config.font_scale)
        masks: List[np.ndarray] = []
        total_width = 0
        max_height = 0
        for _ in range(80):
            cache = GlyphCache(face, scale, thickness, padding=3)
            masks = [cache.get(char, rotation=angle) for char, angle in zip(text, angles)]
            total_width = sum(mask.shape[1] for mask in masks) + sum(spacings)
            max_height = max((mask.shape[0] for mask in masks), default=0)
            if total_width <= self.width - margin * 2 and max_height <= self.height - margin:
                break
            scale *= 0.93
            if scale < 0.35:
                break
        return masks, spacings, total_width, max_height

    def generate(self) -> CaptchaResult:
        opts = self.options
        text = self._text()
        masks, spacings, total_width, _ = self._prepare_glyphs(text)
        fps = self.config.fps
        total_frames = self._frame_count()

        # Cap the reusable field for large frames: a 32x multiplier on a
        # full-HD frame would allocate gigabytes for panning headroom.
        max_field_pixels = 4_000_000
        max_scale = max(1, max_field_pixels // max(1, self.width * self.height))
        scale_factor = max(1, min(int(opts["noise_scale"]), max_scale))
        base_height = self.height * scale_factor + self.height
        base_width = self.width * scale_factor + self.width
        base_noise = self.np_rng.integers(0, 256, size=(base_height, base_width), dtype=np.uint8)

        grain = int(opts["grain"])
        phases = [self.rng.uniform(0.0, math.tau) for _ in text]
        x_cursor = (self.width - total_width) // 2
        positions = []
        for mask, spacing in zip(masks, spacings + [0]):
            positions.append(x_cursor)
            x_cursor += mask.shape[1] + int(spacing)

        max_x = max(1, base_width - self.width)
        max_y = max(1, base_height - self.height)
        x_position = 0.0
        y_position = 0.0
        frames: List[np.ndarray] = []

        for frame_index in range(total_frames):
            x_offset = int(round(x_position)) % max_x
            y_offset = int(round(y_position)) % max_y
            view: np.ndarray = base_noise[
                y_offset : y_offset + self.height,
                x_offset : x_offset + self.width,
            ]
            if grain > 1:
                block_width = max(1, self.width // grain)
                block_height = max(1, self.height // grain)
                view = cv2.resize(
                    view,
                    (block_width, block_height),
                    interpolation=cv2.INTER_AREA,
                )
                view = cv2.resize(
                    view,
                    (self.width, self.height),
                    interpolation=cv2.INTER_NEAREST,
                )
            gray = view.astype(np.float32) / 255.0
            background: np.ndarray = np.clip(
                np.asarray(self.theme.background, dtype=np.float32)
                + (gray[..., None] - 0.5) * 52.0,
                0,
                255,
            ).astype(np.uint8)
            frame: np.ndarray = background[:, :, ::-1].copy()

            text_mask = np.zeros((self.height, self.width), dtype=np.uint8)
            time = frame_index / float(fps)
            for index, (mask, x) in enumerate(zip(masks, positions)):
                offset = float(opts["bounce_amplitude"]) * math.sin(
                    math.tau * float(opts["bounce_speed"]) * time + phases[index]
                )
                y = (self.height - mask.shape[0]) // 2 + int(round(offset))
                blit_mask_onto(text_mask, mask, x, y)

            noise = self.np_rng.integers(0, 256, size=(self.height, self.width), dtype=np.uint8)
            tone = noise if self.theme.is_dark else (255 - noise)
            contrast = float(opts["contrast"])
            tone = np.clip(128.0 + (tone.astype(np.float32) - 128.0) * contrast, 0, 255).astype(
                np.uint8
            )
            text_texture = cv2.bitwise_and(tone, text_mask)
            text_bgr = cv2.cvtColor(text_texture, cv2.COLOR_GRAY2BGR)
            # Give the noise a hint of the foreground colour without losing the texture.
            text_bgr = cv2.addWeighted(
                text_bgr,
                0.82,
                np.full_like(text_bgr, self.theme.foreground_bgr),
                0.18,
                0,
            )

            alpha = (text_mask.astype(np.float32) / 255.0)[..., None]
            frame = np.clip(
                frame.astype(np.float32) * (1.0 - alpha) + text_bgr.astype(np.float32) * alpha,
                0,
                255,
            )
            frames.append(frame.astype(np.uint8))

            x_position = (x_position + float(opts["speed_x"])) % max_x
            y_position = (y_position + float(opts["speed_y"])) % max_y

        return self._result(
            frames,
            answer=text,
            text=text,
            metadata={
                "noise_scale": scale_factor,
                "grain": grain,
                "noise_field": (base_width, base_height),
                "characters": len(text),
            },
        )


__all__ = ["NoiseCaptcha"]

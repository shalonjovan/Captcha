"""Slider / jigsaw puzzle CAPTCHA."""

from __future__ import annotations

from typing import Any, Dict

import numpy as np

from ..colors import blend
from ..exceptions import ConfigurationError
from ..registry import register
from ..rendering import (
    add_lines,
    add_noise,
    add_vignette,
    blit_image_mask,
    blit_mask,
    make_gradient,
    make_puzzle_mask,
    outline_mask,
)
from ..result import CaptchaResult
from .base import BaseGenerator


@register
class SliderCaptcha(BaseGenerator):
    """A jigsaw piece and a matching gap; the answer is the target x position."""

    name = "slider"
    description = "Jigsaw slider puzzle with a cut-out piece and target gap."
    default_size = (460, 300)
    default_format = "png"

    option_defaults = {
        "piece_size": 74,
        "tab_radius": 10,
        "target_x": None,
        "gap_y": None,
        "tolerance": 6,
        "background_blobs": 6,
        "line_count": 5,
        "noise": 0.035,
        "vignette": 0.22,
        "start_x": 14,
    }
    option_docs = {
        "piece_size": "Size of the puzzle piece body in pixels.",
        "tab_radius": "Radius of puzzle tabs and notches.",
        "target_x": "Force the gap x position; None chooses randomly.",
        "gap_y": "Force the gap y position; None chooses randomly.",
        "tolerance": "Accepted pixel error when checking the answer.",
        "background_blobs": "Number of soft colour blobs in the background.",
        "line_count": "Number of background interference lines.",
        "noise": "Background grain amount (0-1).",
        "vignette": "Edge darkening strength (0-1).",
        "start_x": "Initial x position of the draggable piece.",
    }

    def _validate_options(self) -> None:
        opts = self.options
        if not 24 <= int(opts["piece_size"]) <= min(self.width, self.height) - 20:
            raise ConfigurationError("piece_size must fit inside the frame")
        if not 4 <= int(opts["tab_radius"]) <= int(opts["piece_size"]) // 3:
            raise ConfigurationError("tab_radius must be between 4 and piece_size / 3")
        if int(opts["tolerance"]) < 0:
            raise ConfigurationError("tolerance must be non-negative")
        if int(opts["background_blobs"]) < 0 or int(opts["line_count"]) < 0:
            raise ConfigurationError("background element counts must be non-negative")
        if not 0 <= opts["noise"] <= 1:
            raise ConfigurationError("noise must be between 0 and 1")
        if not 0 <= opts["vignette"] <= 1:
            raise ConfigurationError("vignette must be between 0 and 1")
        if int(opts["start_x"]) < 0:
            raise ConfigurationError("start_x must be non-negative")

    def _background(self) -> np.ndarray:
        opts = self.options
        top = self.theme.background
        bottom = blend(self.theme.background, self.theme.noise, 0.72)
        frame = make_gradient(
            self.width,
            self.height,
            top,
            bottom,
            rng=self.np_rng,
            blob_count=int(opts["background_blobs"]),
            blob_alpha=0.20,
        )
        add_lines(
            frame,
            int(opts["line_count"]),
            self.theme.line,
            self.np_rng,
            thickness=(1, 2),
            alpha=0.30,
        )
        add_noise(frame, float(opts["noise"]), self.np_rng, monochrome=True)
        add_vignette(frame, float(opts["vignette"]))
        return frame

    def _pick_positions(self, mask_w: int, mask_h: int) -> tuple[int, int, int]:
        opts = self.options
        margin = 14
        start_x = int(opts["start_x"])
        max_x = max(margin, self.width - mask_w - margin)
        max_y = max(margin, self.height - mask_h - margin)
        if start_x > self.width - mask_w:
            raise ConfigurationError("start_x leaves no room for the puzzle piece")

        target_x: int | None = opts["target_x"]
        if target_x is None:
            low = min(max_x, start_x + mask_w + 24)
            if low >= max_x:
                low = margin
            target_x = self.rng.randint(low, max_x)
        else:
            target_x = int(target_x)
            if not margin <= target_x <= max_x:
                raise ConfigurationError(
                    f"target_x must be between {margin} and {max_x} for this frame size"
                )

        gap_y: int | None = opts["gap_y"]
        if gap_y is None:
            gap_y = self.rng.randint(margin, max_y)
        else:
            gap_y = int(gap_y)
            if not margin <= gap_y <= max_y:
                raise ConfigurationError(
                    f"gap_y must be between {margin} and {max_y} for this frame size"
                )
        return target_x, gap_y, start_x

    def generate(self) -> CaptchaResult:
        opts = self.options
        frame = self._background()
        piece_size = int(opts["piece_size"])
        mask = make_puzzle_mask(piece_size, int(opts["tab_radius"]), self.rng)
        mask_h, mask_w = mask.shape
        target_x, gap_y, start_x = self._pick_positions(mask_w, mask_h)
        start_y = gap_y

        piece_image = frame[gap_y : gap_y + mask_h, target_x : target_x + mask_w].copy()

        # Cut a visible gap, then outline it.
        gap_fill = blend(self.theme.background, self.theme.foreground, 0.58)
        blit_mask(frame, mask, gap_fill, target_x, gap_y, alpha=0.72)
        blit_mask(frame, mask, (0, 0, 0), target_x + 2, gap_y + 2, alpha=0.18)
        outline_mask(frame, mask, self.theme.accent, 2, (target_x, gap_y))

        # Place the draggable piece at its starting position with a shadow and outline.
        blit_mask(frame, mask, (0, 0, 0), start_x + 4, start_y + 4, alpha=0.35)
        blit_image_mask(frame, piece_image, mask, start_x, start_y)
        outline_mask(frame, mask, self.theme.accent, 2, (start_x, start_y))

        piece_bgra = np.dstack([piece_image, mask])
        metadata: Dict[str, Any] = {
            "target_x": target_x,
            "gap_y": gap_y,
            "piece_size": piece_size,
            "piece_box": (start_x, start_y, mask_w, mask_h),
            "gap_box": (target_x, gap_y, mask_w, mask_h),
            "tolerance": int(opts["tolerance"]),
            "instruction": "Drag the puzzle piece into the gap.",
        }
        return self._result(
            [frame],
            answer=target_x,
            text=None,
            metadata=metadata,
            assets={"piece": piece_bgra},
        )


__all__ = ["SliderCaptcha"]

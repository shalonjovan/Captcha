"""Connect-the-numbered-dots pattern CAPTCHA."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import cv2

from ..colors import blend
from ..exceptions import ConfigurationError
from ..fonts import fit_font_scale, measure_text
from ..registry import register
from ..rendering import (
    add_noise,
    add_vignette,
    draw_text,
    draw_text_centered,
    make_gradient,
)
from ..result import CaptchaResult
from .base import BaseGenerator


@register
class PatternCaptcha(BaseGenerator):
    """Connect numbered dots in ascending order on a dot grid."""

    name = "pattern"
    description = "Connect numbered dots in ascending order; the answer is the coordinate sequence."
    default_size = (380, 380)
    default_format = "png"

    option_defaults = {
        "grid": 3,
        "path_length": 5,
        "dot_radius": 12,
        "noise": 0.025,
        "margin": 58,
        "vignette": 0.12,
        "show_instruction": True,
    }
    option_docs = {
        "grid": "Grid size (2-5). A 3x3 grid has nine dots.",
        "path_length": "Number of numbered dots in the challenge.",
        "dot_radius": "Outer dot radius in pixels.",
        "noise": "Background grain amount (0-1).",
        "margin": "Outer margin in pixels.",
        "vignette": "Edge darkening strength (0-1).",
        "show_instruction": "Draw the instruction at the top of the image.",
    }

    def _validate_options(self) -> None:
        opts = self.options
        grid = int(opts["grid"])
        if not 2 <= grid <= 5:
            raise ConfigurationError("grid must be between 2 and 5")
        if not 2 <= int(opts["path_length"]) <= grid * grid:
            raise ConfigurationError("path_length must be between 2 and grid * grid")
        if not 4 <= int(opts["dot_radius"]) <= min(self.width, self.height) // 10:
            raise ConfigurationError("dot_radius is outside the supported range")
        if int(opts["margin"]) < int(opts["dot_radius"]) + 8:
            raise ConfigurationError("margin must leave room for the dot grid")
        if not 0 <= opts["noise"] <= 1:
            raise ConfigurationError("noise must be between 0 and 1")
        if not 0 <= opts["vignette"] <= 1:
            raise ConfigurationError("vignette must be between 0 and 1")

    def _grid_positions(self) -> List[Tuple[int, int]]:
        grid = int(self.options["grid"])
        margin = int(self.options["margin"])
        usable_w = self.width - margin * 2
        usable_h = self.height - margin * 2
        step_x = usable_w / (grid - 1)
        step_y = usable_h / (grid - 1)
        return [
            (int(margin + col * step_x), int(margin + row * step_y))
            for row in range(grid)
            for col in range(grid)
        ]

    def generate(self) -> CaptchaResult:
        opts = self.options
        positions = self._grid_positions()
        total = len(positions)
        path_length = int(opts["path_length"])
        chosen = self.rng.sample(range(total), path_length)
        labels = list(range(1, path_length + 1))
        self.rng.shuffle(labels)
        node_labels = dict(zip(chosen, labels))
        ordered_indices = sorted(chosen, key=lambda index: node_labels[index])

        frame = make_gradient(
            self.width,
            self.height,
            self.theme.background,
            blend(self.theme.background, self.theme.noise, 0.62),
            rng=self.np_rng,
            blob_count=2,
            blob_alpha=0.08,
        )
        add_noise(frame, float(opts["noise"]), self.np_rng, monochrome=True)
        add_vignette(frame, float(opts["vignette"]))

        face = self.font_face
        thickness = max(1, self.config.font_thickness - 1)
        radius = int(opts["dot_radius"])

        if opts["show_instruction"]:
            instruction = "Connect the dots in number order"
            scale = fit_font_scale(
                instruction,
                face,
                0.60,
                thickness,
                self.width - 32,
                int(opts["margin"] * 0.62),
            )
            width, height, baseline = measure_text(instruction, face, scale, thickness)
            draw_text(
                frame,
                instruction,
                (int((self.width - width) / 2), 16 + height),
                face,
                scale,
                thickness,
                self.theme.foreground,
            )

        node_metadata: List[Dict[str, Any]] = []
        for index, (x, y) in enumerate(positions):
            selected = index in node_labels
            if selected:
                cv2_colour = self.theme.accent
                cv2_inner = blend(self.theme.background, self.theme.accent, 0.18)
                cv2.circle(frame, (x, y), radius + 4, cv2_colour[::-1], 1, lineType=cv2.LINE_AA)
                cv2.circle(frame, (x, y), radius, cv2_inner[::-1], -1, lineType=cv2.LINE_AA)
                cv2.circle(frame, (x, y), radius, cv2_colour[::-1], 2, lineType=cv2.LINE_AA)
                label = str(node_labels[index])
                label_scale = 0.54 if len(label) == 1 else 0.42
                draw_text_centered(
                    frame,
                    label,
                    (x, y + 1),
                    face,
                    label_scale,
                    max(1, thickness),
                    self.theme.foreground,
                )
                node_metadata.append(
                    {
                        "index": index,
                        "label": node_labels[index],
                        "x": x,
                        "y": y,
                        "selected": True,
                    }
                )
            else:
                cv2.circle(
                    frame,
                    (x, y),
                    max(3, radius // 3),
                    self.theme.muted[::-1],
                    -1,
                    lineType=cv2.LINE_AA,
                )
                cv2.circle(
                    frame, (x, y), radius + 4, self.theme.muted[::-1], 1, lineType=cv2.LINE_AA
                )
                node_metadata.append(
                    {
                        "index": index,
                        "label": None,
                        "x": x,
                        "y": y,
                        "selected": False,
                    }
                )

        answer = [[positions[index][0], positions[index][1]] for index in ordered_indices]
        return self._result(
            [frame],
            answer=answer,
            text=None,
            metadata={
                "instruction": "Connect the dots in number order",
                "grid": int(opts["grid"]),
                "path_length": path_length,
                "nodes": node_metadata,
                "answer_indices": ordered_indices,
                "labels": [node_labels[index] for index in ordered_indices],
                "dot_radius": radius,
            },
        )


__all__ = ["PatternCaptcha"]

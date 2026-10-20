"""Rotation-alignment CAPTCHA."""

from __future__ import annotations

import math

import cv2
import numpy as np

from ..colors import blend
from ..exceptions import ConfigurationError
from ..fonts import fit_font_scale, measure_text
from ..registry import register
from ..rendering import add_noise, add_vignette, draw_text, make_gradient
from ..result import CaptchaResult
from .base import BaseGenerator

_DIRECTION_ANGLES = {
    "up": 270.0,
    "right": 0.0,
    "down": 90.0,
    "left": 180.0,
}


@register
class RotateCaptcha(BaseGenerator):
    """Rotate an arrow until it points in the requested direction."""

    name = "rotate"
    description = "An arrow at a random angle; the answer is the clockwise rotation needed."
    default_size = (380, 300)
    default_format = "png"

    option_defaults = {
        "direction": "up",
        "min_angle": 30.0,
        "max_angle": 330.0,
        "tolerance": 8.0,
        "noise": 0.025,
        "vignette": 0.14,
        "show_instruction": True,
    }
    option_docs = {
        "direction": "Target direction: up, right, down, or left.",
        "min_angle": "Minimum starting arrow angle in degrees (0 = right).",
        "max_angle": "Maximum starting arrow angle in degrees.",
        "tolerance": "Accepted angular error in degrees.",
        "noise": "Background grain amount (0-1).",
        "vignette": "Edge darkening strength (0-1).",
        "show_instruction": "Draw the instruction at the top of the image.",
    }

    def _validate_options(self) -> None:
        opts = self.options
        if str(opts["direction"]).lower() not in _DIRECTION_ANGLES:
            raise ConfigurationError("direction must be up, right, down, or left")
        if not 0 <= float(opts["min_angle"]) < float(opts["max_angle"]) <= 360:
            raise ConfigurationError("angles must satisfy 0 <= min_angle < max_angle <= 360")
        if not 0 <= float(opts["tolerance"]) <= 45:
            raise ConfigurationError("tolerance must be between 0 and 45 degrees")
        if not 0 <= opts["noise"] <= 1:
            raise ConfigurationError("noise must be between 0 and 1")
        if not 0 <= opts["vignette"] <= 1:
            raise ConfigurationError("vignette must be between 0 and 1")

    def generate(self) -> CaptchaResult:
        opts = self.options
        direction = str(opts["direction"]).lower()
        target_angle = _DIRECTION_ANGLES[direction]
        low = float(opts["min_angle"])
        high = float(opts["max_angle"])
        tolerance = float(opts["tolerance"])
        angle = self.rng.uniform(low, high)
        for _ in range(50):
            difference = abs(((angle - target_angle + 180.0) % 360.0) - 180.0)
            if difference > max(tolerance, 4.0):
                break
            angle = self.rng.uniform(low, high)

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
        if opts["show_instruction"]:
            instruction = f"Rotate the arrow to point {direction}"
            scale = fit_font_scale(instruction, face, 0.60, thickness, self.width - 28, 34)
            width, height, baseline = measure_text(instruction, face, scale, thickness)
            draw_text(
                frame,
                instruction,
                (int((self.width - width) / 2), 18 + height),
                face,
                scale,
                thickness,
                self.theme.foreground,
            )

        centre = (self.width // 2, int(self.height * 0.59))
        radius = int(min(self.width, self.height) * 0.29)
        cv2.circle(frame, centre, radius, self.theme.muted[::-1], 1, lineType=cv2.LINE_AA)
        for degrees in range(0, 360, 30):
            theta = math.radians(degrees)
            inner = (
                int(centre[0] + (radius - 7) * math.cos(theta)),
                int(centre[1] + (radius - 7) * math.sin(theta)),
            )
            outer = (
                int(centre[0] + radius * math.cos(theta)),
                int(centre[1] + radius * math.sin(theta)),
            )
            cv2.line(frame, inner, outer, self.theme.line[::-1], 1, lineType=cv2.LINE_AA)

        # Target marker at the requested direction.
        theta = math.radians(target_angle)
        marker_centre = (
            int(centre[0] + (radius + 14) * math.cos(theta)),
            int(centre[1] + (radius + 14) * math.sin(theta)),
        )
        marker_size = 9
        points = np.array(
            [
                (
                    marker_centre[0] + marker_size * math.cos(theta - math.pi / 2),
                    marker_centre[1] + marker_size * math.sin(theta - math.pi / 2),
                ),
                (
                    marker_centre[0] + marker_size * math.cos(theta + math.pi / 2),
                    marker_centre[1] + marker_size * math.sin(theta + math.pi / 2),
                ),
                (
                    marker_centre[0] - marker_size * 1.2 * math.cos(theta),
                    marker_centre[1] - marker_size * 1.2 * math.sin(theta),
                ),
            ],
            dtype=np.int32,
        )
        cv2.fillPoly(frame, [points], self.theme.accent[::-1], lineType=cv2.LINE_AA)

        angle_rad = math.radians(angle)
        length = int(radius * 0.76)
        tip = (
            int(centre[0] + length * math.cos(angle_rad)),
            int(centre[1] + length * math.sin(angle_rad)),
        )
        thickness_px = max(3, int(min(self.width, self.height) * 0.018))
        cv2.arrowedLine(
            frame,
            (centre[0] + 3, centre[1] + 3),
            (tip[0] + 3, tip[1] + 3),
            blend(self.theme.background, self.theme.foreground, 0.22)[::-1],
            thickness_px,
            line_type=cv2.LINE_AA,
            tipLength=0.25,
        )
        cv2.arrowedLine(
            frame,
            centre,
            tip,
            self.theme.accent[::-1],
            thickness_px,
            line_type=cv2.LINE_AA,
            tipLength=0.25,
        )
        cv2.circle(
            frame, centre, max(4, thickness_px), self.theme.accent[::-1], -1, lineType=cv2.LINE_AA
        )

        answer = round((target_angle - angle) % 360.0, 1)
        return self._result(
            [frame],
            answer=answer,
            text=None,
            metadata={
                "instruction": f"Rotate the arrow to point {direction}",
                "direction": direction,
                "angle": round(angle, 1),
                "target_angle": target_angle,
                "tolerance": tolerance,
                "rotation_needed_clockwise": answer,
                "centre": centre,
                "radius": radius,
            },
        )


__all__ = ["RotateCaptcha"]

"""Click-the-matching-shapes CAPTCHA."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

from ..colors import RGB, blend, parse_color
from ..exceptions import ConfigurationError
from ..fonts import fit_font_scale, measure_text
from ..registry import register
from ..rendering import (
    add_noise,
    add_speckles,
    draw_shape,
    draw_text,
    make_gradient,
)
from ..result import CaptchaResult
from .base import BaseGenerator

_ALLOWED_SHAPES = {"circle", "square", "triangle", "diamond", "star"}


@register
class ClickCaptcha(BaseGenerator):
    """Click every shape matching a target shape and colour."""

    name = "click"
    description = "Click all shapes matching a rendered shape and colour instruction."
    default_size = (460, 320)
    default_format = "png"

    option_defaults = {
        "target_count": 3,
        "decoy_count": 5,
        "shapes": ("circle", "square", "triangle", "diamond", "star"),
        "colors": ("red", "blue", "green", "orange", "purple"),
        "target_shape": None,
        "target_color": None,
        "radius_scale": 0.28,
        "jitter": 0.18,
        "noise": 0.025,
        "dot_count": 50,
        "margin": 18,
    }
    option_docs = {
        "target_count": "Number of correct shapes to click.",
        "decoy_count": "Number of distractor shapes.",
        "shapes": "Shape pool: circle, square, triangle, diamond, star.",
        "colors": "Colour pool: names or hex strings.",
        "target_shape": "Force the target shape; None chooses randomly.",
        "target_color": "Force the target colour; None chooses randomly.",
        "radius_scale": "Shape radius as a fraction of the grid cell size.",
        "jitter": "Random position jitter within each grid cell (0-0.5).",
        "noise": "Background grain amount (0-1).",
        "dot_count": "Background speckle count.",
        "margin": "Outer margin in pixels.",
    }

    def _sequence(self, value: Any, name: str) -> List[str]:
        if isinstance(value, str):
            items = [part.strip() for part in value.split(",") if part.strip()]
        else:
            items = [str(part).strip() for part in value]
        if not items:
            raise ConfigurationError(f"{name} must contain at least one value")
        return items

    def _validate_options(self) -> None:
        opts = self.options
        if int(opts["target_count"]) < 1:
            raise ConfigurationError("target_count must be at least 1")
        if int(opts["decoy_count"]) < 0:
            raise ConfigurationError("decoy_count must be non-negative")
        if (
            int(opts["decoy_count"]) > 0
            and len(self._sequence(opts["shapes"], "shapes")) == 1
            and len(self._sequence(opts["colors"], "colors")) == 1
        ):
            raise ConfigurationError(
                "decoy shapes need at least two shapes or two colours to be distinguishable"
            )
        shapes = [shape.lower() for shape in self._sequence(opts["shapes"], "shapes")]
        invalid = set(shapes) - _ALLOWED_SHAPES
        if invalid:
            raise ConfigurationError(
                f"Unsupported shape(s): {', '.join(sorted(invalid))}. "
                f"Allowed: {', '.join(sorted(_ALLOWED_SHAPES))}"
            )
        self._shapes = list(dict.fromkeys(shapes))
        self._colors: List[Tuple[str, RGB]] = []
        for value in self._sequence(opts["colors"], "colors"):
            self._colors.append((value.lower(), parse_color(value, "colors")))
        self._color_names = [name for name, _ in self._colors]
        if not 0 < opts["radius_scale"] <= 0.5:
            raise ConfigurationError("radius_scale must be between 0 and 0.5")
        if not 0 <= opts["jitter"] <= 0.5:
            raise ConfigurationError("jitter must be between 0 and 0.5")
        if not 0 <= opts["noise"] <= 1:
            raise ConfigurationError("noise must be between 0 and 1")
        if int(opts["dot_count"]) < 0:
            raise ConfigurationError("dot_count must be non-negative")
        if int(opts["margin"]) < 0:
            raise ConfigurationError("margin must be non-negative")

        target_shape = opts["target_shape"]
        if target_shape is not None:
            target_shape = str(target_shape).lower()
            if target_shape not in self._shapes:
                raise ConfigurationError("target_shape must be present in shapes")
        target_color = opts["target_color"]
        if target_color is not None:
            target_color = str(target_color).lower()
            if target_color not in self._color_names:
                raise ConfigurationError("target_color must be present in colors")

    def _pick_target(self) -> Tuple[str, str, RGB]:
        target_shape = self.options["target_shape"]
        target_color = self.options["target_color"]
        target_shape = (
            self.rng.choice(self._shapes) if target_shape is None else str(target_shape).lower()
        )
        if target_color is None:
            target_color = self.rng.choice(self._color_names)
        else:
            target_color = str(target_color).lower()
        colour = dict(self._colors)[target_color]
        return target_shape, target_color, colour

    def _grid(self, total: int) -> Tuple[int, int, float, float, int]:
        opts = self.options
        margin = int(opts["margin"])
        header = max(42, int(self.height * 0.16))
        usable_w = self.width - margin * 2
        usable_h = self.height - header - margin
        if usable_w <= 20 or usable_h <= 20:
            raise ConfigurationError("frame is too small for the click layout")
        aspect = usable_w / max(1.0, usable_h)
        cols = max(1, int(math.ceil(math.sqrt(max(1, total) * aspect))))
        rows = max(1, int(math.ceil(total / cols)))
        return cols, rows, usable_w / cols, usable_h / rows, header

    def _make_items(
        self, target_shape: str, target_color: str, target_colour: RGB
    ) -> List[Dict[str, Any]]:
        shapes = self._shapes
        colours = self._colors
        items: List[Dict[str, Any]] = []
        for _ in range(int(self.options["target_count"])):
            items.append(
                {"shape": target_shape, "color": target_color, "rgb": target_colour, "target": True}
            )
        for _ in range(int(self.options["decoy_count"])):
            for _attempt in range(30):
                shape = self.rng.choice(shapes)
                name, rgb = colours[self.rng.randrange(len(colours))]
                if shape == target_shape and name == target_color:
                    continue
                items.append({"shape": shape, "color": name, "rgb": rgb, "target": False})
                break
            else:
                # A very small pool may leave only matching combinations. Pick at
                # least one non-matching attribute so the decoy stays a decoy.
                decoy_shapes = [shape for shape in shapes if shape != target_shape] or shapes
                decoy_colours = [
                    (name, rgb) for name, rgb in colours if name != target_color
                ] or colours
                shape = self.rng.choice(decoy_shapes)
                name, rgb = self.rng.choice(decoy_colours)
                items.append({"shape": shape, "color": name, "rgb": rgb, "target": False})
        self.rng.shuffle(items)
        return items

    def _instruction(self, target_shape: str, target_color: str) -> str:
        return f"Click every {target_color} {target_shape}"

    def generate(self) -> CaptchaResult:
        opts = self.options
        target_shape, target_color, target_colour = self._pick_target()
        items = self._make_items(target_shape, target_color, target_colour)
        cols, rows, cell_w, cell_h, header = self._grid(len(items))
        margin = int(opts["margin"])

        frame = make_gradient(
            self.width,
            self.height,
            self.theme.background,
            blend(self.theme.background, self.theme.noise, 0.65),
            rng=self.np_rng,
            blob_count=2,
            blob_alpha=0.10,
        )
        add_noise(frame, float(opts["noise"]), self.np_rng, monochrome=True)
        add_speckles(
            frame, int(opts["dot_count"]), self.theme.line, self.np_rng, radius=(1, 2), alpha=0.22
        )

        instruction = self._instruction(target_shape, target_color)
        face = self.font_face
        thickness = self.config.font_thickness
        scale = fit_font_scale(
            instruction,
            face,
            min(0.62, self.height * 0.004),
            max(1, thickness - 1),
            self.width - margin * 2,
            header - 12,
        )
        width, height, baseline = measure_text(instruction, face, scale, max(1, thickness - 1))
        draw_text(
            frame,
            instruction,
            (int((self.width - width) / 2), int(header / 2 + (height - baseline) / 2)),
            face,
            scale,
            max(1, thickness - 1),
            self.theme.foreground,
        )

        radius = max(8, int(min(cell_w, cell_h) * float(opts["radius_scale"])))
        jitter = float(opts["jitter"])
        targets: List[Dict[str, Any]] = []
        index = 0
        for row in range(rows):
            for col in range(cols):
                if index >= len(items):
                    break
                item = items[index]
                cx = margin + int(
                    (col + 0.5) * cell_w + self.rng.uniform(-jitter, jitter) * cell_w * 0.5
                )
                cy = header + int(
                    (row + 0.5) * cell_h + self.rng.uniform(-jitter, jitter) * cell_h * 0.5
                )
                cx = max(margin + radius, min(self.width - margin - radius, cx))
                cy = max(header + radius, min(self.height - margin - radius, cy))
                angle = self.rng.uniform(-18, 18)
                shadow = blend(self.theme.background, self.theme.foreground, 0.22)
                draw_shape(frame, item["shape"], (cx + 3, cy + 3), radius, shadow, angle=angle)
                draw_shape(
                    frame,
                    item["shape"],
                    (cx, cy),
                    radius,
                    item["rgb"],
                    angle=angle,
                    outline=blend(item["rgb"], (0, 0, 0), 0.35),
                    outline_thickness=2,
                )
                if item["target"]:
                    targets.append(
                        {
                            "x": cx,
                            "y": cy,
                            "shape": item["shape"],
                            "color": item["color"],
                            "radius": radius,
                        }
                    )
                index += 1

        return self._result(
            [frame],
            answer=[[target["x"], target["y"]] for target in targets],
            text=None,
            metadata={
                "instruction": instruction,
                "target_shape": target_shape,
                "target_color": target_color,
                "targets": targets,
                "decoy_count": len(items) - len(targets),
                "radius": radius,
                "tolerance": radius,
            },
        )


__all__ = ["ClickCaptcha"]

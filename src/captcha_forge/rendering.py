"""Vectorised rendering primitives used by the generators.

Every frame is a contiguous ``uint8`` BGR array with shape ``(height, width, 3)``.
Masks are single-channel ``uint8`` arrays where ``0`` is transparent and ``255``
is fully opaque. Compositing is done with NumPy slices rather than per-pixel
Python loops, which is the main performance improvement over the original
implementation.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Sequence, Tuple

import cv2
import numpy as np

from .colors import RGB, blend, to_bgr
from .fonts import measure_text, resolve_font_face

Point = Tuple[int, int]


def new_frame(width: int, height: int, background: RGB) -> np.ndarray:
    """Create a BGR frame filled with ``background``."""

    frame = np.empty((height, width, 3), dtype=np.uint8)
    frame[:] = to_bgr(background)
    return frame


def blit_mask(
    frame: np.ndarray,
    mask: np.ndarray,
    color: RGB,
    x: int,
    y: int,
    alpha: float = 1.0,
) -> None:
    """Composite a single-channel mask onto ``frame`` in-place.

    The operation clips automatically at frame boundaries. ``alpha`` scales the
    mask, so ``0.25`` produces a subtle background glyph.
    """

    if alpha <= 0 or mask.size == 0:
        return
    if mask.dtype != np.uint8:
        mask = mask.astype(np.uint8)
    height, width = mask.shape[:2]
    x = int(x)
    y = int(y)
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(frame.shape[1], x + width), min(frame.shape[0], y + height)
    if x0 >= x1 or y0 >= y1:
        return

    source = mask[y0 - y : y1 - y, x0 - x : x1 - x].astype(np.float32)
    factor = (source / 255.0) * min(1.0, max(0.0, alpha))
    roi = frame[y0:y1, x0:x1].astype(np.float32)
    colour = np.asarray(to_bgr(color), dtype=np.float32)
    roi *= 1.0 - factor[..., None]
    roi += colour * factor[..., None]
    frame[y0:y1, x0:x1] = np.clip(roi, 0, 255).astype(np.uint8)


def blit_image_mask(
    frame: np.ndarray,
    image: np.ndarray,
    mask: np.ndarray,
    x: int,
    y: int,
    alpha: float = 1.0,
) -> None:
    """Composite a BGR image through a mask onto ``frame`` in-place."""

    if alpha <= 0 or mask.size == 0 or image.size == 0:
        return
    height, width = mask.shape[:2]
    x, y = int(x), int(y)
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(frame.shape[1], x + width), min(frame.shape[0], y + height)
    if x0 >= x1 or y0 >= y1:
        return

    source = image[y0 - y : y1 - y, x0 - x : x1 - x].astype(np.float32)
    source_mask = mask[y0 - y : y1 - y, x0 - x : x1 - x].astype(np.float32)
    factor = (source_mask / 255.0) * min(1.0, max(0.0, alpha))
    roi = frame[y0:y1, x0:x1].astype(np.float32)
    roi *= 1.0 - factor[..., None]
    roi += source * factor[..., None]
    frame[y0:y1, x0:x1] = np.clip(roi, 0, 255).astype(np.uint8)


def blit_mask_onto(target: np.ndarray, mask: np.ndarray, x: int, y: int) -> None:
    """Merge ``mask`` into a target mask using ``maximum`` with clipping."""

    if mask.size == 0:
        return
    height, width = mask.shape[:2]
    x, y = int(x), int(y)
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(target.shape[1], x + width), min(target.shape[0], y + height)
    if x0 >= x1 or y0 >= y1:
        return
    target[y0:y1, x0:x1] = np.maximum(
        target[y0:y1, x0:x1],
        mask[y0 - y : y1 - y, x0 - x : x1 - x],
    )


def rotate_mask(mask: np.ndarray, angle: float, border: int = 0) -> np.ndarray:
    """Rotate a mask while expanding the canvas so nothing is clipped."""

    if abs(angle) < 0.01:
        return mask
    height, width = mask.shape[:2]
    centre = (width / 2.0, height / 2.0)
    matrix = cv2.getRotationMatrix2D(centre, angle, 1.0)
    cos = abs(matrix[0, 0])
    sin = abs(matrix[0, 1])
    new_width = int(math.ceil(height * sin + width * cos))
    new_height = int(math.ceil(height * cos + width * sin))
    matrix[0, 2] += new_width / 2.0 - centre[0]
    matrix[1, 2] += new_height / 2.0 - centre[1]
    return cv2.warpAffine(
        mask,
        matrix,
        (new_width, new_height),
        flags=cv2.INTER_LINEAR,
        borderValue=border,
    )


def shear_mask(mask: np.ndarray, shear_x: float = 0.0, shear_y: float = 0.0) -> np.ndarray:
    """Shear a mask with automatic canvas expansion."""

    if abs(shear_x) < 1e-6 and abs(shear_y) < 1e-6:
        return mask
    height, width = mask.shape[:2]
    pad = 2
    new_width = int(math.ceil(width + abs(shear_x) * height)) + pad * 2
    new_height = int(math.ceil(height + abs(shear_y) * width)) + pad * 2
    matrix = np.array(
        [
            [1.0, shear_x, pad + max(0.0, -shear_x * height)],
            [shear_y, 1.0, pad + max(0.0, -shear_y * width)],
        ],
        dtype=np.float32,
    )
    return cv2.warpAffine(
        mask,
        matrix,
        (new_width, new_height),
        flags=cv2.INTER_LINEAR,
        borderValue=0,
    )


def render_text_mask(
    text: str,
    font_face: int,
    font_scale: float,
    font_thickness: int,
    padding: int = 6,
    rotation: float = 0.0,
    shear: float = 0.0,
) -> np.ndarray:
    """Render text into a transparent mask, optionally rotated and sheared."""

    if not text:
        return np.zeros((1, 1), dtype=np.uint8)
    font_face = resolve_font_face(font_face)
    width, height, baseline = measure_text(text, font_face, font_scale, font_thickness)
    canvas_width = max(1, width + padding * 2)
    canvas_height = max(1, height + baseline + padding * 2)
    mask = np.zeros((canvas_height, canvas_width), dtype=np.uint8)
    cv2.putText(
        mask,
        text,
        (padding, padding + height),
        font_face,
        font_scale,
        255,
        font_thickness,
        cv2.LINE_AA,
    )
    if abs(shear) > 1e-6:
        mask = shear_mask(mask, shear_x=shear)
    if abs(rotation) > 0.01:
        mask = rotate_mask(mask, rotation)
    return mask


class GlyphCache:
    """Cache rendered glyph masks keyed by character, rotation, and scale."""

    def __init__(
        self,
        font_face: int,
        font_scale: float,
        font_thickness: int,
        padding: int = 4,
    ) -> None:
        self.font_face = resolve_font_face(font_face)
        self.font_scale = float(font_scale)
        self.font_thickness = int(font_thickness)
        self.padding = int(padding)
        self._cache: Dict[Tuple[str, float, float], np.ndarray] = {}

    def get(self, char: str, rotation: float = 0.0, scale: float = 1.0) -> np.ndarray:
        key = (char, round(float(rotation), 1), round(float(scale), 2))
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        mask = render_text_mask(
            char,
            self.font_face,
            self.font_scale,
            self.font_thickness,
            padding=self.padding,
            rotation=rotation,
        )
        if abs(scale - 1.0) > 1e-3:
            width = max(1, int(round(mask.shape[1] * scale)))
            height = max(1, int(round(mask.shape[0] * scale)))
            mask = cv2.resize(mask, (width, height), interpolation=cv2.INTER_LINEAR)
        self._cache[key] = mask
        return mask

    def clear(self) -> None:
        self._cache.clear()


def apply_wave(
    image: np.ndarray,
    amplitude: float,
    wavelength: float,
    phase: float = 0.0,
    axis: str = "horizontal",
    border_value: Any = 0,
) -> np.ndarray:
    """Apply a sinusoidal displacement with ``cv2.remap``.

    ``axis='horizontal'`` shifts rows left/right; ``axis='vertical'`` shifts
    columns up/down.
    """

    if abs(amplitude) < 1e-6 or image.size == 0:
        return image
    height, width = image.shape[:2]
    wavelength = max(1.0, float(wavelength))
    if axis == "vertical":
        map_x = np.tile(np.arange(width, dtype=np.float32), (height, 1))
        offsets = amplitude * np.sin(2.0 * np.pi * np.arange(width) / wavelength + phase)
        map_y = np.tile(np.arange(height, dtype=np.float32)[:, None], (1, width)) + offsets[None, :]
    else:
        map_x = np.tile(np.arange(width, dtype=np.float32), (height, 1))
        offsets = amplitude * np.sin(2.0 * np.pi * np.arange(height) / wavelength + phase)
        map_x = (map_x + offsets[:, None]).astype(np.float32)
        map_y = np.tile(np.arange(height, dtype=np.float32)[:, None], (1, width))
    map_x = np.ascontiguousarray(map_x, dtype=np.float32)
    map_y = np.ascontiguousarray(map_y, dtype=np.float32)
    return cv2.remap(
        image,
        map_x,
        map_y,
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=border_value,
    )


def add_noise(
    frame: np.ndarray, amount: float, rng: np.random.Generator, monochrome: bool = True
) -> None:
    """Add uniform pixel noise in-place. ``amount`` is a fraction of 255."""

    if amount <= 0:
        return
    strength = max(1, int(round(255 * min(1.0, amount))))
    shape = (frame.shape[0], frame.shape[1], 1) if monochrome else frame.shape
    noise = rng.integers(-strength, strength + 1, size=shape, dtype=np.int16)
    result = frame.astype(np.int16) + noise
    frame[:] = np.clip(result, 0, 255).astype(np.uint8)


def add_speckles(
    frame: np.ndarray,
    count: int,
    color: RGB,
    rng: np.random.Generator,
    radius: Tuple[int, int] = (1, 2),
    alpha: float = 0.6,
) -> None:
    """Draw small anti-aliased dots over the frame."""

    if count <= 0:
        return
    overlay = frame.copy()
    height, width = frame.shape[:2]
    for _ in range(count):
        x = int(rng.integers(0, width))
        y = int(rng.integers(0, height))
        r = int(rng.integers(radius[0], radius[1] + 1))
        cv2.circle(overlay, (x, y), r, to_bgr(color), -1, lineType=cv2.LINE_AA)
    cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0, dst=frame)


def add_lines(
    frame: np.ndarray,
    count: int,
    color: RGB,
    rng: np.random.Generator,
    thickness: Tuple[int, int] = (1, 2),
    alpha: float = 0.55,
) -> None:
    """Draw random interference lines over the frame."""

    if count <= 0:
        return
    overlay = frame.copy()
    height, width = frame.shape[:2]
    for _ in range(count):
        x1 = int(rng.integers(-width // 6, width))
        y1 = int(rng.integers(0, height))
        x2 = int(rng.integers(0, width + width // 6))
        y2 = int(rng.integers(0, height))
        cv2.line(
            overlay,
            (x1, y1),
            (x2, y2),
            to_bgr(color),
            int(rng.integers(thickness[0], thickness[1] + 1)),
            lineType=cv2.LINE_AA,
        )
    cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0, dst=frame)


def add_blobs(
    frame: np.ndarray,
    count: int,
    rng: np.random.Generator,
    colors: Sequence[RGB],
    alpha: float = 0.18,
    radius_scale: float = 0.45,
) -> None:
    """Add soft large colour blobs, useful for slider backgrounds."""

    if count <= 0 or not colors:
        return
    overlay = frame.copy()
    height, width = frame.shape[:2]
    for _ in range(count):
        centre = (int(rng.integers(0, width)), int(rng.integers(0, height)))
        radius = int(rng.uniform(0.15, radius_scale) * min(width, height))
        colour = colors[int(rng.integers(0, len(colors)))]
        cv2.circle(overlay, centre, radius, to_bgr(colour), -1, lineType=cv2.LINE_AA)
    cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0, dst=frame)


def make_gradient(
    width: int,
    height: int,
    top: RGB,
    bottom: RGB,
    rng: np.random.Generator | None = None,
    blob_count: int = 0,
    blob_alpha: float = 0.18,
) -> np.ndarray:
    """Create a vertical gradient, optionally decorated with colour blobs."""

    t = np.linspace(0.0, 1.0, height, dtype=np.float32)[:, None, None]
    top_array = np.asarray(top, dtype=np.float32)
    bottom_array = np.asarray(bottom, dtype=np.float32)
    rgb = top_array * (1.0 - t) + bottom_array * t
    rgb = np.repeat(rgb, width, axis=1)
    frame = np.clip(rgb, 0, 255).astype(np.uint8)[:, :, ::-1].copy()
    if rng is not None and blob_count > 0:
        palette = [
            blend(top, (255, 255, 255), 0.25),
            blend(bottom, (0, 0, 0), 0.22),
            blend(top, bottom, 0.5),
        ]
        add_blobs(frame, blob_count, rng, palette, alpha=blob_alpha)
    return frame


def add_vignette(frame: np.ndarray, strength: float = 0.28) -> None:
    """Darken the frame edges in-place."""

    if strength <= 0:
        return
    height, width = frame.shape[:2]
    yy, xx = np.mgrid[0:height, 0:width]
    dx = (xx - width / 2.0) / max(1.0, width / 2.0)
    dy = (yy - height / 2.0) / max(1.0, height / 2.0)
    distance = np.sqrt(dx * dx + dy * dy)
    factor = 1.0 - strength * np.clip(distance, 0.0, 1.0) ** 2
    frame[:] = np.clip(frame.astype(np.float32) * factor[..., None], 0, 255).astype(np.uint8)


def draw_text(
    frame: np.ndarray,
    text: str,
    origin: Point,
    font_face: int,
    font_scale: float,
    font_thickness: int,
    color: RGB,
    shadow: RGB | None = None,
    shadow_offset: int = 1,
) -> None:
    """Draw text with an optional drop shadow."""

    font_face = resolve_font_face(font_face)
    if shadow is not None and shadow_offset:
        cv2.putText(
            frame,
            text,
            (origin[0] + shadow_offset, origin[1] + shadow_offset),
            font_face,
            font_scale,
            to_bgr(shadow),
            font_thickness,
            cv2.LINE_AA,
        )
    cv2.putText(
        frame,
        text,
        origin,
        font_face,
        font_scale,
        to_bgr(color),
        font_thickness,
        cv2.LINE_AA,
    )


def draw_text_centered(
    frame: np.ndarray,
    text: str,
    centre: Point,
    font_face: int,
    font_scale: float,
    font_thickness: int,
    color: RGB,
) -> None:
    """Draw text centred on ``centre``."""

    width, height, baseline = measure_text(
        text, resolve_font_face(font_face), font_scale, font_thickness
    )
    x = int(centre[0] - width / 2)
    y = int(centre[1] + (height - baseline) / 2)
    draw_text(frame, text, (x, y), font_face, font_scale, font_thickness, color)


def shape_points(shape: str, centre: Point, radius: float, angle: float = 0.0) -> np.ndarray:
    """Return polygon points for a shape."""

    cx, cy = centre
    rotation = math.radians(angle)
    key = shape.lower()

    if key == "square":
        corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
        scale = radius / math.sqrt(2.0)
        points = [(cx + x * scale, cy + y * scale) for x, y in corners]
    elif key == "diamond":
        points = [
            (cx, cy - radius),
            (cx + radius, cy),
            (cx, cy + radius),
            (cx - radius, cy),
        ]
    elif key == "triangle":
        points = [
            (
                cx + radius * math.cos(rotation - math.pi / 2),
                cy + radius * math.sin(rotation - math.pi / 2),
            ),
            (
                cx + radius * math.cos(rotation + math.pi / 6),
                cy + radius * math.sin(rotation + math.pi / 6),
            ),
            (
                cx + radius * math.cos(rotation + 5 * math.pi / 6),
                cy + radius * math.sin(rotation + 5 * math.pi / 6),
            ),
        ]
    elif key == "star":
        points = []
        for index in range(10):
            r = radius if index % 2 == 0 else radius * 0.45
            theta = rotation - math.pi / 2 + index * math.pi / 5
            points.append((cx + r * math.cos(theta), cy + r * math.sin(theta)))
    elif key == "hexagon":
        points = [
            (
                cx + radius * math.cos(rotation + index * math.pi / 3),
                cy + radius * math.sin(rotation + index * math.pi / 3),
            )
            for index in range(6)
        ]
    else:
        raise ValueError(f"Unknown shape {shape!r}")

    if key not in {"triangle", "star", "hexagon"} and abs(angle) > 1e-6:
        cos_a, sin_a = math.cos(rotation), math.sin(rotation)
        points = [
            (cx + (x - cx) * cos_a - (y - cy) * sin_a, cy + (x - cx) * sin_a + (y - cy) * cos_a)
            for x, y in points
        ]
    return np.array(points, dtype=np.int32)


def draw_shape(
    frame: np.ndarray,
    shape: str,
    centre: Point,
    radius: int,
    color: RGB,
    angle: float = 0.0,
    outline: RGB | None = None,
    outline_thickness: int = 2,
) -> None:
    """Draw a filled shape with an anti-aliased outline."""

    if shape.lower() == "circle":
        cv2.circle(frame, centre, int(radius), to_bgr(color), -1, lineType=cv2.LINE_AA)
        if outline is not None:
            cv2.circle(
                frame, centre, int(radius), to_bgr(outline), outline_thickness, lineType=cv2.LINE_AA
            )
        return

    points = shape_points(shape, centre, float(radius), angle)
    cv2.fillPoly(frame, [points], to_bgr(color), lineType=cv2.LINE_AA)
    if outline is not None:
        cv2.polylines(
            frame, [points], True, to_bgr(outline), outline_thickness, lineType=cv2.LINE_AA
        )


def outline_mask(
    frame: np.ndarray,
    mask: np.ndarray,
    color: RGB,
    thickness: int = 2,
    offset: Point = (0, 0),
) -> None:
    """Draw the outer contour of a mask onto the frame."""

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return
    shifted = [contour + np.array([[offset[0], offset[1]]], dtype=np.int32) for contour in contours]
    cv2.drawContours(frame, shifted, -1, to_bgr(color), thickness, lineType=cv2.LINE_AA)


def make_puzzle_mask(size: int, tab_radius: int, rng: Any) -> np.ndarray:
    """Create a puzzle-piece mask with random tabs and notches."""

    pad = max(4, int(tab_radius))
    canvas = size + pad * 2
    mask = np.zeros((canvas, canvas), dtype=np.uint8)
    radius = max(2, size // 14)
    cv2.rectangle(mask, (pad + radius, pad), (pad + size - radius, pad + size), 255, -1)
    cv2.rectangle(mask, (pad, pad + radius), (pad + size, pad + size - radius), 255, -1)
    for corner in [
        (pad + radius, pad + radius),
        (pad + size - radius, pad + radius),
        (pad + radius, pad + size - radius),
        (pad + size - radius, pad + size - radius),
    ]:
        cv2.circle(mask, corner, radius, 255, -1)

    sides = ["top", "right", "bottom", "left"]
    rng.shuffle(sides)
    for side in sides[:2]:
        direction = 1 if rng.random() < 0.65 else -1
        tab = int(tab_radius)
        if side == "top":
            centre = (pad + size // 2, pad)
        elif side == "bottom":
            centre = (pad + size // 2, pad + size)
        elif side == "left":
            centre = (pad, pad + size // 2)
        else:
            centre = (pad + size, pad + size // 2)
        cv2.circle(mask, centre, tab, 255 if direction > 0 else 0, -1, lineType=cv2.LINE_AA)
        if direction > 0:
            # Re-open the overlap between the tab and the body.
            if side in {"top", "bottom"}:
                y = pad if side == "top" else pad + size
                cv2.rectangle(mask, (centre[0] - tab, y - 1), (centre[0] + tab, y + 1), 255, -1)
            else:
                x = pad if side == "left" else pad + size
                cv2.rectangle(mask, (x - 1, centre[1] - tab), (x + 1, centre[1] + tab), 255, -1)
    return mask

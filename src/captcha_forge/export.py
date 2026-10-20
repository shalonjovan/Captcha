"""Frame export helpers."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Sequence

import cv2
import numpy as np
from PIL import Image

from .exceptions import ExportError

_STATIC_FORMATS = {"png", "jpeg", "jpg", "bmp", "tiff", "tif"}
_SUFFIXES = {
    ".png": "png",
    ".jpg": "jpeg",
    ".jpeg": "jpeg",
    ".bmp": "bmp",
    ".tif": "tiff",
    ".tiff": "tiff",
    ".gif": "gif",
    ".webp": "webp",
    ".mp4": "mp4",
}
_ENCODE_EXT = {
    "png": ".png",
    "jpeg": ".jpg",
    "bmp": ".bmp",
    "tiff": ".tiff",
}


def normalise_format(value: str) -> str:
    """Normalise a format name or file suffix."""

    text = value.strip().lower().lstrip(".")
    aliases = {
        "jpg": "jpeg",
        "tif": "tiff",
        "mpeg4": "mp4",
        "m4v": "mp4",
    }
    return aliases.get(text, text)


def format_for_path(path: Path, fallback: str = "png") -> str:
    """Infer an output format from a path suffix."""

    suffix = path.suffix.lower()
    if suffix in _SUFFIXES:
        return _SUFFIXES[suffix]
    return normalise_format(fallback)


def _ensure_uint8_bgr(frame: np.ndarray) -> np.ndarray:
    if frame.dtype != np.uint8:
        frame = np.clip(frame, 0, 255).astype(np.uint8)
    if frame.ndim == 2:
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    if frame.ndim != 3 or frame.shape[2] != 3:
        raise ExportError("frames must have shape (height, width, 3)")
    return np.ascontiguousarray(frame)


def encode_image_bytes(frame: np.ndarray, format: str = "png", quality: int | None = None) -> bytes:
    """Encode one frame as an image byte string."""

    fmt = normalise_format(format)
    if fmt in {"gif", "webp", "mp4"}:
        raise ExportError(f"Use encode_animation_bytes() for {fmt!r} output")
    ext = _ENCODE_EXT.get(fmt)
    if ext is None:
        raise ExportError(f"Unsupported image format {format!r}")
    frame = _ensure_uint8_bgr(frame)
    params = []
    if quality is not None and fmt == "jpeg":
        params = [cv2.IMWRITE_JPEG_QUALITY, int(max(1, min(100, quality)))]
    ok, buffer = cv2.imencode(ext, frame, params)
    if not ok:
        raise ExportError(f"OpenCV could not encode the frame as {fmt}")
    return bytes(buffer.tobytes())


def _pil_frames(frames: Sequence[np.ndarray]) -> list:
    return [
        Image.fromarray(cv2.cvtColor(_ensure_uint8_bgr(frame), cv2.COLOR_BGR2RGB))
        for frame in frames
    ]


def encode_animation_bytes(
    frames: Sequence[np.ndarray],
    fps: float = 30.0,
    format: str = "gif",
    quality: int = 80,
) -> bytes:
    """Encode an animated GIF or WebP and return the bytes."""

    if not frames:
        raise ExportError("at least one frame is required")
    fmt = normalise_format(format)
    if fmt not in {"gif", "webp"}:
        raise ExportError(f"Unsupported animation format {format!r}; use 'gif' or 'webp'")
    images = _pil_frames(frames)
    buffer = BytesIO()
    duration = max(10, int(round(1000.0 / max(1.0, float(fps)))))
    options: dict = {
        "save_all": True,
        "append_images": images[1:],
        "duration": duration,
        "loop": 0,
        "optimize": True,
    }
    if fmt == "webp":
        options.update({"quality": int(max(1, min(100, quality))), "method": 6})
    try:
        images[0].save(buffer, format=fmt.upper(), **options)
    except Exception as exc:  # Pillow raises different errors depending on version.
        raise ExportError(f"Could not encode {fmt.upper()} output: {exc}") from exc
    return buffer.getvalue()


def save_frames(
    frames: Sequence[np.ndarray],
    path: str | Path,
    fps: float = 30.0,
    format: str | None = None,
    quality: int | None = None,
) -> Path:
    """Write frames to an image, GIF, WebP, or MP4 file.

    A static format writes the first frame; use GIF, WebP, or MP4 for
    animation.
    """

    if not frames:
        raise ExportError("at least one frame is required")
    target = Path(path).expanduser()
    fmt = normalise_format(format) if format else format_for_path(target)
    if not target.suffix:
        suffix = ".jpg" if fmt == "jpeg" else f".{fmt}"
        target = target.with_suffix(suffix)
    target.parent.mkdir(parents=True, exist_ok=True)

    if fmt in {"gif", "webp"}:
        target.write_bytes(
            encode_animation_bytes(frames, fps=fps, format=fmt, quality=quality or 80)
        )
        return target

    if fmt == "mp4":
        first = _ensure_uint8_bgr(frames[0])
        height, width = first.shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore[attr-defined]
        writer = cv2.VideoWriter(str(target), fourcc, float(fps), (width, height))
        if not writer.isOpened():
            raise ExportError(
                "OpenCV could not open an MP4 writer. Install a build with the mp4v codec, "
                "or export a GIF/WebP instead."
            )
        try:
            for frame in frames:
                frame = _ensure_uint8_bgr(frame)
                if frame.shape[1] != width or frame.shape[0] != height:
                    frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
                writer.write(frame)
        finally:
            writer.release()
        return target

    if fmt not in _STATIC_FORMATS:
        raise ExportError(f"Unsupported output format {fmt!r}")

    target.write_bytes(encode_image_bytes(frames[0], fmt, quality=quality))
    return target


__all__ = [
    "normalise_format",
    "format_for_path",
    "encode_image_bytes",
    "encode_animation_bytes",
    "save_frames",
]

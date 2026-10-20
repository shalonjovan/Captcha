"""The result object returned by every generator."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, Tuple

import numpy as np

from .exceptions import ExportError


@dataclass
class CaptchaResult:
    """Frames, solution, and type-specific metadata for one challenge.

    ``frames`` follows OpenCV's BGR convention. ``answer`` is the value a user
    should produce to solve the challenge (a string for text-based challenges,
    coordinates for click challenges, a sequence for pattern challenges, and so
    on). ``text`` is the text that was rendered when applicable.

    The object is sequence-like, so existing code that iterates over the result
    or indexes it still receives frames.
    """

    captcha_type: str
    frames: Tuple[np.ndarray, ...]
    answer: Any = None
    text: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    assets: Dict[str, np.ndarray] = field(default_factory=dict)
    fps: int = 30
    suggested_format: str = "png"

    def __post_init__(self) -> None:
        self.frames = tuple(self.frames)
        if not self.frames:
            raise ValueError("CaptchaResult requires at least one frame")
        for frame in self.frames:
            if not isinstance(frame, np.ndarray) or frame.ndim != 3 or frame.shape[2] != 3:
                raise ValueError("every frame must be a BGR numpy array with shape (h, w, 3)")
        if self.fps <= 0:
            raise ValueError("fps must be positive")
        self.metadata = dict(self.metadata)
        self.assets = dict(self.assets)

    @property
    def image(self) -> np.ndarray:
        """The first frame."""

        return self.frames[0]

    @property
    def size(self) -> Tuple[int, int]:
        """Frame size as ``(width, height)``."""

        height, width = self.frames[0].shape[:2]
        return width, height

    @property
    def duration(self) -> float:
        """Approximate duration in seconds."""

        return len(self.frames) / float(self.fps)

    def save(
        self,
        path: str | Path,
        *,
        format: str | None = None,
        fps: float | None = None,
        quality: int | None = None,
    ) -> Path:
        """Write the challenge to disk and return the written path."""

        from .export import save_frames

        target = Path(path)
        if format is None and not target.suffix:
            format = self.suggested_format
        return save_frames(
            self.frames,
            target,
            fps=self.fps if fps is None else fps,
            format=format,
            quality=quality,
        )

    def to_bytes(self, format: str = "png", quality: int | None = None) -> bytes:
        """Encode the first frame or a GIF/WebP animation to bytes."""

        from .export import encode_animation_bytes, encode_image_bytes

        fmt = format.strip().lower().lstrip(".")
        if fmt in {"gif", "webp"}:
            return encode_animation_bytes(
                self.frames, fps=self.fps, format=fmt, quality=quality or 80
            )
        if fmt == "mp4":
            raise ExportError("MP4 byte output is not supported; save to a file instead")
        return encode_image_bytes(self.frames[0], format=fmt, quality=quality)

    def __iter__(self) -> Iterator[np.ndarray]:
        return iter(self.frames)

    def __len__(self) -> int:
        return len(self.frames)

    def __getitem__(self, index: int | slice) -> np.ndarray | Tuple[np.ndarray, ...]:
        return self.frames[index]

    def __repr__(self) -> str:
        width, height = self.size
        return (
            f"CaptchaResult(type={self.captcha_type!r}, frames={len(self.frames)}, "
            f"size={width}x{height}, answer={self.answer!r})"
        )


__all__ = ["CaptchaResult"]

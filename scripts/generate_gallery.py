#!/usr/bin/env python
"""Generate the documentation gallery and a 3x3 overview contact sheet."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np

from captcha_forge import Captcha, available_types


def _fit(image: np.ndarray, width: int, height: int) -> np.ndarray:
    h, w = image.shape[:2]
    scale = min(width / w, height / h)
    resized = cv2.resize(
        image, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA
    )
    canvas = np.full((height, width, 3), (245, 245, 242), dtype=np.uint8)
    y = (height - resized.shape[0]) // 2
    x = (width - resized.shape[1]) // 2
    canvas[y : y + resized.shape[0], x : x + resized.shape[1]] = resized
    return canvas


def _contact_sheet(images: List[Tuple[str, np.ndarray]], path: Path) -> None:
    cell_w, cell_h = 420, 290
    padding = 18
    label_h = 38
    cols = 3
    rows = (len(images) + cols - 1) // cols
    width = cols * cell_w + (cols + 1) * padding
    height = rows * (cell_h + label_h) + (rows + 1) * padding
    sheet = np.full((height, width, 3), (245, 245, 242), dtype=np.uint8)

    for index, (name, image) in enumerate(images):
        row, col = divmod(index, cols)
        x = padding + col * (cell_w + padding)
        y = padding + row * (cell_h + label_h + padding)
        sheet[y : y + cell_h, x : x + cell_w] = _fit(image, cell_w, cell_h)
        cv2.putText(
            sheet,
            name,
            (x + 8, y + cell_h + 28),
            cv2.FONT_HERSHEY_DUPLEX,
            0.72,
            (30, 30, 34),
            1,
            cv2.LINE_AA,
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), sheet)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default="docs/assets/gallery",
        help="Directory for the gallery assets.",
    )
    parser.add_argument("--seed", type=int, default=2026, help="Base seed.")
    parser.add_argument("--duration", type=float, default=1.2, help="Animated sample duration.")
    parser.add_argument("--fps", type=int, default=8, help="Animated sample frame rate.")
    parser.add_argument("--animated-width", type=int, default=360, help="Animated sample width.")
    parser.add_argument("--animated-height", type=int, default=130, help="Animated sample height.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    first_frames: List[Tuple[str, np.ndarray]] = []

    for index, name in enumerate(sorted(available_types())):
        info = Captcha.describe(name)
        kwargs: Dict[str, object] = {"seed": args.seed + index}
        if info["animated"]:
            kwargs.update(
                {
                    "duration": args.duration,
                    "fps": args.fps,
                    "width": args.animated_width,
                    "height": args.animated_height,
                }
            )
        result = Captcha(name, **kwargs).generate()
        suffix = result.suggested_format
        path = result.save(output_dir / f"{name}.{suffix}")
        first_frames.append((name, result.image.copy()))
        print(f"{name:<10} -> {path}  answer={result.answer!r}")

    _contact_sheet(first_frames, output_dir / "overview.png")
    print(f"overview   -> {output_dir / 'overview.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

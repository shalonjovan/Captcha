#!/usr/bin/env python
"""Rough generation benchmark for every built-in CAPTCHA type."""

from __future__ import annotations

import argparse
import time

from captcha_forge import Captcha, available_types


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeat", type=int, default=3, help="Number of timed runs per type.")
    parser.add_argument(
        "--duration", type=float, default=2.0, help="Animation duration in seconds."
    )
    parser.add_argument("--fps", type=int, default=30, help="Animation frame rate.")
    args = parser.parse_args()

    print(f"{'type':<10} {'frames':>7} {'seconds':>10} {'frames/s':>12}")
    print("-" * 43)
    for name in sorted(available_types()):
        info = Captcha.describe(name)
        kwargs = {"seed": 123}
        if info["animated"]:
            kwargs.update({"duration": args.duration, "fps": args.fps})
        best = float("inf")
        frames = 0
        for _ in range(max(1, args.repeat)):
            started = time.perf_counter()
            result = Captcha(name, **kwargs).generate()
            elapsed = time.perf_counter() - started
            best = min(best, elapsed)
            frames = len(result)
        rate = frames / best if best else 0.0
        print(f"{name:<10} {frames:>7} {best:>10.4f} {rate:>12.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

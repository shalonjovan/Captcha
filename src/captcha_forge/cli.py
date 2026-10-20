"""Command-line interface for Captcha Forge."""

from __future__ import annotations

import argparse
import json
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Dict, Sequence

import numpy as np

from .exceptions import CaptchaError
from .facade import Captcha
from .fonts import FONT_FACES
from .registry import available_types


def _version() -> str:
    try:
        return version("captcha-forge")
    except PackageNotFoundError:  # pragma: no cover
        return "1.0.0"


def _parse_options(pairs: Sequence[str]) -> Dict[str, Any]:
    options: Dict[str, Any] = {}
    for pair in pairs:
        if "=" not in pair:
            raise CaptchaError(f"--option expects KEY=VALUE, got {pair!r}")
        key, raw = pair.split("=", 1)
        key = key.strip()
        if not key:
            raise CaptchaError("--option keys cannot be empty")
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            value = raw
        options[key] = value
    return options


def _jsonable(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _common_kwargs(args: argparse.Namespace) -> Dict[str, Any]:
    kwargs: Dict[str, Any] = {}
    for key in (
        "width",
        "height",
        "fps",
        "duration",
        "seed",
        "text",
        "length",
        "alphabet",
        "color_mode",
        "background",
        "foreground",
        "font",
        "font_scale",
        "font_thickness",
    ):
        value = getattr(args, key, None)
        if value is not None:
            kwargs["font_face" if key == "font" else key] = value
    kwargs.update(_parse_options(getattr(args, "option", []) or []))
    return kwargs


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="captcha-forge",
        description="Generate animated and static CAPTCHA challenges.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {_version()}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List every registered CAPTCHA type.")
    list_parser.set_defaults(func=_cmd_list)

    info_parser = subparsers.add_parser("info", help="Show metadata and options for a type.")
    info_parser.add_argument("type", nargs="?", help="CAPTCHA type; omit to list all types.")
    info_parser.set_defaults(func=_cmd_info)

    generate_parser = subparsers.add_parser("generate", help="Generate one challenge.")
    generate_parser.add_argument("type", help="CAPTCHA type name.")
    generate_parser.add_argument("-o", "--output", help="Output file path.")
    generate_parser.add_argument("--format", help="Output format: png, jpeg, gif, webp, or mp4.")
    generate_parser.add_argument("--width", type=int, help="Frame width in pixels.")
    generate_parser.add_argument("--height", type=int, help="Frame height in pixels.")
    generate_parser.add_argument("--fps", type=int, help="Frames per second.")
    generate_parser.add_argument("--duration", type=float, help="Animation duration in seconds.")
    generate_parser.add_argument("--seed", type=int, help="Seed for reproducible output.")
    generate_parser.add_argument("--text", help="Force the rendered text or expression.")
    generate_parser.add_argument("--length", type=int, help="Random text length.")
    generate_parser.add_argument("--alphabet", help="Characters used for random text.")
    generate_parser.add_argument(
        "--color-mode",
        choices=["light", "dark", "custom"],
        help="Built-in theme or a custom background/foreground pair.",
    )
    generate_parser.add_argument("--background", help="Custom background colour (name/hex).")
    generate_parser.add_argument("--foreground", help="Custom foreground colour (name/hex).")
    generate_parser.add_argument(
        "--font",
        choices=sorted(FONT_FACES),
        help="OpenCV Hershey font name.",
    )
    generate_parser.add_argument("--font-scale", type=float, help="Font scale.")
    generate_parser.add_argument("--font-thickness", type=int, help="Font stroke thickness.")
    generate_parser.add_argument(
        "--option",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Generator-specific option; JSON values are accepted. Repeatable.",
    )
    generate_parser.add_argument("--json", action="store_true", help="Print a JSON report.")
    generate_parser.add_argument(
        "--quiet", action="store_true", help="Suppress human-readable output."
    )
    generate_parser.set_defaults(func=_cmd_generate)

    gallery_parser = subparsers.add_parser("gallery", help="Generate one sample of every type.")
    gallery_parser.add_argument(
        "-o", "--output-dir", default="captcha-gallery", help="Destination directory."
    )
    gallery_parser.add_argument("--types", help="Comma-separated subset of type names.")
    gallery_parser.add_argument(
        "--seed", type=int, help="Base seed; each type gets a different seed."
    )
    gallery_parser.add_argument("--fps", type=int, help="Frames per second for animated types.")
    gallery_parser.add_argument("--duration", type=float, help="Duration for animated types.")
    gallery_parser.add_argument(
        "--quiet", action="store_true", help="Suppress human-readable output."
    )
    gallery_parser.set_defaults(func=_cmd_gallery)

    return parser


def _cmd_list(args: argparse.Namespace) -> int:
    for name, description in available_types().items():
        print(f"{name:<10} {description}")
    return 0


def _cmd_info(args: argparse.Namespace) -> int:
    if args.type is None:
        return _cmd_list(args)
    info = Captcha.describe(args.type)
    print(f"Type: {info['name']}")
    print(f"Description: {info['description']}")
    print(f"Default size: {info['default_size'][0]}x{info['default_size'][1]}")
    print(f"Default format: {info['default_format']}")
    print(f"Animated: {'yes' if info['animated'] else 'no'}")
    if info["options"]:
        print("Options:")
        for option in info["options"]:
            help_text = f"  # {option['help']}" if option["help"] else ""
            print(f"  {option['name']}={option['default']!r}{help_text}")
    return 0


def _output_path(args: argparse.Namespace, result: Any) -> Path:
    if args.output:
        return Path(args.output)
    fmt = args.format or result.suggested_format
    return Path(f"captcha_{args.type}.{fmt}")


def _cmd_generate(args: argparse.Namespace) -> int:
    captcha = Captcha(args.type, **_common_kwargs(args))
    result = captcha.generate()
    output = _output_path(args, result)
    path = result.save(output, format=args.format)

    if args.json:
        report = {
            "type": result.captcha_type,
            "path": str(path),
            "width": result.size[0],
            "height": result.size[1],
            "frames": len(result),
            "fps": result.fps,
            "duration": result.duration,
            "answer": _jsonable(result.answer),
            "text": result.text,
            "metadata": _jsonable(result.metadata),
        }
        print(json.dumps(report, indent=2))
    elif not args.quiet:
        print(f"Saved {path} ({len(result)} frame(s), {result.size[0]}x{result.size[1]})")
        if result.answer is not None:
            print(f"Answer: {result.answer}")
    return 0


def _cmd_gallery(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir)
    names = list(available_types())
    if args.types:
        requested = [name.strip().lower() for name in args.types.split(",") if name.strip()]
        unknown = sorted(set(requested) - set(names))
        if unknown:
            raise CaptchaError(f"Unknown type(s): {', '.join(unknown)}")
        names = requested

    for index, name in enumerate(names):
        info = Captcha.describe(name)
        kwargs: Dict[str, Any] = {}
        if args.seed is not None:
            kwargs["seed"] = args.seed + index
        if args.fps is not None:
            kwargs["fps"] = args.fps
        if args.duration is not None and info["animated"]:
            kwargs["duration"] = args.duration
        elif info["animated"]:
            kwargs["duration"] = 1.5
        result = Captcha(name, **kwargs).generate()
        path = result.save(output_dir / f"{name}.{result.suggested_format}")
        if not args.quiet:
            print(f"{name:<10} -> {path}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""

    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except CaptchaError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


__all__ = ["main"]

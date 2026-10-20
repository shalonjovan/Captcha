"""Generate a few challenges and save them.

Run from the repository root:

    python examples/quickstart.py
"""

from pathlib import Path

from captcha_forge import Captcha

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def main() -> None:
    # Animated text challenge.
    result = Captcha("text", seed=42, duration=2.0).generate()
    path = result.save(OUTPUT_DIR / "text.gif")
    print(f"{path.name}: answer={result.answer!r}, frames={len(result)}")

    # Static distorted image challenge.
    result = Captcha(
        "image",
        seed=7,
        length=5,
        color_mode="dark",
        font_face="duplex",
    ).generate()
    path = result.save(OUTPUT_DIR / "image.png")
    print(f"{path.name}: answer={result.answer!r}, size={result.size}")

    # One-shot helper: no Captcha object needed.
    from captcha_forge import create

    result = create("math", seed=3, operands=2, max_operand=9)
    path = result.save(OUTPUT_DIR / "math.png")
    print(f"{path.name}: answer={result.answer}, text={result.text!r}")


if __name__ == "__main__":
    main()

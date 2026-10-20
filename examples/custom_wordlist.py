"""Use a custom word list for the ``word`` challenge.

Run from the repository root:

    python examples/custom_wordlist.py
"""

from pathlib import Path

from captcha_forge import Captcha

OUTPUT_DIR = Path(__file__).resolve().parent / "output"

WORDS = [
    "harbor",
    "lantern",
    "meadow",
    "cobalt",
    "summit",
    "willow",
    "tundra",
    "pixel",
]


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    result = Captcha(
        "word",
        wordlist=WORDS,
        min_length=5,
        max_length=8,
        seed=11,
    ).generate()

    path = result.save(OUTPUT_DIR / "word-custom.png")
    print(f"Saved {path}; answer={result.answer!r}")


if __name__ == "__main__":
    main()

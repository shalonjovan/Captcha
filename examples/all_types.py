"""Generate one sample of every built-in challenge type.

Run from the repository root:

    python examples/all_types.py
"""

from pathlib import Path

from captcha_forge import Captcha

OUTPUT_DIR = Path(__file__).resolve().parent / "output" / "all-types"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for index, (name, description) in enumerate(Captcha.available_types().items()):
        options = {}
        if Captcha.describe(name)["animated"]:
            # Keep the samples small; the default duration is 3 seconds.
            options["duration"] = 1.0
            options["fps"] = 10

        result = Captcha(name, seed=2026 + index, **options).generate()
        path = result.save(OUTPUT_DIR / f"{name}.{result.suggested_format}")
        answer = result.answer
        if isinstance(answer, list):
            answer = f"{len(answer)} point(s)"
        print(f"{name:<9} {path.name:<12} answer={answer!r}  ({description})")


if __name__ == "__main__":
    main()

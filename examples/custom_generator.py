"""Register and use a custom generator.

Run from the repository root:

    python examples/custom_generator.py
"""

from pathlib import Path

from captcha_forge import Captcha, ConfigurationError, register
from captcha_forge.generators import BaseGenerator
from captcha_forge.rendering import draw_text_centered


@register
class HelloCaptcha(BaseGenerator):
    """A tiny greeting challenge used to demonstrate the plugin API."""

    name = "hello"
    description = "A friendly greeting rendered in the active theme."
    default_size = (360, 140)
    default_format = "png"

    option_defaults = {
        "greeting": "HELLO",
        "shadow": True,
    }
    option_docs = {
        "greeting": "Text displayed in the challenge.",
        "shadow": "Draw a subtle drop shadow behind the greeting.",
    }

    def _validate_options(self) -> None:
        greeting = self.options["greeting"]
        if not isinstance(greeting, str) or not greeting:
            raise ConfigurationError("greeting must be a non-empty string")
        if not isinstance(self.options["shadow"], bool):
            raise ConfigurationError("shadow must be a boolean")

    def generate(self):
        frame = self._new_frame()
        greeting = self.options["greeting"]

        if self.options["shadow"]:
            draw_text_centered(
                frame,
                greeting,
                (self.width // 2 + 2, self.height // 2 + 2),
                self.config.font_face,
                self.config.font_scale,
                self.config.font_thickness,
                self.theme.muted,
            )

        draw_text_centered(
            frame,
            greeting,
            (self.width // 2, self.height // 2),
            self.config.font_face,
            self.config.font_scale,
            self.config.font_thickness,
            self.theme.foreground,
        )

        return self._result(
            [frame],
            answer=greeting,
            text=greeting,
            metadata={"custom_type": True},
        )


def main() -> None:
    output_dir = Path(__file__).resolve().parent / "output"
    output_dir.mkdir(exist_ok=True)

    result = Captcha("hello", greeting="WELCOME", seed=1).generate()
    path = result.save(output_dir / "hello.png")
    print(f"Saved {path} with answer {result.answer!r}")

    # Custom generators appear in the same registry and CLI.
    print("hello" in Captcha.available_types())
    print(Captcha.describe("hello")["options"])


if __name__ == "__main__":
    main()

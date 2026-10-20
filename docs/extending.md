# Extending Captcha Forge

Every built-in type is a subclass of
[`BaseGenerator`](api.md#captcha_forge.generators.base.BaseGenerator). You can add
your own generator in a few lines, and it will participate in the same registry,
CLI, validation, and result API.

## A minimal custom generator

```python
from captcha_forge import ConfigurationError, register
from captcha_forge.generators import BaseGenerator
from captcha_forge.rendering import draw_text_centered


@register
class HelloCaptcha(BaseGenerator):
    name = "hello"
    description = "A friendly greeting rendered in the theme colours."
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
```

Import the module once so the decorator runs:

```python
import mypackage.hello  # noqa: F401  (registers the generator)
from captcha_forge import Captcha

result = Captcha("hello", greeting="WELCOME", seed=1).generate()
result.save("hello.png")
```

The CLI sees registered generators too:

```bash
captcha-forge list
captcha-forge info hello
captcha-forge generate hello -o hello.png --option greeting=WELCOME
```

## What the base class gives you

| Attribute / method | Purpose |
| --- | --- |
| `self.config` | The validated `CaptchaConfig`. |
| `self.theme` | Resolved theme colours (`background`, `foreground`, `muted`, `accent`, `noise`, `line`, `palette`) as RGB. |
| `self.font_face` | Resolved OpenCV font constant. |
| `self.width`, `self.height` | Resolved frame dimensions. |
| `self.rng` | `random.Random` seeded from `config.seed`. |
| `self.np_rng` | `numpy.random.Generator` seeded from `config.seed`. |
| `self.options` | Declared option defaults merged with user values. |
| `self._text()` | Configured `text` or random text from the alphabet/length. |
| `self._new_frame()` | A BGR frame filled with the theme background. |
| `self._frame_count()` | `round(duration * fps)`, minimum 1. |
| `self._result(...)` | Build a `CaptchaResult` with common metadata filled in. |

## Declaring options

Options are declared in `option_defaults`. Unknown option names are rejected
before rendering, and `option_docs` is shown by `captcha-forge info`.

```python
option_defaults = {
    "threshold": 0.5,
    "labels": ("A", "B", "C"),
}
option_docs = {
    "threshold": "Detection threshold between 0 and 1.",
    "labels": "Labels to sample from.",
}
```

The CLI can pass JSON values:

```bash
captcha-forge generate mytype -o out.png \
  --option threshold=0.7 \
  --option 'labels=["X", "Y"]'
```

## Animation

Set `animated = True`, use a GIF/WebP-friendly `default_format`, and build one
frame per iteration:

```python
@register
class PulseCaptcha(BaseGenerator):
    name = "pulse"
    description = "A pulsing circle."
    default_size = (320, 200)
    default_format = "gif"
    animated = True
    option_defaults = {"radius": 40}

    def generate(self):
        frames = []
        total = self._frame_count()
        for index in range(total):
            frame = self._new_frame()
            phase = index / max(1, self.config.fps)
            radius = int(self.options["radius"] * (0.8 + 0.2 * (phase % 1.0)))
            import cv2

            cv2.circle(
                frame,
                (self.width // 2, self.height // 2),
                radius,
                self.theme.accent[::-1],
                -1,
                lineType=cv2.LINE_AA,
            )
            frames.append(frame)
        return self._result(frames, answer="pulse", metadata={"radius": self.options["radius"]})
```

## Using the rendering primitives

The `captcha_forge.rendering` module contains the vectorised helpers used by the
built-in generators:

- `new_frame(width, height, background)` — create a BGR frame.
- `blit_mask(frame, mask, colour, x, y, alpha=1.0)` — composite a mask.
- `blit_image_mask(frame, image, mask, x, y, alpha=1.0)` — composite a BGR image.
- `render_text_mask(text, ...)` — render text into a transparent mask.
- `GlyphCache` — cache glyph masks by character, rotation, and scale.
- `apply_wave`, `add_noise`, `add_lines`, `add_speckles`, `add_vignette`.
- `make_gradient`, `draw_text`, `draw_text_centered`, `draw_shape`.

All masks are `uint8` single-channel arrays; `0` is transparent and `255` is
opaque. Frames are BGR `uint8` arrays.

## Registering under a different name

```python
@register(name="friendly-greeting")
class HelloCaptcha(BaseGenerator):
    ...
```

The registry normalises names to lowercase. Aliases can be added in
`captcha_forge.registry._ALIASES` if you need a second public name, though a
single clear name is usually better.

## Packaging a plugin

A plugin is a normal Python package that depends on `captcha-forge` and imports
its generator module at application startup. There is no hidden global state
beyond the in-process registry, so tests can register a generator in a fixture
and use it immediately.

```toml
[project]
name = "my-captcha-generators"
dependencies = ["captcha-forge>=1.0"]
```

```python
# my_captcha_generators/__init__.py
from .hello import HelloCaptcha  # noqa: F401
```

```python
import my_captcha_generators  # noqa: F401
from captcha_forge import Captcha

Captcha("hello").generate()
```

## Testing a custom generator

```python
from captcha_forge import Captcha


def test_hello_generator():
    result = Captcha("hello", greeting="WELCOME", seed=1).generate()
    assert result.answer == "WELCOME"
    assert result.image.shape == (140, 360, 3)
    assert result.metadata["custom_type"] is True
```

Use `seed=...` for deterministic tests, and assert on the answer and frame shape
rather than exact pixels unless you intentionally snapshot the renderer.

## Next steps

- [API reference](api.md)
- [Challenge types](captcha-types.md)
- [Configuration](configuration.md)
- [Contributing](contributing.md)

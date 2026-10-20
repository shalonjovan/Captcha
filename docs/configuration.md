# Configuration

## Common options

Every generator accepts the following options.

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `width` | `int` | generator default | Frame width in pixels (minimum 32). |
| `height` | `int` | generator default | Frame height in pixels (minimum 32). |
| `fps` | `int` | `30` | Animation frame rate, 1–120. Ignored by static types. |
| `duration` | `float` | `3.0` | Animation duration in seconds, 0.05–120. |
| `seed` | `int \| None` | `None` | Seed for Python and NumPy randomness. |
| `color_mode` | `str` | `"light"` | `"light"`, `"dark"`, or `"custom"`. |
| `background` | colour | `None` | Custom background; required with `color_mode="custom"`. |
| `foreground` | colour | `None` | Custom foreground; required with `color_mode="custom"`. |
| `font_face` | `int \| str` | `"duplex"` | OpenCV Hershey font name or integer constant. |
| `font_scale` | `float` | `2.5` | Base font scale. |
| `font_thickness` | `int` | `2` | Font stroke thickness. |
| `alphabet` | `str` | `"ABCDEFGHJKLMNPQRSTUVWXYZ23456789"` | Characters for random text. |
| `text` | `str \| None` | `None` | Force the rendered text or expression. |
| `length` | `int` | `6` | Random text length when `text` is `None`. |

The default `alphabet` omits `0/O` and `1/I` to reduce accidental ambiguity.

## Colours

Colours accept:

- A named colour: `"red"`, `"blue"`, `"green"`, `"orange"`, `"purple"`,
  `"teal"`, `"pink"`, `"gray"`, `"navy"`, `"gold"`, …
- A hex string: `"#ff8800"` or `"#f80"`.
- An RGB triple: `(255, 136, 0)`.

All public colours are **RGB**. Frames are written in OpenCV's BGR order
internally.

```python
Captcha(
    "image",
    color_mode="custom",
    background="#fff4e0",
    foreground="#223344",
)
```

`color_mode="light"` uses an off-white background with near-black foreground.
`color_mode="dark"` uses a near-black background with an off-white foreground.
For either mode you may override `background`, `foreground`, or both; the
derived muted, noise, line, and accent tones are recalculated from the resulting
pair. The `"ligth"` typo from the original project is accepted and normalized to
`"light"`.

## Fonts

OpenCV ships vector Hershey fonts, so no font files are needed. Friendly names:

| Name | OpenCV constant |
| --- | --- |
| `simplex` | `FONT_HERSHEY_SIMPLEX` |
| `plain` | `FONT_HERSHEY_PLAIN` |
| `duplex` | `FONT_HERSHEY_DUPLEX` |
| `complex` | `FONT_HERSHEY_COMPLEX` |
| `triplex` | `FONT_HERSHEY_TRIPLEX` |
| `complex_small` | `FONT_HERSHEY_COMPLEX_SMALL` |
| `script_simplex` | `FONT_HERSHEY_SCRIPT_SIMPLEX` |
| `script_complex` | `FONT_HERSHEY_SCRIPT_COMPLEX` |
| `italic` | `FONT_HERSHEY_SIMPLEX | FONT_ITALIC` |

```python
Captcha("image", font_face="complex", font_scale=3.0, font_thickness=3)
```

Only printable ASCII can be rendered with Hershey fonts. Passing non-ASCII
`text` raises `ConfigurationError`.

## Type-specific options

Each generator declares its own options. You can inspect them at runtime:

```python
from captcha_forge import Captcha

info = Captcha.describe("slider")
for option in info["options"]:
    print(option["name"], option["default"], option["help"])
```

Or from the command line:

```bash
captcha-forge info slider
```

The options are grouped below; see [Challenge types](captcha-types.md) for
examples and answer formats.

### text

| Option | Default | Description |
| --- | --- | --- |
| `max_rotation` | `15.0` | Maximum glyph rotation in degrees. |
| `min_spacing` | `2` | Minimum foreground character spacing. |
| `max_spacing` | `6` | Maximum foreground character spacing. |
| `bg_spawn_rate` | `10.0` | Background glyphs spawned per second. |
| `bg_speed_min` | `0.6` | Minimum background glyph speed. |
| `bg_speed_max` | `2.0` | Maximum background glyph speed. |
| `initial_bg_count` | `25` | Background glyphs on the first frame. |
| `max_bg_count` | `80` | Maximum simultaneous background glyphs. |
| `bg_alpha` | `0.26` | Background glyph opacity. |
| `bg_scale` | `0.55` | Background glyph size relative to the font. |
| `fg_wave_amplitude` | `0.0` | Vertical foreground wave amplitude. |
| `fg_wave_speed` | `2.0` | Foreground wave speed. |
| `shadow_offset` | `2` | Drop-shadow offset. |
| `margin` | `24` | Safe margin. |
| `noise` | `0.012` | Fine grain noise amount. |

### noise

| Option | Default | Description |
| --- | --- | --- |
| `noise_scale` | `8` | Reusable noise field multiplier (2–32). |
| `grain` | `1` | Noise pixel block size. |
| `speed_x` | `1.0` | Horizontal panning speed. |
| `speed_y` | `0.0` | Vertical panning speed. |
| `bounce_amplitude` | `8.0` | Character bounce amplitude. |
| `bounce_speed` | `2.0` | Character bounce speed. |
| `max_rotation` | `12.0` | Character rotation. |
| `min_spacing` | `2` | Minimum character spacing. |
| `max_spacing` | `8` | Maximum character spacing. |
| `margin` | `24` | Safe margin. |
| `contrast` | `1.15` | Noise-text contrast multiplier. |

### image

| Option | Default | Description |
| --- | --- | --- |
| `max_rotation` | `12.0` | Per-character rotation. |
| `letter_spacing` | `4` | Extra spacing between characters. |
| `char_jitter` | `2` | Vertical jitter. |
| `char_scale` | `0.08` | Per-character scale variation. |
| `shear` | `0.12` | Per-character shear. |
| `wave_amplitude` | `3.5` | Global wave amplitude. |
| `wave_wavelength` | `70.0` | Global wave wavelength. |
| `noise` | `0.045` | Fine grain noise. |
| `line_count` | `4` | Interference lines. |
| `dot_count` | `120` | Interference speckles. |
| `shadow_offset` | `2` | Drop-shadow offset. |
| `margin` | `30` | Safe margin. |
| `vignette` | `0.18` | Edge darkening. |

### word

`word` supports every `image` option plus:

| Option | Default | Description |
| --- | --- | --- |
| `wordlist` | `None` | Custom sequence or whitespace-separated string. |
| `min_length` | `4` | Minimum word length. |
| `max_length` | `8` | Maximum word length. |
| `uppercase` | `True` | Render words in uppercase. |

### math

`math` supports every `image` option plus:

| Option | Default | Description |
| --- | --- | --- |
| `operations` | `("+", "-", "*")` | Operations to sample. |
| `min_operand` | `1` | Minimum operand. |
| `max_operand` | `20` | Maximum operand. |
| `operands` | `2` | Number of operands (2–5). |
| `allow_negative` | `False` | Allow negative intermediate values. |

### slider

| Option | Default | Description |
| --- | --- | --- |
| `piece_size` | `74` | Puzzle piece body size. |
| `tab_radius` | `10` | Tab/notch radius. |
| `target_x` | `None` | Force the gap x position. |
| `gap_y` | `None` | Force the gap y position. |
| `tolerance` | `6` | Accepted pixel error. |
| `background_blobs` | `6` | Background colour blobs. |
| `line_count` | `5` | Background interference lines. |
| `noise` | `0.035` | Background grain. |
| `vignette` | `0.22` | Edge darkening. |
| `start_x` | `14` | Initial piece x position. |

### click

| Option | Default | Description |
| --- | --- | --- |
| `target_count` | `3` | Correct shapes to click. |
| `decoy_count` | `5` | Distractor shapes. |
| `shapes` | `("circle", "square", "triangle", "diamond", "star")` | Shape pool. |
| `colors` | `("red", "blue", "green", "orange", "purple")` | Colour pool. |
| `target_shape` | `None` | Force the target shape. |
| `target_color` | `None` | Force the target colour. |
| `radius_scale` | `0.28` | Shape radius vs. grid cell. |
| `jitter` | `0.18` | Position jitter within a cell. |
| `noise` | `0.025` | Background grain. |
| `dot_count` | `50` | Background speckles. |
| `margin` | `18` | Outer margin. |

### pattern

| Option | Default | Description |
| --- | --- | --- |
| `grid` | `3` | Grid size (2–5). |
| `path_length` | `5` | Numbered dots in the challenge. |
| `dot_radius` | `12` | Outer dot radius. |
| `noise` | `0.025` | Background grain. |
| `margin` | `58` | Outer margin. |
| `vignette` | `0.12` | Edge darkening. |
| `show_instruction` | `True` | Draw the instruction. |

### rotate

| Option | Default | Description |
| --- | --- | --- |
| `direction` | `"up"` | `up`, `right`, `down`, or `left`. |
| `min_angle` | `30.0` | Minimum starting angle. |
| `max_angle` | `330.0` | Maximum starting angle. |
| `tolerance` | `8.0` | Accepted angular error. |
| `noise` | `0.025` | Background grain. |
| `vignette` | `0.14` | Edge darkening. |
| `show_instruction` | `True` | Draw the instruction. |

## Using a config object

```python
from captcha_forge import Captcha, CaptchaConfig

config = CaptchaConfig(
    width=500,
    height=180,
    seed=42,
    color_mode="dark",
)

challenge = Captcha("image", config=config, length=5).generate()
```

Keyword arguments override fields on the config object; generator-specific
options are merged into `config.options`.

## Validation

Configuration errors are raised early with specific messages:

```python
Captcha("text", min_spacing=10, max_spacing=1).generate()
# ConfigurationError: spacing values must satisfy 0 <= min_spacing <= max_spacing

Captcha("text", unknown_option=True)
# ConfigurationError: Unsupported option(s) for 'text': unknown_option. ...
```

`Captcha(...)` validates option **names** immediately. Option **values** are
validated when the generator is instantiated, which happens inside
`.generate()`.

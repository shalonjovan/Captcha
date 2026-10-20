# Challenge types

Captcha Forge registers nine generators. Each one returns a
[`CaptchaResult`](api.md#captcha_forge.result.CaptchaResult) with frames, an
answer, and type-specific metadata.

| Type | Kind | Default size | Default format | Answer |
| --- | --- | --- | --- | --- |
| [`text`](#text) | animated | 500×160 | GIF | Displayed text |
| [`noise`](#noise) | animated | 500×160 | GIF | Displayed text |
| [`image`](#image) | static | 500×180 | PNG | Displayed text |
| [`word`](#word) | static | 500×180 | PNG | Displayed word |
| [`math`](#math) | static | 500×180 | PNG | Integer answer as a string |
| [`slider`](#slider) | static | 460×300 | PNG | Target x position |
| [`click`](#click) | static | 460×320 | PNG | List of `[x, y]` centres |
| [`pattern`](#pattern) | static | 380×380 | PNG | Ordered `[x, y]` coordinates |
| [`rotate`](#rotate) | static | 380×300 | PNG | Clockwise rotation in degrees |

Static types produce one frame. `duration` and `fps` are validated but do not
add frames. Animated types produce `round(duration * fps)` frames.

Friendly aliases are accepted for a few types: `arithmetic` → `math`,
`words` → `word`, `drag` or `puzzle` → `slider`, `click-select` → `click`,
`rotation` → `rotate`, and `animated-text` / `animated-noise` → `text` /
`noise`.

---

## text

![Animated text CAPTCHA](assets/gallery/text.gif)

Animated characters over drifting, semi-transparent background letters. The
foreground is stable so the answer remains readable while the background moves.

```python
from captcha_forge import Captcha

result = Captcha(
    "text",
    duration=3,
    fps=30,
    bg_spawn_rate=12,
    max_rotation=18,
    seed=42,
).generate()

print(result.answer)
result.save("text.gif")
```

- **Answer:** the rendered text, also available as `result.text`.
- **Metadata:** `font_scale`, `characters`, `background_glyphs`,
  `background_spawn_rate`.
- **Default output:** animated GIF.
- **Useful options:** `bg_spawn_rate`, `bg_speed_min`, `bg_speed_max`,
  `initial_bg_count`, `bg_alpha`, `bg_scale`, `fg_wave_amplitude`,
  `min_spacing`, `max_spacing`, `max_rotation`.

Set `bg_spawn_rate=0` and `initial_bg_count=0` for a clean foreground-only
animation. Set `fg_wave_amplitude=3` for a gentle foreground wave.

---

## noise

![Animated noise CAPTCHA](assets/gallery/noise.gif)

Characters carved out of an animated static field. The reusable noise texture
is generated once and panned across frames, which keeps rendering fast.

```python
result = Captcha(
    "noise",
    duration=4,
    noise_scale=10,
    speed_x=2,
    grain=2,
    seed=42,
).generate()
result.save("noise.gif")
```

- **Answer:** the rendered text, also available as `result.text`.
- **Metadata:** `noise_scale`, `grain`, `noise_field`, `characters`.
- **Default output:** animated GIF.
- **Useful options:** `noise_scale`, `grain`, `speed_x`, `speed_y`,
  `bounce_amplitude`, `bounce_speed`, `contrast`, `max_rotation`.

Use `grain=2` or `3` for larger, blockier noise. `contrast` controls how
strongly the noise texture separates from the background.

---

## image

![Distorted image CAPTCHA](assets/gallery/image.png)

Static characters distorted with per-character rotation, scale, shear, a global
wave, noise, speckles, and interference lines. This is the general-purpose
static text challenge.

```python
result = Captcha(
    "image",
    width=500,
    height=180,
    max_rotation=15,
    wave_amplitude=4,
    line_count=5,
    seed=42,
).generate()
result.save("image.png")
```

- **Answer:** the rendered text, also available as `result.text`.
- **Metadata:** `font_scale`, `characters`, `distortion`.
- **Default output:** PNG.
- **Useful options:** `max_rotation`, `letter_spacing`, `char_jitter`,
  `char_scale`, `shear`, `wave_amplitude`, `wave_wavelength`, `noise`,
  `line_count`, `dot_count`, `shadow_offset`, `vignette`.

---

## word

![Dictionary word CAPTCHA](assets/gallery/word.png)

A distorted English word from the bundled word list, or from your own list.

```python
result = Captcha(
    "word",
    wordlist=["tiger", "zebra", "otter", "maple"],
    min_length=4,
    max_length=5,
    uppercase=True,
    seed=42,
).generate()

print(result.answer)  # e.g. "OTTER"
result.save("word.png")
```

- **Answer:** the selected word (uppercase by default).
- **Metadata:** `word_length`, `wordlist_size`.
- **Default output:** PNG.
- **Bundled list:** `src/captcha_forge/data/words.txt`.
- **Useful options:** all `image` options plus `wordlist`, `min_length`,
  `max_length`, `uppercase`.

A custom `wordlist` may be a sequence of words or a whitespace-separated
string. Non-ASCII and non-alphabetic entries are filtered out.

---

## math

![Arithmetic CAPTCHA](assets/gallery/math.png)

A distorted arithmetic expression. The numeric answer is computed and returned,
so a server can validate it without parsing the image.

```python
result = Captcha(
    "math",
    operands=3,
    min_operand=1,
    max_operand=9,
    operations=("+", "-", "*"),
    seed=42,
).generate()

print(result.text)    # e.g. "7 + 5 * 2 = ?"
print(result.answer)  # "24" (evaluated left to right)

# If you force custom text, no answer is computed.
custom = Captcha("math", text="2 + 3 = ?").generate()
print(custom.answer)  # None
```

- **Answer:** the integer result as a string.
- **Metadata:** `operands`, `operations`, `expected_value`.
- **Default output:** PNG.
- **Useful options:** all `image` options plus `operations`, `min_operand`,
  `max_operand`, `operands`, `allow_negative`.

Expressions are evaluated left to right and use only `+`, `-`, and `*`.
Negative intermediate values are avoided unless `allow_negative=True`.

---

## slider

![Slider CAPTCHA](assets/gallery/slider.png)

A jigsaw puzzle piece and a matching gap. The image shows the piece at its start
position; the client-side widget is responsible for dragging it. The answer is
the target x coordinate, and `result.assets["piece"]` contains the piece as a
BGRA image for a custom UI.

```python
result = Captcha(
    "slider",
    piece_size=74,
    tab_radius=10,
    tolerance=6,
    seed=42,
).generate()

print(result.answer)                 # target x in pixels
print(result.metadata["gap_box"])    # (x, y, width, height)
print(result.metadata["piece_box"])  # (x, y, width, height)
piece_bgra = result.assets["piece"]
result.save("slider.png")
```

- **Answer:** the target x position in pixels.
- **Metadata:** `target_x`, `gap_y`, `piece_size`, `piece_box`, `gap_box`,
  `tolerance`, `instruction`.
- **Assets:** `piece` — a BGRA array with the puzzle piece cut from the
  background.
- **Default output:** PNG.
- **Useful options:** `piece_size`, `tab_radius`, `target_x`, `gap_y`,
  `tolerance`, `background_blobs`, `line_count`, `noise`, `vignette`,
  `start_x`.

Validate the user's submitted x against `answer` within `tolerance` pixels.

---

## click

![Click CAPTCHA](assets/gallery/click.png)

A grid of shapes with a rendered instruction such as
`"Click every blue triangle"`. The answer lists the centres of all matching
shapes.

```python
result = Captcha(
    "click",
    target_count=3,
    decoy_count=5,
    shapes=("circle", "square", "triangle", "diamond", "star"),
    colors=("red", "blue", "green", "orange", "purple"),
    seed=42,
).generate()

print(result.metadata["instruction"])
print(result.answer)  # [[x, y], [x, y], ...]
result.save("click.png")
```

- **Answer:** a list of `[x, y]` target centres.
- **Metadata:** `instruction`, `target_shape`, `target_color`, `targets`,
  `decoy_count`, `radius`, `tolerance` (equal to the radius).
- **Default output:** PNG.
- **Useful options:** `target_count`, `decoy_count`, `shapes`, `colors`,
  `target_shape`, `target_color`, `radius_scale`, `jitter`, `noise`,
  `dot_count`, `margin`.

Use the rendered instruction as the source of truth. If you force
`target_shape` or `target_color`, the instruction still describes the generated
target.

---

## pattern

![Pattern CAPTCHA](assets/gallery/pattern.png)

A dot grid with numbered nodes. The user connects the dots in ascending numeric
order. The answer is the ordered sequence of coordinates.

```python
result = Captcha(
    "pattern",
    grid=3,
    path_length=5,
    dot_radius=12,
    seed=42,
).generate()

print(result.answer)                    # [[x, y], ...] in numeric order
print(result.metadata["answer_indices"])
print(result.metadata["labels"])
result.save("pattern.png")
```

- **Answer:** a list of `[x, y]` coordinates in numeric label order.
- **Metadata:** `instruction`, `grid`, `path_length`, `nodes`, `answer_indices`,
  `labels`, `dot_radius`.
- **Default output:** PNG.
- **Useful options:** `grid`, `path_length`, `dot_radius`, `noise`, `margin`,
  `vignette`, `show_instruction`.

Node labels are shuffled across the grid, so the visual path is not a simple
row-major sequence.

---

## rotate

![Rotate CAPTCHA](assets/gallery/rotate.png)

An arrow at a random angle with a target marker. The user rotates the image
until the arrow points in the requested direction. The answer is the clockwise
rotation in degrees.

```python
result = Captcha(
    "rotate",
    direction="up",
    min_angle=30,
    max_angle=330,
    tolerance=8,
    seed=42,
).generate()

print(result.answer)  # degrees clockwise, e.g. 142.9
print(result.metadata["angle"], result.metadata["target_angle"])
result.save("rotate.png")
```

- **Answer:** clockwise rotation needed, in degrees.
- **Metadata:** `instruction`, `direction`, `angle`, `target_angle`,
  `tolerance`, `rotation_needed_clockwise`, `centre`, `radius`.
- **Default output:** PNG.
- **Useful options:** `direction`, `min_angle`, `max_angle`, `tolerance`,
  `noise`, `vignette`, `show_instruction`.

Angles use image coordinates: `0°` is right, `90°` is down, `180°` is left, and
`270°` is up. The answer is computed as
`(target_angle - angle) % 360`.

---

## Choosing a type

- **Animated text/noise** are good demos and lightweight challenges.
- **Image/word** are compact static challenges suitable for forms.
- **Math** works well when the answer can be validated numerically and the
  audience is comfortable with arithmetic.
- **Slider/click/pattern/rotate** provide interaction-based challenges but need
  a client-side widget; the library supplies the image, answer, and geometry.
- **Accessibility:** visual challenges exclude some users. Always provide an
  alternative (audio, email verification, manual review) for sensitive flows.

See [Security](security.md) for the server-side responsibilities that come with
any of these types.

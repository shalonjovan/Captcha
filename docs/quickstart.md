# Quick start

## Render your first challenge

```python
from captcha_forge import Captcha

challenge = Captcha(
    "text",
    width=500,
    height=160,
    duration=3.0,
    fps=30,
    seed=42,
).generate()

print(challenge.answer)
challenge.save("challenge.gif")
```

`Captcha(...)` selects a generator and checks option names immediately.
`.generate()` validates generator option values, renders the frames, and returns
a `CaptchaResult`.

## Inspect the result

```python
challenge.frames      # tuple of BGR uint8 arrays, shape (height, width, 3)
challenge.image       # first frame
challenge.answer      # expected response
challenge.text        # rendered text, or None for non-text challenges
challenge.metadata    # size, seed, answer geometry, and type-specific details
challenge.assets      # extra images, e.g. the slider piece
challenge.size        # (width, height)
challenge.duration    # len(frames) / fps
```

Frames follow OpenCV's **BGR** convention. Use
`cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)` before displaying with a library that
expects RGB.

`CaptchaResult` is sequence-like:

```python
first = challenge[0]
for frame in challenge:
    ...
```

## Save to a file

```python
challenge.save("challenge.gif")   # animated GIF
challenge.save("challenge.webp")  # animated WebP
challenge.save("challenge.mp4")   # MP4 via OpenCV
challenge.save("challenge.png")   # first frame
challenge.save("challenge.jpg", quality=90)
```

Formats are inferred from the suffix. You can override them explicitly:

```python
challenge.save("output.data", format="gif")
```

When a path has no suffix, the generator's suggested format is used. Animated
types suggest GIF; static types suggest PNG.

## Deterministic output

Pass a seed when you need the same frames and answer twice:

```python
first = Captcha("image", seed=123).generate()
second = Captcha("image", seed=123).generate()

assert first.answer == second.answer
assert (first.image == second.image).all()
```

The seed controls both Python randomness and NumPy noise.

## Choose a challenge type

```python
Captcha("text").generate()     # animated, drifting background letters
Captcha("noise").generate()    # animated, moving static texture
Captcha("image").generate()    # static, distorted characters
Captcha("word").generate()     # static, distorted dictionary word
Captcha("math").generate()     # static arithmetic expression
Captcha("slider").generate()   # jigsaw slider puzzle
Captcha("click").generate()    # click matching shapes
Captcha("pattern").generate()  # connect numbered dots
Captcha("rotate").generate()   # rotate the arrow to a direction
```

See [Challenge types](captcha-types.md) for the answer format and metadata of
each one.

## Common options

```python
Captcha(
    "image",
    width=500,
    height=180,
    fps=30,
    duration=3.0,
    seed=42,
    color_mode="light",
    font_face="duplex",
    font_scale=2.5,
    font_thickness=2,
    alphabet="ABCDEFGHJKLMNPQRSTUVWXYZ23456789",
    text=None,
    length=6,
)
```

Type-specific options are passed as keyword arguments:

```python
Captcha("text", max_rotation=20, bg_spawn_rate=14)
Captcha("math", operands=3, max_operand=9)
Captcha("slider", piece_size=82, tolerance=4)
```

Use `Captcha.describe("text")` to discover supported options:

```python
>>> from captcha_forge import Captcha
>>> info = Captcha.describe("text")
>>> info["description"]
'Animated characters over drifting, semi-transparent background letters.'
>>> [option["name"] for option in info["options"]][:3]
['max_rotation', 'min_spacing', 'max_spacing']
```

Unknown option names raise `ConfigurationError` immediately with the supported
option list.

## Themes and colours

```python
Captcha("image", color_mode="dark").generate()
Captcha("image", color_mode="custom", background="#101820", foreground="#f2f2f2").generate()
```

Colours accept names (`"red"`, `"teal"`, …), hex strings (`"#ff8800"`), or RGB
triples (`(255, 136, 0)`).

## Use the result in a web response

```python
from fastapi import Response

challenge = Captcha("image", seed=7).generate()
answer = challenge.answer       # store this server-side; do not send it
image_bytes = challenge.to_bytes("png")
return Response(content=image_bytes, media_type="image/png")
```

`to_bytes("gif")` and `to_bytes("webp")` return animated bytes. MP4 byte output
is not supported; write to a temporary file instead.

## Command line

```bash
captcha-forge list
captcha-forge info click
captcha-forge generate image -o challenge.png --seed 42
captcha-forge generate text -o challenge.gif --duration 4
captcha-forge gallery -o samples
```

See [CLI](cli.md) for all commands.

## Next steps

- [Challenge types](captcha-types.md)
- [Configuration reference](configuration.md)
- [Recipes](recipes.md)
- [Security](security.md)

# Recipes

## Serve a CAPTCHA from a web API

The important rule: **generate and store the answer on the server; send only the
image (and any non-answer assets) to the client.**

This FastAPI example uses an in-memory store for clarity. Use Redis, a database,
or another shared store in production, with an expiry and one-time consumption.

```python
import secrets
import time

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

from captcha_forge import Captcha

app = FastAPI()
CHALLENGES: dict[str, dict] = {}
TTL_SECONDS = 120


class Answer(BaseModel):
    token: str
    answer: str


@app.get("/captcha")
def create_captcha() -> Response:
    result = Captcha("image", seed=None).generate()
    token = secrets.token_urlsafe(16)
    CHALLENGES[token] = {
        "answer": result.answer,
        "created": time.time(),
    }
    # Never include result.answer in the response.
    return Response(
        content=result.to_bytes("png"),
        media_type="image/png",
        headers={
            "Cache-Control": "no-store",
            "X-Captcha-Token": token,
        },
    )


@app.post("/captcha/verify")
def verify_captcha(payload: Answer) -> dict[str, bool]:
    challenge = CHALLENGES.pop(payload.token, None)
    if challenge is None:
        raise HTTPException(status_code=404, detail="Unknown or already used token")
    if time.time() - challenge["created"] > TTL_SECONDS:
        raise HTTPException(status_code=410, detail="Challenge expired")
    valid = secrets.compare_digest(
        payload.answer.strip().upper(),
        str(challenge["answer"]).strip().upper(),
    )
    return {"valid": valid}
```

For numeric challenges (math, slider, rotate), compare with a tolerance instead
of string equality. For click and pattern, compare ordered coordinate lists
within a radius.

### Animated challenge

```python
result = Captcha("noise", duration=3).generate()
return Response(
    content=result.to_bytes("gif"),
    media_type="image/gif",
    headers={"Cache-Control": "no-store"},
)
```

### Slider asset

The slider piece is a BGRA array. Encode it separately if your UI needs to draw
the piece as an image:

```python
import cv2

result = Captcha("slider").generate()
piece = result.assets["piece"]
ok, buffer = cv2.imencode(".png", piece)
piece_bytes = buffer.tobytes()
```

Do not send `result.answer` or `result.metadata["target_x"]`; the gap is already
visible in the challenge image. Validate the submitted x on the server with
`metadata["tolerance"]`.

### Click and pattern coordinates

For `click`, `result.answer` is a list of `[x, y]` centres. For `pattern`, it is
the ordered list of `[x, y]` coordinates. Keep them on the server and compare
submitted clicks with a radius or sequence check.

## Use bytes instead of temporary files

```python
from captcha_forge import Captcha

result = Captcha("image", seed=42).generate()
png_bytes = result.to_bytes("png")
gif_bytes = result.to_bytes("gif")
webp_bytes = result.to_bytes("webp")
```

MP4 is file-only; write it to a temporary directory and stream/remove the file.

## Custom word list

```python
from pathlib import Path

words = Path("my_words.txt").read_text().split()
result = Captcha("word", wordlist=words, min_length=4, max_length=10).generate()
```

The word list is filtered to ASCII alphabetic words within the requested length
range. Duplicate words are removed while preserving order.

## Custom colours

```python
result = Captcha(
    "image",
    color_mode="custom",
    background="#fff8e7",
    foreground="#2b2b2b",
    font_face="complex",
    font_scale=2.8,
).generate()
```

Colours accept names, hex strings, or RGB triples. Frames are BGR; public colour
values are RGB.

## Reproducible regression tests

```python
from captcha_forge import Captcha

first = Captcha("image", seed=123).generate()
second = Captcha("image", seed=123).generate()

assert first.answer == second.answer
assert (first.image == second.image).all()
```

Seed control is useful for snapshot tests. If you want fresh challenges in
production, leave `seed=None`.

## Generate a gallery for a README

```bash
captcha-forge gallery -o docs/assets/gallery --seed 2026 --duration 1.2 --fps 8
```

Or use the included script for the documentation layout and contact sheet:

```bash
python scripts/generate_gallery.py
```

## Batch generation

```python
from pathlib import Path

from captcha_forge import Captcha

output = Path("samples")
output.mkdir(exist_ok=True)

for index in range(20):
    challenge = Captcha("word", seed=1000 + index).generate()
    challenge.save(output / f"word-{index:02d}.png")
```

Generating many challenges is CPU-bound. Avoid regenerating the same challenge
on every page load; create it once, store the answer with a short TTL, and reuse
the image for that session.

## Use a config object

```python
from captcha_forge import Captcha, CaptchaConfig

config = CaptchaConfig(
    width=520,
    height=190,
    color_mode="dark",
    font_face="duplex",
    seed=42,
)

challenge = Captcha("text", config=config, duration=4).generate()
```

Keyword arguments override config fields. Generator options are merged into
`config.options` and validated when the generator is created.

## CLI JSON in a script

```bash
captcha-forge generate math -o math.png --json > math.json
```

The JSON report contains `answer`, `text`, `metadata`, frame count, and the
output path. This is convenient for test fixtures and batch tooling.

## Next steps

- [Challenge types](captcha-types.md) for answer formats.
- [Configuration](configuration.md) for every option.
- [Security](security.md) before shipping a production flow.

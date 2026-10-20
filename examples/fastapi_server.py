"""Minimal server-side CAPTCHA flow with FastAPI.

Install the optional example dependencies:

    pip install fastapi uvicorn

Run from the repository root:

    uvicorn examples.fastapi_server:app --reload

Open http://127.0.0.1:8000/docs and call ``GET /captcha`` to receive an image
and a token, then ``POST /captcha/verify`` with the token and the text you see.

This example keeps challenges in memory and is intentionally small. Use Redis
or a database, plus rate limiting, in production.
"""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

from captcha_forge import Captcha

TTL_SECONDS = 120
app = FastAPI(title="Captcha Forge example")


@dataclass
class Challenge:
    answer: str
    created: float


CHALLENGES: dict[str, Challenge] = {}


class Verification(BaseModel):
    token: str
    answer: str


def _purge_expired() -> None:
    cutoff = time.time() - TTL_SECONDS
    for token in [key for key, value in CHALLENGES.items() if value.created < cutoff]:
        CHALLENGES.pop(token, None)


@app.get("/captcha")
def create_captcha() -> Response:
    _purge_expired()
    result = Captcha("image", seed=None).generate()
    token = secrets.token_urlsafe(24)
    CHALLENGES[token] = Challenge(answer=str(result.answer), created=time.time())

    # Only the image is sent; the answer stays on the server.
    return Response(
        content=result.to_bytes("png"),
        media_type="image/png",
        headers={
            "Cache-Control": "no-store",
            "X-Captcha-Token": token,
        },
    )


@app.post("/captcha/verify")
def verify_captcha(payload: Verification) -> dict[str, bool]:
    # Consume the challenge whether the answer is correct or not.
    challenge = CHALLENGES.pop(payload.token, None)
    if challenge is None:
        raise HTTPException(status_code=404, detail="Unknown or already used token")
    if time.time() - challenge.created > TTL_SECONDS:
        raise HTTPException(status_code=410, detail="Challenge expired")

    valid = secrets.compare_digest(
        payload.answer.strip().upper(),
        challenge.answer.strip().upper(),
    )
    return {"valid": valid}

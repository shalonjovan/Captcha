# Security and responsible use

Captcha Forge generates challenge images. It is **not** a complete anti-bot
system, an authentication factor, or a security boundary on its own. A CAPTCHA
only helps when the answer is generated, stored, and verified on a trusted
server, and when the surrounding application applies rate limits and risk
controls.

## The essential rules

1. **Generate on the server.** Do not ship a challenge generator and its answer
   to the browser. Client-side generation exposes the answer and makes the
   challenge meaningless.
2. **Store the answer server-side.** Keep it in a session, Redis, or database
   keyed by an unguessable token. Never put it in HTML, JavaScript, URL
   parameters, logs, or analytics.
3. **Expire challenges.** Use a short TTL (for example 2–5 minutes).
4. **Consume once.** Delete or mark the challenge used after a verification
   attempt, whether it succeeds or fails.
5. **Rate-limit.** Limit challenge creation and verification per IP, account,
   session, and token. A CAPTCHA does not stop credential stuffing by itself.
6. **Use HTTPS.** Tokens and answers must not travel over plain HTTP.
7. **Log carefully.** Do not log answers, tokens, or full request bodies.
8. **Provide an alternative.** Visual CAPTCHAs are inaccessible to some users.
   Offer an audio challenge, email/SMS verification, or manual review for
   sensitive flows.

## Do not leak the answer

`CaptchaResult` deliberately contains `answer`, `text`, and solution geometry so
that tests and server-side code can use them. Treat the whole result as
server-side data.

```python
# Server-side only
result = Captcha("image").generate()
store[token] = {"answer": result.answer, "created": time.time()}

# Send only the image bytes
return Response(content=result.to_bytes("png"), media_type="image/png")
```

For interactive challenges (`slider`, `click`, `pattern`, `rotate`), the image
contains the visual puzzle but the metadata contains the expected coordinates or
angle. Send the image (and, for slider, the piece asset) to the client; keep the
answer and target geometry on the server.

## Validate type-specific answers

| Type | Validation |
| --- | --- |
| `text`, `noise`, `image`, `word` | Normalize case/whitespace as appropriate and compare. |
| `math` | Parse the submission as an integer and compare with `int(answer)`. |
| `slider` | Compare the submitted x with `answer` within `metadata["tolerance"]`. |
| `click` | Compare each submitted point with a target in `metadata["targets"]` within `metadata["tolerance"]`. |
| `pattern` | Compare the ordered coordinate sequence with `answer` (allow a click radius). |
| `rotate` | Compare the submitted rotation with `answer` within the angular `tolerance`, handling wraparound. |

Avoid loose matching that makes the challenge trivial (for example, accepting
any non-empty text).

## CAPTCHAs are not enough

Modern bots can solve many image challenges with OCR and machine learning. Use
CAPTCHAs as one signal among several:

- rate limits and progressive delays;
- device and network reputation;
- account-level anomaly detection;
- email or phone verification for high-risk actions;
- server-side authorization checks for every sensitive operation;
- monitoring of solve rates and abuse patterns.

Rotate challenge types and parameters periodically. Do not rely on a single
challenge type for high-value flows.

## Accessibility

Visual challenges can exclude users with low vision, cognitive disabilities, or
screen readers. Provide:

- an audio alternative that is not trivial to automate;
- a support/manual-review path;
- clear instructions and generous time limits;
- keyboard-accessible interactive widgets.

The `text` and `noise` animations are not a substitute for an accessible
alternative.

## Privacy

Challenge images can contain random text but should not contain personal data.
Avoid embedding user identifiers, emails, or account details in the image.
Store only what you need for verification, and delete it promptly.

## Responsible use

Use Captcha Forge to protect forms, generate test data, teach image processing,
or evaluate detection systems. Do not use it to create deceptive pages,
phishing flows, fake security prompts, or to harass users. You are responsible
for complying with applicable laws, platform policies, and accessibility
requirements.

## Reporting a vulnerability

If you find a security issue in Captcha Forge itself, please follow
[SECURITY.md](https://github.com/shalonjovan/Captcha/blob/main/SECURITY.md) rather
than opening a public issue with exploit details.

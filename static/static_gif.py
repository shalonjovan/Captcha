import cv2
import numpy as np
import imageio
import random
import string
import math
import time

# ---------------- CONFIG ----------------
FRAME_W, FRAME_H = 550, 150
NOISE_SCALE = 10
SPEED_X, SPEED_Y = 1, 0
FPS = 30

TEXT_LEN = 6
FONT = cv2.FONT_HERSHEY_DUPLEX
FONT_SCALE = 3
FONT_THICKNESS = 5

MAX_ROTATION = 15
MAX_SPACING = 2

BOUNCE_AMPLITUDE = 8
BOUNCE_SPEED = 2.0

SAVE_GIF = True
GIF_DURATION_SECONDS = 3
GIF_FPS = 15
GIF_NAME = "captcha.gif"

# ---------------- RANDOM TEXT ----------------
ALPHABET = (
    string.ascii_letters.replace('I', '').replace('j', '') +
    string.digits.replace('1', '')
)

captcha_text = ''.join(random.choices(ALPHABET, k=TEXT_LEN))
print("CAPTCHA:", captcha_text)

# ---------------- BASE NOISE ----------------
noise_h = FRAME_H * NOISE_SCALE
noise_w = FRAME_W * NOISE_SCALE

base_noise = np.random.randint(
    0, 256, (noise_h, noise_w), dtype=np.uint8
)

# ---------------- PREPARE CHAR OBJECTS ----------------
chars = []

left_margin = 20
right_margin = 20
usable_width = FRAME_W - left_margin - right_margin

char_widths = []
for ch in captcha_text:
    (w, h), baseline = cv2.getTextSize(ch, FONT, FONT_SCALE, FONT_THICKNESS)
    char_widths.append(w + 20)

remaining_space = max(0, usable_width - sum(char_widths))

spacings = []
for _ in range(TEXT_LEN - 1):
    s = random.randint(0, min(MAX_SPACING, remaining_space)) if remaining_space > 0 else 0
    spacings.append(s)
    remaining_space -= s

x_cursor = left_margin
y_center = FRAME_H // 2

for i, ch in enumerate(captcha_text):
    spacing = spacings[i] if i < len(spacings) else 0

    (ch_w, ch_h), baseline = cv2.getTextSize(
        ch, FONT, FONT_SCALE, FONT_THICKNESS
    )

    glyph_h = ch_h + baseline
    pad = 10

    canvas = np.zeros(
        (glyph_h + pad * 2, ch_w + pad * 2),
        dtype=np.uint8
    )

    cv2.putText(
        canvas,
        ch,
        (pad, pad + ch_h),
        FONT,
        FONT_SCALE,
        255,
        FONT_THICKNESS,
        cv2.LINE_8
    )

    angle = random.uniform(-MAX_ROTATION, MAX_ROTATION)
    center = (canvas.shape[1] // 2, canvas.shape[0] // 2)
    rot = cv2.getRotationMatrix2D(center, angle, 1.0)

    rotated = cv2.warpAffine(
        canvas,
        rot,
        (canvas.shape[1], canvas.shape[0]),
        flags=cv2.INTER_NEAREST
    )

    chars.append({
        "img": rotated,
        "x": x_cursor,
        "phase": random.uniform(0, 2 * math.pi)
    })

    x_cursor += rotated.shape[1] + spacing

# ---------------- ANIMATION LOOP ----------------
x = y = 0
start_time = time.time()

cv2.namedWindow("captcha", cv2.WINDOW_AUTOSIZE)

gif_frames = []
max_gif_frames = GIF_DURATION_SECONDS * GIF_FPS

while True:
    t = time.time() - start_time

    # Background
    bg = base_noise[y:y + FRAME_H, x:x + FRAME_W]
    bg = cv2.resize(bg, (FRAME_W, FRAME_H), interpolation=cv2.INTER_NEAREST)
    bg = cv2.cvtColor(bg, cv2.COLOR_GRAY2BGR)

    text_mask = np.zeros((FRAME_H, FRAME_W), dtype=np.uint8)

    for ch in chars:
        offset = int(
            BOUNCE_AMPLITUDE * math.sin(BOUNCE_SPEED * t + ch["phase"])
        )

        img = ch["img"]
        h, w = img.shape

        y_pos = (y_center - h // 2) + offset
        x_pos = ch["x"]

        y1 = max(0, y_pos)
        y2 = min(FRAME_H, y_pos + h)
        x1 = max(0, x_pos)
        x2 = min(FRAME_W, x_pos + w)

        if y1 >= y2 or x1 >= x2:
            continue

        img_y1 = y1 - y_pos
        img_y2 = img_y1 + (y2 - y1)
        img_x1 = x1 - x_pos
        img_x2 = img_x1 + (x2 - x1)

        roi = text_mask[y1:y2, x1:x2]
        text_mask[y1:y2, x1:x2] = np.maximum(
            roi,
            img[img_y1:img_y2, img_x1:img_x2]
        )

    # Text texture
    text_noise = np.random.randint(
        0, 256, (FRAME_H, FRAME_W), dtype=np.uint8
    )
    text_texture = cv2.bitwise_and(text_noise, text_mask)

    # Composite
    text_bgr = cv2.cvtColor(text_texture, cv2.COLOR_GRAY2BGR)
    mask_inv = cv2.bitwise_not(text_mask)

    bg_part = cv2.bitwise_and(bg, bg, mask=mask_inv)
    text_part = cv2.bitwise_and(text_bgr, text_bgr, mask=text_mask)

    frame = cv2.add(bg_part, text_part)
    cv2.imshow("captcha", frame)

    # ---- GIF CAPTURE ----
    if SAVE_GIF and len(gif_frames) < max_gif_frames:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        gif_frames.append(rgb_frame)

    if SAVE_GIF and len(gif_frames) >= max_gif_frames:
        break

    x = (x + SPEED_X) % (noise_w - FRAME_W)
    y = (y + SPEED_Y) % (noise_h - FRAME_H)

    if cv2.waitKey(int(1000 / FPS)) & 0xFF == 27:
        break

cv2.destroyAllWindows()

# ---------------- SAVE GIF (ONCE) ----------------
if SAVE_GIF and gif_frames:
    imageio.mimsave(GIF_NAME, gif_frames, fps=GIF_FPS)
    print(f"GIF saved as {GIF_NAME}")

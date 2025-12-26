import cv2
import numpy as np
import random
import string

# ---------------- CONFIG ----------------
FRAME_W, FRAME_H = 400, 150
NOISE_SCALE = 10
SPEED_X, SPEED_Y = 0, 1
FPS = 30

TEXT_LEN = 6
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 2
FONT_THICKNESS = 5

MAX_ROTATION = 20          # degrees
MAX_SPACING = 5

# ---------------- RANDOM TEXT ----------------
captcha_text = ''.join(
    random.choices(string.ascii_letters + string.digits, k=TEXT_LEN)
)
print("CAPTCHA:", captcha_text)

# ---------------- BASE NOISE (SHARP STATIC) ----------------
noise_h = FRAME_H * NOISE_SCALE
noise_w = FRAME_W * NOISE_SCALE

base_noise = np.random.randint(
    0, 256, (noise_h, noise_w), dtype=np.uint8
)

# ---------------- TEXT MASK (PER-CHAR) ----------------
text_mask = np.zeros((FRAME_H, FRAME_W), dtype=np.uint8)

left_margin = 20
right_margin = 20
usable_width = FRAME_W - left_margin - right_margin

# Measure approximate character widths
char_widths = [
    cv2.getTextSize(ch, FONT, FONT_SCALE, FONT_THICKNESS)[0][0] + 20
    for ch in captcha_text
]

total_char_width = sum(char_widths)
remaining_space = max(0, usable_width - total_char_width)

# Generate safe random spacings
spacings = []
for _ in range(TEXT_LEN - 1):
    if remaining_space <= 0:
        s = 0
    else:
        s = random.randint(0, min(MAX_SPACING, remaining_space))
    spacings.append(s)
    remaining_space -= s

x_cursor = left_margin
y_center = FRAME_H // 2

for idx, ch in enumerate(captcha_text):
    spacing = spacings[idx] if idx < len(spacings) else 0

    (ch_w, ch_h), _ = cv2.getTextSize(
        ch, FONT, FONT_SCALE, FONT_THICKNESS
    )

    pad = 10
    ch_canvas = np.zeros(
        (ch_h + pad * 2, ch_w + pad * 2),
        dtype=np.uint8
    )

    cv2.putText(
        ch_canvas,
        ch,
        (pad, ch_h + pad),
        FONT,
        FONT_SCALE,
        255,
        FONT_THICKNESS,
        cv2.LINE_8
    )

    angle = random.uniform(-MAX_ROTATION, MAX_ROTATION)
    center = (ch_canvas.shape[1] // 2, ch_canvas.shape[0] // 2)
    rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)

    rotated = cv2.warpAffine(
        ch_canvas,
        rot_mat,
        (ch_canvas.shape[1], ch_canvas.shape[0]),
        flags=cv2.INTER_NEAREST
    )

    y_pos = y_center - rotated.shape[0] // 2

    if x_cursor + rotated.shape[1] > FRAME_W:
        break

    roi = text_mask[
        y_pos:y_pos + rotated.shape[0],
        x_cursor:x_cursor + rotated.shape[1]
    ]

    text_mask[
        y_pos:y_pos + rotated.shape[0],
        x_cursor:x_cursor + rotated.shape[1]
    ] = np.maximum(roi, rotated)

    x_cursor += rotated.shape[1] + spacing

# ---------------- TEXT TEXTURE (NOISE) ----------------
text_noise = np.random.randint(
    0, 256, (FRAME_H, FRAME_W), dtype=np.uint8
)

text_texture = cv2.bitwise_and(text_noise, text_mask)

# ---------------- ANIMATION LOOP ----------------
x = y = 0
cv2.namedWindow("captcha", cv2.WINDOW_NORMAL)

while True:
    bg = base_noise[y:y + FRAME_H, x:x + FRAME_W]

    bg = cv2.resize(
        bg,
        (FRAME_W, FRAME_H),
        interpolation=cv2.INTER_NEAREST
    )

    bg = cv2.cvtColor(bg, cv2.COLOR_GRAY2BGR)
    text_bgr = cv2.cvtColor(text_texture, cv2.COLOR_GRAY2BGR)

    mask_inv = cv2.bitwise_not(text_mask)

    bg_part = cv2.bitwise_and(bg, bg, mask=mask_inv)
    text_part = cv2.bitwise_and(text_bgr, text_bgr, mask=text_mask)

    frame = cv2.add(bg_part, text_part)

    cv2.imshow("captcha", frame)

    x = (x + SPEED_X) % (noise_w - FRAME_W)
    y = (y + SPEED_Y) % (noise_h - FRAME_H)

    if cv2.waitKey(int(1000 / FPS)) & 0xFF == 27:
        break

cv2.destroyAllWindows()

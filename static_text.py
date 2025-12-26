import cv2
import numpy as np
import random
import string

# ---------------- CONFIG ----------------
FRAME_W, FRAME_H = 400, 150
NOISE_SCALE = 3
SPEED_X, SPEED_Y = 0, 1
FPS = 30

TEXT_LEN = 6
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 2
FONT_THICKNESS = 10

# ---------------- RANDOM TEXT ----------------
captcha_text = ''.join(
    random.choices(string.ascii_letters + string.digits, k=TEXT_LEN)
)
print("CAPTCHA:", captcha_text)

# ---------------- BASE NOISE ----------------
noise_h = FRAME_H * NOISE_SCALE
noise_w = FRAME_W * NOISE_SCALE

base_noise = np.random.randint(
    0, 255, (noise_h, noise_w), dtype=np.uint8
)
base_noise = cv2.GaussianBlur(base_noise, (5, 5), 0)

# ---------------- TEXT MASK ----------------
text_mask = np.zeros((FRAME_H, FRAME_W), dtype=np.uint8)

(text_w, text_h), baseline = cv2.getTextSize(
    captcha_text, FONT, FONT_SCALE, FONT_THICKNESS
)

text_x = (FRAME_W - text_w) // 2
text_y = (FRAME_H + text_h) // 2

cv2.putText(
    text_mask,
    captcha_text,
    (text_x, text_y),
    FONT,
    FONT_SCALE,
    255,
    FONT_THICKNESS,
    cv2.LINE_8
)

# ---------------- TEXT NOISE ----------------
text_noise = np.random.randint(
    0, 256, (FRAME_H, FRAME_W), dtype=np.uint8
)
text_noise = cv2.GaussianBlur(text_noise, (3, 3), 0)

# Apply mask
text_texture = cv2.bitwise_and(text_noise, text_mask)

# ---------------- ANIMATION LOOP ----------------
x = y = 0
cv2.namedWindow("captcha", cv2.WINDOW_NORMAL)

while True:
    bg = base_noise[y:y+FRAME_H, x:x+FRAME_W]
    bg = cv2.resize(bg, (FRAME_W, FRAME_H))
    bg = cv2.cvtColor(bg, cv2.COLOR_GRAY2BGR)

    # Convert text texture to BGR
    text_bgr = cv2.cvtColor(text_texture, cv2.COLOR_GRAY2BGR)

    # Composite: text overrides background
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

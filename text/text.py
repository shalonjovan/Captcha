import cv2
import numpy as np
import random
import string
import time
import math
import imageio

# ---------------- CONFIG ----------------
FRAME_W, FRAME_H = 500, 160
FPS = 30
DURATION = 10  # seconds

TEXT_LEN = 6
FONT = cv2.FONT_HERSHEY_DUPLEX
FONT_SCALE = 2.5
FONT_THICKNESS = 2

# Background behavior
BG_SPAWN_RATE = 10
BG_SPEED_MIN = 0.6
BG_SPEED_MAX = 2.0
INITIAL_BG_COUNT = 25

# Foreground randomness
MAX_TEXT_ROTATION = 15
MIN_SPACING = 2
MAX_SPACING = 6

# -------- COLOR MODE --------
COLOR_MODE = "light"   # "light" or "dark"

if COLOR_MODE == "light":
    BG_COLOR = 255   # white
    FG_COLOR = 0     # black
else:
    BG_COLOR = 0     # black
    FG_COLOR = 255   # white

# -------- GIF EXPORT --------
EXPORT_GIF = True
GIF_NAME = "captcha.gif"
GIF_FPS = 15

# ---------------- TEXT SET ----------------
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

captcha_text = ''.join(random.choices(ALPHABET, k=TEXT_LEN))
print("CAPTCHA:", captcha_text)

# ---------------- BACKGROUND CHAR OBJECT ----------------
class FloatingChar:
    def __init__(self, initial=False):
        self.char = random.choice(ALPHABET)

        if initial:
            self.x = random.randint(-20, FRAME_W)
            self.y = random.randint(-20, FRAME_H)
        else:
            self.x = random.randint(-40, FRAME_W)
            self.y = random.randint(-40, FRAME_H)

        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-BG_SPEED_MAX, -BG_SPEED_MIN)
        self.angle = random.uniform(-15, 15)

    def update(self):
        self.x += self.vx
        self.y += self.vy

    def alive(self):
        return self.y > -80 and -80 < self.x < FRAME_W + 80

# ---------------- PREPARE FOREGROUND CHARACTERS ----------------
char_canvases = []
char_spacings = []
total_width = 0

for ch in captcha_text:
    char_spacings.append(random.randint(MIN_SPACING, MAX_SPACING))

for ch in captcha_text:
    (cw, ch_h), baseline = cv2.getTextSize(
        ch, FONT, FONT_SCALE, FONT_THICKNESS
    )

    glyph_h = ch_h + baseline
    pad = 10

    canvas = np.zeros(
        (glyph_h + pad * 2, cw + pad * 2),
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

    angle = random.uniform(-MAX_TEXT_ROTATION, MAX_TEXT_ROTATION)
    center = (canvas.shape[1] // 2, canvas.shape[0] // 2)
    rot = cv2.getRotationMatrix2D(center, angle, 1.0)

    rotated = cv2.warpAffine(
        canvas,
        rot,
        (canvas.shape[1], canvas.shape[0]),
        flags=cv2.INTER_NEAREST
    )

    char_canvases.append(rotated)
    total_width += rotated.shape[1] + char_spacings[len(char_canvases) - 1]

# ---------------- MAIN LOOP ----------------
bg_chars = []
for _ in range(INITIAL_BG_COUNT):
    bg_chars.append(FloatingChar(initial=True))

gif_frames = []

start = time.time()
cv2.namedWindow("captcha", cv2.WINDOW_AUTOSIZE)

while True:
    t = time.time() - start
    if t > DURATION:
        break

    frame = np.ones((FRAME_H, FRAME_W, 3), dtype=np.uint8) * BG_COLOR

    # Spawn background chars
    if random.random() < BG_SPAWN_RATE / FPS:
        bg_chars.append(FloatingChar())

    # Update & draw background chars
    new_bg = []
    for ch in bg_chars:
        ch.update()
        if ch.alive():
            new_bg.append(ch)

            canvas = np.zeros((50, 50), dtype=np.uint8)
            cv2.putText(
                canvas,
                ch.char,
                (5, 40),
                FONT,
                FONT_SCALE,
                255,
                FONT_THICKNESS,
                cv2.LINE_8
            )

            M = cv2.getRotationMatrix2D((25, 25), ch.angle, 1)
            rot = cv2.warpAffine(canvas, M, (50, 50))

            for iy in range(50):
                for ix in range(50):
                    if rot[iy, ix] > 0:
                        y = int(ch.y + iy)
                        x = int(ch.x + ix)
                        if 0 <= x < FRAME_W and 0 <= y < FRAME_H:
                            frame[y, x] = (FG_COLOR, FG_COLOR, FG_COLOR)

    bg_chars = new_bg

    # Draw foreground CAPTCHA text
    x_cursor = (FRAME_W - total_width) // 2
    y_center = FRAME_H // 2

    for i, img in enumerate(char_canvases):
        h, w = img.shape
        y_pos = y_center - h // 2

        for iy in range(h):
            for ix in range(w):
                if img[iy, ix] > 0:
                    y = y_pos + iy
                    x = x_cursor + ix
                    if 0 <= x < FRAME_W and 0 <= y < FRAME_H:
                        frame[y, x] = (FG_COLOR, FG_COLOR, FG_COLOR)

        x_cursor += w + char_spacings[i]

    # Show preview
    cv2.imshow("captcha", frame)

    # Collect GIF frames
    if EXPORT_GIF:
        gif_frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    if cv2.waitKey(int(1000 / FPS)) & 0xFF == 27:
        break

cv2.destroyAllWindows()

# ---------------- SAVE GIF ----------------
if EXPORT_GIF and gif_frames:
    imageio.mimsave(GIF_NAME, gif_frames, fps=GIF_FPS)
    print(f"GIF saved as {GIF_NAME}")

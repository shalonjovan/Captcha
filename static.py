import cv2
import numpy as np

# ---- CONFIG ----
FRAME_W, FRAME_H = 400, 150
NOISE_SCALE = 3        # larger = coarser noise
SPEED_X = 1            # pixels per frame
SPEED_Y = 1
FPS = 30

# ---- GENERATE LARGE NOISE FIELD ----
noise_h = FRAME_H * NOISE_SCALE
noise_w = FRAME_W * NOISE_SCALE

base_noise = np.random.randint(
    0, 256, (noise_h, noise_w), dtype=np.uint8
)

# Optional: smooth noise slightly
base_noise = cv2.GaussianBlur(base_noise, (5, 5), 0)

x, y = 0, 0

cv2.namedWindow("moving_static", cv2.WINDOW_NORMAL)

while True:
    # Extract moving window
    frame = base_noise[
        y:y + FRAME_H,
        x:x + FRAME_W
    ]

    # Resize to final resolution
    frame = cv2.resize(
        frame,
        (FRAME_W, FRAME_H),
        interpolation=cv2.INTER_LINEAR
    )

    # Convert to BGR (for later text overlay)
    frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

    cv2.imshow("moving_static", frame)

    # Update position (wrap-around)
    x = (x + SPEED_X) % (noise_w - FRAME_W)
    y = (y + SPEED_Y) % (noise_h - FRAME_H)

    if cv2.waitKey(int(1000 / FPS)) & 0xFF == 27:
        break

cv2.destroyAllWindows()

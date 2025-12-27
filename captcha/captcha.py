import cv2
import numpy as np
import random
import string
import math
import imageio
from pathlib import Path


class Captcha:
    """
    Captcha generator supporting multiple captcha types.

    Types:
        - "noise": static noise captcha
        - "text": floating background text captcha
    """

    # ---------------- DEFAULTS ----------------
    DEFAULTS = dict(
        captcha_type="text",          # "text" | "noise"
        frame_size=(500, 160),
        fps=30,
        duration=10,

        font=cv2.FONT_HERSHEY_DUPLEX,
        font_scale=2.5,
        font_thickness=2,

        max_rotation=15,
        min_spacing=2,
        max_spacing=6,

        color_mode="ligth",           # "light" | "dark"

        bg_spawn_rate=10,
        bg_speed_min=0.6,
        bg_speed_max=2.0,
        initial_bg_count=25,

        export=True,
        export_format="gif",           # "gif" | "mp4"
        output_name="captcha",

        captcha_text=None              # None = random
    )

    ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

    # ---------------- INIT ----------------
    def __init__(self, **kwargs):
        cfg = self.DEFAULTS.copy()
        cfg.update(kwargs)
        self.cfg = cfg

        self.w, self.h = cfg["frame_size"]
        self.frames = []

        # Colors
        if cfg["color_mode"] == "light":
            self.bg_color = 255
            self.fg_color = 0
        else:
            self.bg_color = 0
            self.fg_color = 255

        # Captcha text
        self.text = (
            cfg["captcha_text"]
            if cfg["captcha_text"]
            else "".join(random.choices(self.ALPHABET, k=6))
        )

    # ---------------- PUBLIC API ----------------
    def generate(self):
        if self.cfg["captcha_type"] == "text":
            self._generate_text_captcha()
        elif self.cfg["captcha_type"] == "noise":
            self._generate_noise_captcha()
        else:
            raise ValueError("Unknown captcha_type")

        if self.cfg["export"]:
            self._export()

        return self.frames

    # ---------------- TEXT CAPTCHA ----------------
    def _generate_text_captcha(self):
        fps = self.cfg["fps"]
        total_frames = int(self.cfg["duration"] * fps)

        bg_chars = self._init_bg_chars()

        fg_imgs, spacings, total_width = self._prepare_foreground_chars()

        for _ in range(total_frames):
            frame = np.ones((self.h, self.w, 3), dtype=np.uint8) * self.bg_color

            # spawn bg chars
            if random.random() < self.cfg["bg_spawn_rate"] / fps:
                bg_chars.append(self._new_bg_char())

            # draw bg chars
            bg_chars = self._draw_bg_chars(frame, bg_chars)

            # draw foreground text
            x = (self.w - total_width) // 2
            y_center = self.h // 2

            for img, space in zip(fg_imgs, spacings):
                h, w = img.shape
                y = y_center - h // 2
                self._blit(frame, img, x, y)
                x += w + space

            self.frames.append(frame)

    # ---------------- NOISE CAPTCHA ----------------
    def _generate_noise_captcha(self):
        cfg = self.cfg
        fps = cfg["fps"]
        total_frames = int(cfg["duration"] * fps)

        FRAME_W, FRAME_H = self.w, self.h

        NOISE_SCALE = cfg.get("noise_scale", 10)
        SPEED_X = cfg.get("speed_x", 1)
        SPEED_Y = cfg.get("speed_y", 0)

        # ---------- BASE NOISE (STATIC, LARGE) ----------
        noise_h = FRAME_H * NOISE_SCALE
        noise_w = FRAME_W * NOISE_SCALE

        base_noise = np.random.randint(
            0, 256, (noise_h, noise_w), dtype=np.uint8
        )

        # ---------- PREPARE CHAR OBJECTS ----------
        chars = []
        text = self.text

        left_margin = 20
        right_margin = 20
        usable_width = FRAME_W - left_margin - right_margin

        char_widths = []
        for ch in text:
            (w, h), baseline = cv2.getTextSize(
                ch, cfg["font"], cfg["font_scale"], cfg["font_thickness"]
            )
            char_widths.append(w + 20)

        remaining_space = max(0, usable_width - sum(char_widths))

        spacings = []
        for _ in range(len(text) - 1):
            s = random.randint(
                0, min(cfg["max_spacing"], remaining_space)
            ) if remaining_space > 0 else 0
            spacings.append(s)
            remaining_space -= s

        x_cursor = left_margin
        y_center = FRAME_H // 2

        for i, ch in enumerate(text):
            spacing = spacings[i] if i < len(spacings) else 0

            (ch_w, ch_h), baseline = cv2.getTextSize(
                ch, cfg["font"], cfg["font_scale"], cfg["font_thickness"]
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
                cfg["font"],
                cfg["font_scale"],
                255,
                cfg["font_thickness"],
                cv2.LINE_8
            )

            angle = random.uniform(-cfg["max_rotation"], cfg["max_rotation"])
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

        # ---------- ANIMATION ----------
        x = y = 0
        t = 0.0

        for _ in range(total_frames):
            # moving noise background
            bg = base_noise[y:y + FRAME_H, x:x + FRAME_W]
            bg = cv2.resize(bg, (FRAME_W, FRAME_H), interpolation=cv2.INTER_NEAREST)
            bg = cv2.cvtColor(bg, cv2.COLOR_GRAY2BGR)

            text_mask = np.zeros((FRAME_H, FRAME_W), dtype=np.uint8)

            for ch in chars:
                offset = int(
                    cfg.get("bounce_amplitude", 8)
                    * math.sin(cfg.get("bounce_speed", 2.0) * t + ch["phase"])
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

            # text texture noise
            text_noise = np.random.randint(
                0, 256, (FRAME_H, FRAME_W), dtype=np.uint8
            )
            text_texture = cv2.bitwise_and(text_noise, text_mask)

            # composite
            text_bgr = cv2.cvtColor(text_texture, cv2.COLOR_GRAY2BGR)
            mask_inv = cv2.bitwise_not(text_mask)

            bg_part = cv2.bitwise_and(bg, bg, mask=mask_inv)
            text_part = cv2.bitwise_and(text_bgr, text_bgr, mask=text_mask)

            frame = cv2.add(bg_part, text_part)
            self.frames.append(frame)

            # update noise viewport
            x = (x + SPEED_X) % (noise_w - FRAME_W)
            y = (y + SPEED_Y) % (noise_h - FRAME_H)
            t += 1 / fps


    # ---------------- HELPERS ----------------
    def _prepare_foreground_chars(self):
        imgs = []
        spacings = []
        total_width = 0

        for ch in self.text:
            spacings.append(
                random.randint(self.cfg["min_spacing"], self.cfg["max_spacing"])
            )

            (cw, ch_h), baseline = cv2.getTextSize(
                ch,
                self.cfg["font"],
                self.cfg["font_scale"],
                self.cfg["font_thickness"]
            )

            canvas = np.zeros((ch_h + baseline + 20, cw + 20), dtype=np.uint8)
            cv2.putText(
                canvas,
                ch,
                (10, ch_h + 10),
                self.cfg["font"],
                self.cfg["font_scale"],
                255,
                self.cfg["font_thickness"],
                cv2.LINE_8
            )

            angle = random.uniform(-self.cfg["max_rotation"], self.cfg["max_rotation"])
            M = cv2.getRotationMatrix2D(
                (canvas.shape[1] // 2, canvas.shape[0] // 2),
                angle,
                1.0
            )

            img = cv2.warpAffine(canvas, M, canvas.shape[::-1])
            imgs.append(img)
            total_width += img.shape[1] + spacings[-1]

        return imgs, spacings, total_width

    def _init_bg_chars(self):
        return [self._new_bg_char(initial=True) for _ in range(self.cfg["initial_bg_count"])]

    def _new_bg_char(self, initial=False):
        return dict(
            char=random.choice(self.ALPHABET),
            x=random.randint(-40, self.w),
            y=random.randint(-40, self.h),
            vx=random.uniform(-0.5, 0.5),
            vy=random.uniform(-self.cfg["bg_speed_max"], -self.cfg["bg_speed_min"]),
            angle=random.uniform(-15, 15)
        )

    def _draw_bg_chars(self, frame, chars):
        new = []
        for c in chars:
            c["x"] += c["vx"]
            c["y"] += c["vy"]

            if -80 < c["x"] < self.w + 80 and c["y"] > -80:
                new.append(c)

                canvas = np.zeros((50, 50), dtype=np.uint8)
                cv2.putText(
                    canvas,
                    c["char"],
                    (5, 40),
                    self.cfg["font"],
                    self.cfg["font_scale"],
                    255,
                    self.cfg["font_thickness"],
                    cv2.LINE_8
                )

                M = cv2.getRotationMatrix2D((25, 25), c["angle"], 1)
                img = cv2.warpAffine(canvas, M, (50, 50))
                self._blit(frame, img, int(c["x"]), int(c["y"]))

        return new

    def _blit(self, frame, img, x, y):
        h, w = img.shape
        for iy in range(h):
            for ix in range(w):
                if img[iy, ix] > 0:
                    yy, xx = y + iy, x + ix
                    if 0 <= xx < self.w and 0 <= yy < self.h:
                        frame[yy, xx] = (self.fg_color,) * 3

    # ---------------- EXPORT ----------------
    def _export(self):
        out = Path(self.cfg["output_name"])

        if self.cfg["export_format"] == "gif":
            imageio.mimsave(
                out.with_suffix(".gif"),
                [cv2.cvtColor(f, cv2.COLOR_BGR2RGB) for f in self.frames],
                fps=self.cfg["fps"]
            )

        elif self.cfg["export_format"] == "mp4":
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            vw = cv2.VideoWriter(
                str(out.with_suffix(".mp4")),
                fourcc,
                self.cfg["fps"],
                (self.w, self.h)
            )
            for f in self.frames:
                vw.write(f)
            vw.release()

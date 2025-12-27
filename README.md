# CAPTCHA Generator Module

A Python module for generating **animated CAPTCHA challenges** using OpenCV.

This project supports multiple CAPTCHA types, including:
- **Noise-based CAPTCHA** (text made of noise with moving static background)
- **Text-based CAPTCHA** (floating background characters with stable foreground text)

The output can be exported as **GIF or MP4**, or used directly as frames.

---

## Features

- Two CAPTCHA types:
  - `noise` – static noise background with mask-based text
  - `text` – floating background characters
- Fully parameterized (size, speed, font, rotation, spacing, colors)
- Light / dark mode
- Random or user-provided CAPTCHA text
- Export to GIF or MP4
- Designed to be extensible (add new CAPTCHA types easily)

---

## Configuration Options

Captcha(
    captcha_type="noise",        # "noise" or "text"
    frame_size=(500, 160),
    fps=30,
    duration=4.0,

    font_scale=2.5,
    font_thickness=2,
    max_rotation=15,
    min_spacing=2,
    max_spacing=6,

    color_mode="light",          # "light" or "dark"

    bg_spawn_rate=10,
    bg_speed_min=0.6,
    bg_speed_max=2.0,
    initial_bg_count=25,

    export=True,
    export_format="gif",         # "gif" or "mp4"
    output_name="captcha",

    captcha_text=None            # None = random
)


## Installation

Create a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

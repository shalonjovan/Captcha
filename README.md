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

## Installation

Create a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

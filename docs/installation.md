# Installation

## Requirements

- Python **3.9+**
- A platform supported by NumPy, OpenCV, and Pillow (Linux, macOS, Windows)

## Install from PyPI

```bash
pip install captcha-forge
```

Verify the installation:

```bash
python -c "import captcha_forge; print(captcha_forge.__version__)"
captcha-forge list
```

## Install from source

```bash
git clone https://github.com/shalonjovan/Captcha.git
cd Captcha
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,docs]"
```

On Windows, activate the environment with `.venv\Scripts\activate`.

## Optional dependencies

| Extra | Purpose | Install |
| --- | --- | --- |
| `dev` | tests, linting, typing, build tools | `pip install -e ".[dev]"` |
| `docs` | MkDocs Material and mkdocstrings | `pip install -e ".[docs]"` |

The runtime dependencies are:

- `numpy`
- `opencv-python-headless`
- `Pillow`

## A note about OpenCV builds

Captcha Forge uses `opencv-python-headless`, which avoids GUI dependencies and
is the right choice for servers and headless containers. Do not install both
`opencv-python` and `opencv-python-headless` in the same environment; they
provide the same `cv2` module and can overwrite each other.

If you need a GUI build of OpenCV for another part of your application, install
`opencv-python` and remove `opencv-python-headless`:

```bash
pip uninstall opencv-python-headless
pip install opencv-python
```

## Docker

```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 \
    && rm -rf /var/lib/apt/lists/*
RUN pip install captcha-forge
```

The headless OpenCV wheel usually does not need `libgl1`, but some slim images
and older wheels do. If you see a missing `libGL.so.1` error, install
`libgl1`.

## Troubleshooting

### MP4 export fails

MP4 output uses OpenCV's `mp4v` writer. Some minimal OpenCV builds do not ship
an MP4 codec. Export a GIF or animated WebP instead, or install a full OpenCV
build.

### `libGL.so.1` is missing

Install the system OpenGL library (for Debian/Ubuntu: `apt-get install libgl1`)
or use the headless wheel.

### Fonts look different on another machine

Captcha Forge uses OpenCV Hershey vector fonts, which are built into OpenCV, so
rendering is portable. No system font files are required.

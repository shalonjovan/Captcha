# Command line

The package installs a `captcha-forge` console script. The same commands are
available as `python -m captcha_forge`.

```bash
captcha-forge --help
python -m captcha_forge --help
```

## Commands

### `list`

Print every registered type with a one-line description.

```bash
captcha-forge list
```

### `info`

Show the default size, output format, animation capability, and every supported
option for a type.

```bash
captcha-forge info
captcha-forge info text
captcha-forge info slider
```

Example output for `info text`:

```text
Type: text
Description: Animated characters over drifting, semi-transparent background letters.
Default size: 500x160
Default format: gif
Animated: yes
Options:
  max_rotation=15.0  # Maximum foreground and background glyph rotation in degrees.
  min_spacing=2  # Minimum pixel spacing between foreground characters.
  ...
```

### `generate`

Generate one challenge and write it to disk.

```bash
captcha-forge generate <type> [options]
```

Common options:

| Flag | Description |
| --- | --- |
| `-o`, `--output PATH` | Output file. The suffix selects the format. |
| `--format FORMAT` | Override the output format (`png`, `jpeg`, `gif`, `webp`, `mp4`). |
| `--width PX` | Frame width. |
| `--height PX` | Frame height. |
| `--fps N` | Animation frame rate. |
| `--duration SECONDS` | Animation duration. |
| `--seed N` | Reproducible output. |
| `--text TEXT` | Force the rendered text or expression. |
| `--length N` | Random text length. |
| `--alphabet CHARS` | Characters for random text. |
| `--color-mode MODE` | `light`, `dark`, or `custom`. |
| `--background COLOUR` | Custom background (name or hex). |
| `--foreground COLOUR` | Custom foreground (name or hex). |
| `--font NAME` | OpenCV Hershey font name. |
| `--font-scale FLOAT` | Font scale. |
| `--font-thickness N` | Font stroke thickness. |
| `--option KEY=VALUE` | Generator-specific option; repeatable. JSON values accepted. |
| `--json` | Print a JSON report instead of human-readable text. |
| `--quiet` | Suppress human-readable output. |

Examples:

```bash
# Animated text, 4 seconds, reproducible
captcha-forge generate text -o challenge.gif --duration 4 --seed 42

# Static dark image
captcha-forge generate image -o challenge.png --color-mode dark --font complex

# Arithmetic with three operands
captcha-forge generate math -o math.png --option operands=3 --option max_operand=9

# Click challenge with two targets
captcha-forge generate click -o click.png \
  --option target_count=2 \
  --option decoy_count=4

# JSON report, useful in scripts
captcha-forge generate word -o word.png --json
```

The `--option` value is parsed as JSON when possible, so booleans, numbers,
lists, and strings work:

```bash
captcha-forge generate click \
  --option 'shapes=["circle", "square"]' \
  --option 'target_count=2'
```

If JSON parsing fails, the raw string is used. This makes
`--option target_color=red` work without quotes.

When `--output` is omitted, the file is named
`captcha_<type>.<suggested-format>`, for example `captcha_text.gif`.

### `gallery`

Generate one sample of every type into a directory. Animated types use a short
1.5-second sample by default.

```bash
captcha-forge gallery -o captcha-gallery
captcha-forge gallery -o captcha-gallery --types image,math,click
captcha-forge gallery -o captcha-gallery --seed 2026 --duration 2
```

| Flag | Description |
| --- | --- |
| `-o`, `--output-dir DIR` | Destination directory (default `captcha-gallery`). |
| `--types LIST` | Comma-separated subset of type names. |
| `--seed N` | Base seed; each type gets a different seed. |
| `--fps N` | Frame rate for animated types. |
| `--duration SECONDS` | Duration for animated types. |
| `--quiet` | Suppress per-file output. |

## JSON output

`--json` writes a single JSON object to stdout:

```json
{
  "type": "click",
  "path": "click.png",
  "width": 460,
  "height": 320,
  "frames": 1,
  "fps": 30,
  "duration": 0.0333,
  "answer": [[183, 117], [277, 108], [397, 120]],
  "text": null,
  "metadata": {
    "instruction": "Click every circle",
    "target_shape": "circle",
    "target_color": "blue",
    "targets": [
      {"x": 183, "y": 117, "shape": "circle", "color": "blue", "radius": 38}
    ],
    "tolerance": 38
  }
}
```

`answer` is type-specific: a string for text-based challenges, a number for
slider/rotate, or a list of coordinates for click/pattern. Review the
[Challenge types](captcha-types.md) table before comparing answers.

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success. |
| `1` | Filesystem or export error. |
| `2` | Configuration, unknown type, or invalid CLI option. |

## Scripting tips

- Use `--quiet` when you only care about the file.
- Use `--json` to capture the answer and metadata for a test harness.
- Use `--seed` to make gallery or regression snapshots reproducible.
- MP4 output depends on OpenCV's `mp4v` codec. If it is unavailable, use GIF or
  WebP, or call `result.save()` from Python after checking the error.

"""CLI tests."""

from __future__ import annotations

import json
from pathlib import Path

from captcha_forge.cli import main


def test_list(capsys) -> None:
    assert main(["list"]) == 0
    output = capsys.readouterr().out
    for name in ("text", "noise", "image", "math", "word", "slider", "click", "pattern", "rotate"):
        assert name in output


def test_info(capsys) -> None:
    assert main(["info", "text"]) == 0
    output = capsys.readouterr().out
    assert "Type: text" in output
    assert "max_rotation" in output
    assert "Animated: yes" in output


def test_generate_png(tmp_path: Path, capsys) -> None:
    output = tmp_path / "challenge.png"
    code = main(
        [
            "generate",
            "image",
            "--seed",
            "42",
            "--text",
            "HELLO",
            "--output",
            str(output),
            "--quiet",
        ]
    )
    assert code == 0
    assert output.exists()
    assert capsys.readouterr().out == ""


def test_generate_json(tmp_path: Path, capsys) -> None:
    output = tmp_path / "challenge.png"
    code = main(
        [
            "generate",
            "click",
            "--seed",
            "5",
            "--output",
            str(output),
            "--json",
        ]
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["type"] == "click"
    assert payload["path"] == str(output)
    assert payload["frames"] == 1
    assert isinstance(payload["answer"], list)
    assert payload["metadata"]["instruction"].startswith("Click every")


def test_generate_with_option(tmp_path: Path) -> None:
    output = tmp_path / "challenge.png"
    code = main(
        [
            "generate",
            "text",
            "--duration",
            "0.2",
            "--fps",
            "5",
            "--option",
            "min_spacing=0",
            "--option",
            "max_spacing=1",
            "--output",
            str(output),
        ]
    )
    assert code == 0
    assert output.exists()


def test_gallery_subset(tmp_path: Path) -> None:
    code = main(
        [
            "gallery",
            "--types",
            "image,math",
            "--output-dir",
            str(tmp_path),
            "--seed",
            "3",
            "--quiet",
        ]
    )
    assert code == 0
    assert (tmp_path / "image.png").exists()
    assert (tmp_path / "math.png").exists()


def test_unknown_type(capsys) -> None:
    assert main(["generate", "nope"]) == 2
    error = capsys.readouterr().err
    assert "Unknown CAPTCHA type" in error


def test_invalid_option(capsys) -> None:
    assert main(["generate", "text", "--option", "bad"]) == 2
    assert "KEY=VALUE" in capsys.readouterr().err

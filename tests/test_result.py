"""CaptchaResult and export tests."""

from __future__ import annotations

import numpy as np
import pytest

from captcha_forge import Captcha, CaptchaResult, ExportError


def _result():
    return Captcha("text", seed=11, duration=0.4, fps=10).generate()


def test_sequence_protocol() -> None:
    result = _result()
    assert len(result) == 4
    assert result[0].shape == result.frames[0].shape
    assert len(list(iter(result))) == 4
    assert result.image is result.frames[0]
    assert result.duration == pytest.approx(0.4)


def test_repr_contains_type_and_answer() -> None:
    result = _result()
    text = repr(result)
    assert "text" in text
    assert "frames=4" in text
    assert result.answer in text


@pytest.mark.parametrize("suffix", ["png", "jpg", "gif", "webp"])
def test_save_image_and_animation(tmp_path, suffix: str) -> None:
    result = _result()
    path = result.save(tmp_path / f"challenge.{suffix}")
    assert path.exists()
    assert path.stat().st_size > 0
    data = path.read_bytes()
    if suffix == "png":
        assert data.startswith(b"\x89PNG")
    elif suffix == "jpg":
        assert data.startswith(b"\xff\xd8")
    elif suffix == "gif":
        assert data.startswith(b"GIF8")
    elif suffix == "webp":
        assert data.startswith(b"RIFF") and data[8:12] == b"WEBP"


def test_save_mp4(tmp_path) -> None:
    result = _result()
    try:
        path = result.save(tmp_path / "challenge.mp4")
    except ExportError as exc:
        pytest.skip(str(exc))
    assert path.exists()
    assert path.stat().st_size > 0
    assert path.read_bytes()[4:8] == b"ftyp"


def test_save_adds_extension(tmp_path) -> None:
    result = _result()
    path = result.save(tmp_path / "challenge")
    assert path.suffix == ".gif"
    assert path.exists()


def test_save_static_format_uses_first_frame(tmp_path) -> None:
    result = _result()
    path = result.save(tmp_path / "first.png")
    assert path.exists()


def test_save_with_explicit_format(tmp_path) -> None:
    result = _result()
    path = result.save(tmp_path / "challenge.data", format="gif")
    assert path.read_bytes().startswith(b"GIF8")


def test_to_bytes() -> None:
    result = _result()
    assert result.to_bytes("png").startswith(b"\x89PNG")
    assert result.to_bytes("gif").startswith(b"GIF8")
    with pytest.raises(ExportError):
        result.to_bytes("mp4")


def test_unsupported_format(tmp_path) -> None:
    result = _result()
    with pytest.raises(ExportError):
        result.save(tmp_path / "challenge.xyz", format="xyz")


def test_result_validation() -> None:
    frame = np.zeros((20, 20, 3), dtype=np.uint8)
    with pytest.raises(ValueError):
        CaptchaResult(captcha_type="x", frames=())
    with pytest.raises(ValueError):
        CaptchaResult(captcha_type="x", frames=(frame,), fps=0)
    with pytest.raises(ValueError):
        CaptchaResult(captcha_type="x", frames=(np.zeros((20, 20), dtype=np.uint8),))


def test_export_quality(tmp_path) -> None:
    result = Captcha("image", seed=4).generate()
    low = result.save(tmp_path / "low.jpg", quality=20)
    high = result.save(tmp_path / "high.jpg", quality=95)
    assert low.stat().st_size < high.stat().st_size

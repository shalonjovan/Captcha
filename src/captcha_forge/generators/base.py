"""Base class for CAPTCHA generators."""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Dict, List, Mapping, Sequence, Tuple

import numpy as np

from ..config import CaptchaConfig
from ..exceptions import ConfigurationError
from ..rendering import new_frame
from ..result import CaptchaResult
from ..theme import Theme, resolve_theme


class BaseGenerator(ABC):
    """Shared lifecycle for all built-in generators.

    Subclasses declare their public options in :attr:`option_defaults`; passing
    an unknown option raises a clear error instead of being silently ignored.
    """

    name: ClassVar[str] = ""
    description: ClassVar[str] = ""
    default_size: ClassVar[Tuple[int, int]] = (500, 160)
    default_format: ClassVar[str] = "png"
    animated: ClassVar[bool] = False
    option_defaults: ClassVar[Mapping[str, Any]] = {}
    option_docs: ClassVar[Mapping[str, str]] = {}

    @classmethod
    def validate_option_names(cls, options: Mapping[str, Any]) -> None:
        """Reject option names that the generator does not declare."""

        unknown = sorted(set(options) - set(cls.option_defaults))
        if unknown:
            allowed = ", ".join(sorted(cls.option_defaults)) or "none"
            raise ConfigurationError(
                f"Unsupported option(s) for {cls.name!r}: {', '.join(unknown)}. "
                f"Supported options: {allowed}"
            )

    def __init__(self, config: CaptchaConfig, **options: Any) -> None:
        if not self.name:
            raise ConfigurationError("A generator must define a name")
        self.config = config
        self.theme: Theme = resolve_theme(config)
        self.font_face = config.font_face_id
        self.width, self.height = config.resolved_size(self.default_size)
        self.rng = random.Random(config.seed)
        self.np_rng = np.random.default_rng(config.seed)

        self.validate_option_names(options)
        self.options: Dict[str, Any] = dict(self.option_defaults)
        self.options.update(options)
        self._validate_options()

    def _validate_options(self) -> None:  # noqa: B027 - optional hook
        """Validate generator-specific options. Override in subclasses."""

    @property
    def option_values(self) -> Mapping[str, Any]:
        return dict(self.options)

    @classmethod
    def describe_options(cls) -> List[Dict[str, Any]]:
        """Return option metadata for the CLI and documentation tooling."""

        rows = []
        for key, default in cls.option_defaults.items():
            rows.append(
                {
                    "name": key,
                    "default": default,
                    "help": cls.option_docs.get(key, ""),
                }
            )
        return rows

    def _frame_count(self) -> int:
        return max(1, int(round(self.config.duration * self.config.fps)))

    def _text(self) -> str:
        if self.config.text is not None:
            return self.config.text
        return "".join(self.rng.choices(self.config.alphabet, k=self.config.length))

    def _new_frame(self) -> np.ndarray:
        return new_frame(self.width, self.height, self.theme.background)

    def _result(
        self,
        frames: Sequence[np.ndarray],
        *,
        answer: Any = None,
        text: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        assets: Mapping[str, np.ndarray] | None = None,
        suggested_format: str | None = None,
    ) -> CaptchaResult:
        details = {
            "width": self.width,
            "height": self.height,
            "fps": self.config.fps,
            "duration": self.config.duration,
            "color_mode": self.config.color_mode,
            "seed": self.config.seed,
        }
        if metadata:
            details.update(metadata)
        return CaptchaResult(
            captcha_type=self.name,
            frames=tuple(frames),
            answer=answer,
            text=text,
            metadata=details,
            assets=dict(assets or {}),
            fps=self.config.fps,
            suggested_format=suggested_format or self.default_format,
        )

    @abstractmethod
    def generate(self) -> CaptchaResult:
        """Render a challenge and return a :class:`~captcha_forge.result.CaptchaResult`."""

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(name={self.name!r}, "
            f"size={self.width}x{self.height}, fps={self.config.fps})"
        )


__all__ = ["BaseGenerator"]

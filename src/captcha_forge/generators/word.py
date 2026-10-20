"""Dictionary-word CAPTCHA built on the distorted image renderer."""

from __future__ import annotations

from collections.abc import Sequence
from importlib import resources
from typing import Any, Dict, List, Tuple

from ..exceptions import ConfigurationError
from ..registry import register
from .image import ImageCaptcha


@register
class WordCaptcha(ImageCaptcha):
    """Static distorted English word from a bundled or custom word list."""

    name = "word"
    description = "A distorted dictionary word with noise and interference."
    default_size = (500, 180)
    default_format = "png"

    option_defaults = {
        **ImageCaptcha.option_defaults,
        "wordlist": None,
        "min_length": 4,
        "max_length": 8,
        "uppercase": True,
    }
    option_docs = {
        **ImageCaptcha.option_docs,
        "wordlist": "Optional sequence of words or a whitespace-separated string.",
        "min_length": "Minimum word length to sample.",
        "max_length": "Maximum word length to sample.",
        "uppercase": "Render and return words in uppercase.",
    }

    def _validate_options(self) -> None:
        super()._validate_options()
        opts = self.options
        if opts["min_length"] < 1 or opts["max_length"] < opts["min_length"]:
            raise ConfigurationError("word lengths must satisfy 1 <= min_length <= max_length")
        self._words = self._load_words()

    def _load_words(self) -> List[str]:
        source = self.options["wordlist"]
        if source is None:
            with (
                resources.files("captcha_forge")
                .joinpath("data/words.txt")
                .open("r", encoding="utf-8") as handle
            ):
                raw = [line.strip() for line in handle if line.strip()]
        elif isinstance(source, str):
            raw = source.split()
        else:
            if not isinstance(source, Sequence):
                raise ConfigurationError("wordlist must be a sequence of words or a string")
            raw = [str(word).strip() for word in source]

        minimum = int(self.options["min_length"])
        maximum = int(self.options["max_length"])
        words: List[str] = []
        for word in raw:
            if not word or not word.isascii() or not word.isalpha():
                continue
            if minimum <= len(word) <= maximum:
                words.append(word)
        if not words:
            raise ConfigurationError(
                "wordlist produced no usable words; provide plain ASCII words within the "
                "configured length range"
            )
        # Preserve order while removing duplicates.
        return list(dict.fromkeys(words))

    def _make_problem(self) -> Tuple[str, Any, Dict[str, Any]]:
        word = self.config.text if self.config.text is not None else self.rng.choice(self._words)
        if self.options["uppercase"]:
            word = word.upper()
        return word, word, {"word_length": len(word), "wordlist_size": len(self._words)}


__all__ = ["WordCaptcha"]

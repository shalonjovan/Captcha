"""Generator registry and lookup helpers."""

from __future__ import annotations

from typing import Any, Dict, Type

from .exceptions import UnknownCaptchaType

_REGISTRY: Dict[str, Type[Any]] = {}
_ALIASES = {
    "arithmetic": "math",
    "animated-text": "text",
    "animated-noise": "noise",
    "words": "word",
    "drag": "slider",
    "puzzle": "slider",
    "click-select": "click",
    "rotation": "rotate",
}


def register(cls: Any = None, *, name: str | None = None):
    """Register a generator class.

    Can be used as ``@register`` or ``@register(name="custom")``.
    """

    def decorator(generator_cls: Any) -> Any:
        raw_name = name if name is not None else getattr(generator_cls, "name", "")
        key = str(raw_name).strip().lower()
        if not key:
            raise ValueError("A registered generator must define a non-empty name")
        if key in _REGISTRY and _REGISTRY[key] is not generator_cls:
            raise ValueError(f"A generator named {key!r} is already registered")
        _REGISTRY[key] = generator_cls
        return generator_cls

    if cls is None:
        return decorator
    return decorator(cls)


def _ensure_loaded() -> None:
    if not _REGISTRY:
        from . import generators  # noqa: F401  (import side effect registers classes)


def resolve_type(name: str) -> str:
    """Resolve aliases and validate a type name."""

    _ensure_loaded()
    key = str(name).strip().lower()
    key = _ALIASES.get(key, key)
    if key not in _REGISTRY:
        choices = ", ".join(sorted(_REGISTRY))
        raise UnknownCaptchaType(f"Unknown CAPTCHA type {name!r}. Available types: {choices}")
    return key


def get_generator_class(name: str) -> Type[Any]:
    """Return the generator class registered under ``name``."""

    key = resolve_type(name)
    return _REGISTRY[key]


def available_types() -> Dict[str, str]:
    """Return a mapping of type name to one-line description."""

    _ensure_loaded()
    return {
        key: getattr(generator, "description", "") for key, generator in sorted(_REGISTRY.items())
    }


def get_generator(name: str) -> Any:
    """Instantiate a generator by name (mainly useful for plugins)."""

    return get_generator_class(name)


__all__ = [
    "register",
    "resolve_type",
    "get_generator_class",
    "get_generator",
    "available_types",
]

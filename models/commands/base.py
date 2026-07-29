from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Mapping

from PIL import Image


class CommandError(ValueError):
    pass


class ImageCommand(ABC):
    name: str = ""
    parameters: set[str] = set()

    @abstractmethod
    def execute(self, options: Mapping[str, Any], *, last_output: Any, resource_root: Path) -> Any:
        raise NotImplementedError


def as_int_tuple(value: Any, length: int, name: str) -> tuple[int, ...]:
    if not isinstance(value, (list, tuple)) or len(value) != length:
        raise CommandError(f"{name} must contain exactly {length} numeric values")
    if any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in value):
        raise CommandError(f"{name} must contain only numeric values")
    return tuple(int(item) for item in value)


def resampling(value: str | None):
    names = {"nearest": "NEAREST", "bilinear": "BILINEAR", "bicubic": "BICUBIC", "lanczos": "LANCZOS"}
    value = value or "nearest"
    try:
        name = names[value.lower()]
    except (AttributeError, KeyError) as exc:
        raise CommandError(f"Unsupported resample value: {value}") from exc
    return getattr(getattr(Image, "Resampling", Image), name)


def source_image(options: Mapping[str, Any], last_output: Any, command_name: str) -> Image.Image:
    source = options.get("source", last_output)
    if source is None:
        raise CommandError(f"{command_name} has no source and no previous command output")
    if not isinstance(source, Image.Image):
        raise CommandError(f"{command_name} source must be an image")
    return source


def resource_path(root: Path, relative_path: str) -> Path:
    if not isinstance(relative_path, str) or not relative_path:
        raise CommandError("load-image path must be a non-empty resource path")
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise CommandError("load-image path must remain inside the resources directory") from exc
    if not candidate.is_file():
        raise CommandError(f"Resource image does not exist: {relative_path}")
    return candidate

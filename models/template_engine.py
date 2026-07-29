from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, Mapping

import yaml
from PIL import Image


class TemplateError(ValueError):
    """Raised when a conversion template is invalid or cannot be executed."""


REFERENCE_RE = re.compile(r"^\$([A-Za-z_][A-Za-z0-9_]*)$")
RUNTIME_VARIABLES = {"pa", "pb", "output_dir"}
MASK_MODES = {"alpha", "grayscale"}
FLIP_DIRECTIONS = {"horizontal", "vertical"}

COMMAND_PARAMETERS = {
    "copy": {"source", "register-var"},
    "new-image": {"mode", "size", "color", "register-var"},
    "load-image": {"path", "register-var"},
    "crop": {"source", "box", "register-var"},
    "resize": {"source", "size", "resample", "register-var"},
    "rotate": {"source", "angle", "expand", "resample", "fill-color", "register-var"},
    "flip": {"source", "direction", "register-var"},
    "paste": {"target", "source", "position", "mask", "register-var"},
    "composite": {"foreground", "background", "mask", "mask-mode", "register-var"},
}


def _as_int_tuple(value: Any, length: int, name: str) -> tuple:
    if not isinstance(value, (list, tuple)) or len(value) != length:
        raise TemplateError(f"{name} must contain exactly {length} numeric values")
    if any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in value):
        raise TemplateError(f"{name} must contain only numeric values")
    return tuple(int(item) for item in value)


def _resampling(value: str | None):
    value = value or "nearest"
    names = {"nearest": "NEAREST", "bilinear": "BILINEAR", "bicubic": "BICUBIC", "lanczos": "LANCZOS"}
    try:
        name = names[value.lower()]
    except (AttributeError, KeyError) as exc:
        raise TemplateError(f"Unsupported resample value: {value}") from exc
    resampling = getattr(Image, "Resampling", Image)
    return getattr(resampling, name)


def _reference(value: Any, variables: Mapping[str, Any], name: str) -> Any:
    if not isinstance(value, str):
        raise TemplateError(f"{name} must be a variable reference such as $output")
    match = REFERENCE_RE.match(value)
    if not match:
        raise TemplateError(f"{name} must be a variable reference such as $output")
    variable = match.group(1)
    if variable not in variables:
        raise TemplateError(f"Variable ${variable} is not defined before {name}")
    return variables[variable]


def _resource_path(root: Path, relative_path: str) -> Path:
    if not isinstance(relative_path, str) or not relative_path:
        raise TemplateError("load-image path must be a non-empty resource path")
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise TemplateError("load-image path must remain inside the resources directory") from exc
    if not candidate.is_file():
        raise TemplateError(f"Resource image does not exist: {relative_path}")
    return candidate


def _copy_image(source: Image.Image, **_: Any) -> Image.Image:
    return source.copy()


def _new_image(*, mode: str, size: Any, color: Any, **_: Any) -> Image.Image:
    return Image.new(mode=mode, size=_as_int_tuple(size, 2, "new-image size"), color=color)


def _load_image(*, path: Path, **_: Any) -> Image.Image:
    return Image.open(path).copy()


def _crop(*, source: Image.Image, box: Any, **_: Any) -> Image.Image:
    left, top, right, bottom = _as_int_tuple(box, 4, "crop box")
    if right <= left or bottom <= top:
        raise TemplateError("crop box must have positive width and height")
    return source.crop((left, top, right, bottom))


def _resize(*, source: Image.Image, size: Any, resample: str | None = None, **_: Any) -> Image.Image:
    width, height = _as_int_tuple(size, 2, "resize size")
    if width <= 0 or height <= 0:
        raise TemplateError("resize size must be positive")
    return source.resize((width, height), _resampling(resample))


def _rotate(*, source: Image.Image, angle: Any, expand: bool = False, resample: str | None = None, fill_color: Any = None, **_: Any) -> Image.Image:
    if isinstance(angle, bool) or not isinstance(angle, (int, float)):
        raise TemplateError("rotate angle must be numeric")
    return source.rotate(angle, resample=_resampling(resample), expand=bool(expand), fillcolor=fill_color)


def _flip(*, source: Image.Image, direction: str, **_: Any) -> Image.Image:
    operations = {"horizontal": Image.Transpose.FLIP_LEFT_RIGHT, "vertical": Image.Transpose.FLIP_TOP_BOTTOM}
    try:
        return source.transpose(operations[direction])
    except KeyError as exc:
        raise TemplateError("flip direction must be horizontal or vertical") from exc


def _paste(*, target: Image.Image, source: Image.Image, position: Any, mask: Image.Image | None = None, **_: Any) -> Image.Image:
    x, y = _as_int_tuple(position, 2, "paste position")
    result = target.copy()
    result.paste(source, (x, y), mask=mask)
    return result


def _composite(*, foreground: Image.Image, background: Image.Image, mask: Image.Image, mask_mode: str = "alpha", **_: Any) -> Image.Image:
    if mask_mode not in MASK_MODES:
        raise TemplateError("composite mask-mode must be alpha or grayscale")
    prepared_mask = mask.convert("L") if mask_mode == "grayscale" else mask
    return Image.composite(foreground, background, prepared_mask)


HANDLERS = {
    "copy": _copy_image,
    "new-image": _new_image,
    "load-image": _load_image,
    "crop": _crop,
    "resize": _resize,
    "rotate": _rotate,
    "flip": _flip,
    "paste": _paste,
    "composite": _composite,
}


def _normalize_command(command: Any, location: str) -> tuple[str, dict]:
    """Accept the concise ``- paste:`` form and the legacy ``command: paste`` form."""
    if not isinstance(command, dict):
        raise TemplateError(f"{location} must be a mapping")

    if "command" in command:
        name = command.get("command")
        options = {key: value for key, value in command.items() if key != "command"}
    elif len(command) == 1:
        name, options = next(iter(command.items()))
        options = {} if options is None else options
        if not isinstance(options, dict):
            raise TemplateError(f"{location}.{name} must contain an options mapping")
    else:
        raise TemplateError(f"{location} must use exactly one command key, such as '- paste:'")

    if name not in COMMAND_PARAMETERS:
        raise TemplateError(f"{location} uses unsupported command: {name}")
    return name, options


class TemplateEngine:
    def __init__(self, template_dir: str | os.PathLike[str], resource_root: str | os.PathLike[str]):
        self.template_dir = Path(template_dir)
        self.resource_root = Path(resource_root)
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, dict]:
        templates: Dict[str, dict] = {}
        if not self.template_dir.exists():
            raise TemplateError(f"Template directory does not exist: {self.template_dir}")
        for path in sorted(self.template_dir.glob("*.y*ml")):
            with path.open("r", encoding="utf-8") as stream:
                template = yaml.safe_load(stream)
            self.validate(template, source=str(path))
            template["_path"] = str(path)
            if template["id"] in templates:
                raise TemplateError(f"Duplicate template id: {template['id']}")
            templates[template["id"]] = template
        if not templates:
            raise TemplateError(f"No YAML templates found in {self.template_dir}")
        return templates

    @staticmethod
    def validate(template: Any, source: str = "template") -> None:
        if not isinstance(template, dict):
            raise TemplateError(f"{source} must contain a YAML mapping")
        required = {"id", "display_name", "result-var", "commands"}
        missing = required - set(template)
        if missing:
            raise TemplateError(f"{source} is missing required fields: {', '.join(sorted(missing))}")
        if not isinstance(template["id"], str) or not template["id"]:
            raise TemplateError(f"{source}.id must be a non-empty string")
        if not isinstance(template["commands"], list) or not template["commands"]:
            raise TemplateError(f"{source}.commands must be a non-empty list")
        registered = set(RUNTIME_VARIABLES)
        result_var = template["result-var"]
        if not isinstance(result_var, str) or not REFERENCE_RE.match("$" + result_var):
            raise TemplateError(f"{source}.result-var must be a valid variable name")

        for index, raw_command in enumerate(template["commands"]):
            location = f"{source}.commands[{index}]"
            name, command = _normalize_command(raw_command, location)
            unknown = set(command) - COMMAND_PARAMETERS[name]
            if unknown:
                raise TemplateError(f"{location}.{name} has unsupported parameters: {', '.join(sorted(unknown))}")
            register_var = command.get("register-var")
            if not isinstance(register_var, str) or not REFERENCE_RE.match("$" + register_var):
                raise TemplateError(f"{location}.{name}.register-var must be a valid variable name")
            for key, value in command.items():
                if isinstance(value, str) and value.startswith("$"):
                    match = REFERENCE_RE.match(value)
                    if not match:
                        raise TemplateError(f"{location}.{name}.{key} is not a valid variable reference")
                    if match.group(1) not in registered:
                        raise TemplateError(f"{location}.{name}.{key} references undefined variable {value}")
            if name == "flip" and command.get("direction") not in FLIP_DIRECTIONS:
                raise TemplateError(f"{location}.flip.direction must be horizontal or vertical")
            if name == "composite" and command.get("mask-mode", "alpha") not in MASK_MODES:
                raise TemplateError(f"{location}.composite.mask-mode must be alpha or grayscale")
            registered.add(register_var)
        if result_var not in registered:
            raise TemplateError(f"{source}.result-var ${result_var} is never registered")

    def execute(self, template_id: str, pa: Image.Image, pb: Image.Image, output_dir: str = "") -> Image.Image:
        try:
            template = self.templates[template_id]
        except KeyError as exc:
            raise TemplateError(f"Unknown conversion template: {template_id}") from exc
        variables: Dict[str, Any] = {"pa": pa, "pb": pb, "output_dir": output_dir}
        for index, raw_command in enumerate(template["commands"]):
            name, command = _normalize_command(raw_command, f"commands[{index}]")
            args: Dict[str, Any] = {}
            for key, value in command.items():
                if key == "register-var":
                    continue
                if isinstance(value, str) and value.startswith("$"):
                    args[key.replace("-", "_")] = _reference(value, variables, f"commands[{index}].{name}.{key}")
                else:
                    args[key.replace("-", "_")] = value
            if name == "load-image":
                args["path"] = _resource_path(self.resource_root, args["path"])
            variables[command["register-var"]] = HANDLERS[name](**args)
        return variables[template["result-var"]]

    def choices(self) -> list[tuple[str, str]]:
        return [(template_id, self.templates[template_id]["display_name"]) for template_id in self.templates]

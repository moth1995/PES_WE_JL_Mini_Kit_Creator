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
    "copy": {"source"},
    "new-image": {"mode", "size", "color"},
    "load-image": {"path"},
    "crop": {"source", "box"},
    "resize": {"source", "size", "resample"},
    "rotate": {"source", "angle", "expand", "resample", "fill-color"},
    "flip": {"source", "direction"},
    "paste": {"target", "source", "position", "mask"},
    "composite": {"foreground", "background", "mask", "mask-mode"},
}


def _as_int_tuple(value: Any, length: int, name: str) -> tuple:
    if not isinstance(value, (list, tuple)) or len(value) != length:
        raise TemplateError(f"{name} must contain exactly {length} numeric values")
    if any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in value):
        raise TemplateError(f"{name} must contain only numeric values")
    return tuple(int(item) for item in value)


def _resampling(value: str | None):
    names = {"nearest": "NEAREST", "bilinear": "BILINEAR", "bicubic": "BICUBIC", "lanczos": "LANCZOS"}
    value = value or "nearest"
    try:
        name = names[value.lower()]
    except (AttributeError, KeyError) as exc:
        raise TemplateError(f"Unsupported resample value: {value}") from exc
    return getattr(getattr(Image, "Resampling", Image), name)


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


def _copy(source: Image.Image, **_: Any) -> Image.Image:
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
    return Image.composite(foreground, background, mask.convert("L") if mask_mode == "grayscale" else mask)


HANDLERS = {
    "copy": _copy,
    "new-image": _new_image,
    "load-image": _load_image,
    "crop": _crop,
    "resize": _resize,
    "rotate": _rotate,
    "flip": _flip,
    "paste": _paste,
    "composite": _composite,
}


def _normalize_command(item: Any, location: str) -> tuple[str, dict, str | None]:
    """Return command name, options, and the standalone registration name."""
    if not isinstance(item, dict) or not item:
        raise TemplateError(f"{location} must be a non-empty mapping")

    # Preferred syntax: ``- resize: {...}`` followed by ``register-var: name``.
    if "command" not in item:
        commands = [(key, value) for key, value in item.items() if key != "register-var"]
        if len(commands) != 1:
            raise TemplateError(f"{location} must contain exactly one command key")
        name, options = commands[0]
        register_var = item.get("register-var")
    else:
        name = item.get("command")
        options = {key: value for key, value in item.items() if key not in {"command", "register-var"}}
        register_var = item.get("register-var")

    if name not in COMMAND_PARAMETERS:
        raise TemplateError(f"{location} uses unsupported command: {name}")
    if options is None:
        options = {}
    if not isinstance(options, dict):
        raise TemplateError(f"{location}.{name} must contain an options mapping")
    unknown = set(options) - COMMAND_PARAMETERS[name]
    if unknown:
        raise TemplateError(f"{location}.{name} has unsupported parameters: {', '.join(sorted(unknown))}")
    if register_var is not None and (not isinstance(register_var, str) or not REFERENCE_RE.match("$" + register_var)):
        raise TemplateError(f"{location}.register-var must be a valid variable name")
    return name, dict(options), register_var


def _validate_commands(template: dict, source: str) -> None:
    registered = set(RUNTIME_VARIABLES)
    has_last_output = False
    for index, item in enumerate(template["commands"]):
        location = f"{source}.commands[{index}]"
        name, options, register_var = _normalize_command(item, location)

        for key, value in options.items():
            if isinstance(value, str) and value.startswith("$"):
                match = REFERENCE_RE.match(value)
                if not match:
                    raise TemplateError(f"{location}.{name}.{key} is not a valid variable reference")
                if match.group(1) not in registered:
                    raise TemplateError(f"{location}.{name}.{key} references undefined variable {value}")

        if name == "flip" and options.get("direction") not in FLIP_DIRECTIONS:
            raise TemplateError(f"{location}.flip.direction must be horizontal or vertical")
        if name == "composite" and options.get("mask-mode", "alpha") not in MASK_MODES:
            raise TemplateError(f"{location}.composite.mask-mode must be alpha or grayscale")

        # Every command may omit its input references. In that case execution uses
        # the previous command output. The first command must provide its inputs.
        implicit_keys = {
            "copy": ("source",),
            "crop": ("source",),
            "resize": ("source",),
            "rotate": ("source",),
            "flip": ("source",),
            "paste": ("target", "source"),
            "composite": ("foreground", "background", "mask"),
        }.get(name, ())
        if not has_last_output and any(key not in options for key in implicit_keys):
            missing = ", ".join(key for key in implicit_keys if key not in options)
            raise TemplateError(f"{location}.{name} requires {missing}; no previous command output exists")

        has_last_output = True
        if register_var is not None:
            registered.add(register_var)

    result_var = template["result-var"]
    if result_var not in registered:
        raise TemplateError(f"{source}.result-var ${result_var} is never registered")


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
        result_var = template["result-var"]
        if not isinstance(result_var, str) or not REFERENCE_RE.match("$" + result_var):
            raise TemplateError(f"{source}.result-var must be a valid variable name")
        _validate_commands(template, source)

    def execute(self, template_id: str, pa: Image.Image, pb: Image.Image, output_dir: str = "") -> Image.Image:
        try:
            template = self.templates[template_id]
        except KeyError as exc:
            raise TemplateError(f"Unknown conversion template: {template_id}") from exc

        variables: Dict[str, Any] = {"pa": pa, "pb": pb, "output_dir": output_dir}
        last_output: Any = None
        for index, item in enumerate(template["commands"]):
            location = f"commands[{index}]"
            name, options, register_var = _normalize_command(item, location)
            args: Dict[str, Any] = {}
            for key, value in options.items():
                if isinstance(value, str) and value.startswith("$"):
                    args[key.replace("-", "_")] = _reference(value, variables, f"{location}.{name}.{key}")
                else:
                    args[key.replace("-", "_")] = value

            # Any omitted input is the most recent command output. A first-command
            # omission is rejected instead of silently using runtime variables.
            if name in {"copy", "crop", "resize", "rotate", "flip"} and "source" not in args:
                if last_output is None:
                    raise TemplateError(f"{location}.{name} has no source and no previous command output")
                args["source"] = last_output
            elif name == "paste":
                if "target" not in args:
                    if last_output is None:
                        raise TemplateError(f"{location}.paste has no target and no previous command output")
                    args["target"] = last_output
                if "source" not in args:
                    if last_output is None:
                        raise TemplateError(f"{location}.paste has no source and no previous command output")
                    args["source"] = last_output
            elif name == "composite":
                for key in ("foreground", "background", "mask"):
                    if key not in args:
                        if last_output is None:
                            raise TemplateError(f"{location}.composite has no {key} and no previous command output")
                        args[key] = last_output

            if name == "load-image":
                args["path"] = _resource_path(self.resource_root, args["path"])
            last_output = HANDLERS[name](**args)
            if register_var is not None:
                variables[register_var] = last_output

        return variables[template["result-var"]]

    def choices(self) -> list[tuple[str, str]]:
        return [(template_id, self.templates[template_id]["display_name"]) for template_id in self.templates]

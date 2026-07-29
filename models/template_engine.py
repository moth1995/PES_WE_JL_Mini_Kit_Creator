from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, Mapping

import yaml

from .commands import COMMANDS, CommandError


class TemplateError(ValueError):
    """Raised when a conversion template is invalid or cannot be executed."""


REFERENCE_RE = re.compile(r"^\$([A-Za-z_][A-Za-z0-9_]*)$")
RUNTIME_VARIABLES = {"pa", "pb", "output_dir"}


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


def _normalize_command(item: Any, location: str) -> tuple[str, dict, str | None]:
    if not isinstance(item, dict) or not item:
        raise TemplateError(f"{location} must be a non-empty mapping")
    if "command" in item:
        name = item.get("command")
        options = {key: value for key, value in item.items() if key not in {"command", "register-var"}}
    else:
        commands = [(key, value) for key, value in item.items() if key != "register-var"]
        if len(commands) != 1:
            raise TemplateError(f"{location} must contain exactly one command key")
        name, options = commands[0]
    if name not in COMMANDS:
        raise TemplateError(f"{location} uses unsupported command: {name}")
    if options is None:
        options = {}
    if not isinstance(options, dict):
        raise TemplateError(f"{location}.{name} must contain an options mapping")
    unknown = set(options) - COMMANDS[name].parameters
    if unknown:
        raise TemplateError(f"{location}.{name} has unsupported parameters: {', '.join(sorted(unknown))}")
    register_var = item.get("register-var")
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
        input_keys = {
            "copy": ("source",), "crop": ("source",), "resize": ("source",),
            "rotate": ("source",), "flip": ("source",), "paste": ("target", "source"),
            "composite": ("foreground", "background", "mask"),
        }.get(name, ())
        if not has_last_output and any(key not in options for key in input_keys):
            missing = ", ".join(key for key in input_keys if key not in options)
            raise TemplateError(f"{location}.{name} requires {missing}; no previous command output exists")
        if register_var is not None:
            registered.add(register_var)
        has_last_output = True
    if template["result-var"] not in registered:
        raise TemplateError(f"{source}.result-var ${template['result-var']} is never registered")


class TemplateEngine:
    def __init__(self, template_dir: str | os.PathLike[str], resource_root: str | os.PathLike[str]):
        self.template_dir = Path(template_dir)
        self.resource_root = Path(resource_root)
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, dict]:
        templates = {}
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
        if not isinstance(template["commands"], list) or not template["commands"]:
            raise TemplateError(f"{source}.commands must be a non-empty list")
        if not isinstance(template["result-var"], str) or not REFERENCE_RE.match("$" + template["result-var"]):
            raise TemplateError(f"{source}.result-var must be a valid variable name")
        _validate_commands(template, source)

    def execute(self, template_id: str, pa, pb, output_dir: str = ""):
        try:
            template = self.templates[template_id]
        except KeyError as exc:
            raise TemplateError(f"Unknown conversion template: {template_id}") from exc
        variables = {"pa": pa, "pb": pb, "output_dir": output_dir}
        last_output = None
        for index, item in enumerate(template["commands"]):
            location = f"commands[{index}]"
            name, options, register_var = _normalize_command(item, location)
            resolved = {}
            for key, value in options.items():
                resolved[key] = _reference(value, variables, f"{location}.{name}.{key}") if isinstance(value, str) and value.startswith("$") else value
            try:
                last_output = COMMANDS[name].execute(resolved, last_output=last_output, resource_root=self.resource_root)
            except CommandError as exc:
                raise TemplateError(f"{location}.{name}: {exc}") from exc
            if register_var is not None:
                variables[register_var] = last_output
        return variables[template["result-var"]]

    def choices(self) -> list[tuple[str, str]]:
        return [(template_id, template["display_name"]) for template_id, template in self.templates.items()]

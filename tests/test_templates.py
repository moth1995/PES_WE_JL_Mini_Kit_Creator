"""Integration tests for the YAML template files."""
import os
import pathlib

import pytest
import yaml
from PIL import Image

from models.template_engine import TemplateEngine, TemplateError


REPO_ROOT = pathlib.Path(__file__).parent.parent
TEMPLATES_DIR = REPO_ROOT / "templates"
RESOURCES_DIR = REPO_ROOT / "resources"

EXPECTED_TEMPLATE_IDS = {
    "pes2013-old-style",
    "pes2013-pes14-style-like",
    "we10-old-style",
    "we10-pes14-style-like",
}


class TestTemplateLoading:
    def test_all_templates_load_without_error(self):
        engine = TemplateEngine(TEMPLATES_DIR, REPO_ROOT)
        assert set(engine.templates.keys()) == EXPECTED_TEMPLATE_IDS

    def test_each_template_validates_individually(self):
        for path in sorted(TEMPLATES_DIR.glob("*.y*ml")):
            with path.open("r", encoding="utf-8") as stream:
                template = yaml.safe_load(stream)
            TemplateEngine.validate(template, source=str(path))

    def test_templates_use_new_command_key_syntax(self):
        for path in sorted(TEMPLATES_DIR.glob("*.y*ml")):
            with path.open("r", encoding="utf-8") as stream:
                template = yaml.safe_load(stream)
            for index, item in enumerate(template["commands"]):
                assert "command" not in item, (
                    f"{path.name} command[{index}] still uses the old 'command:' key syntax"
                )

    def test_template_choices_returns_all_templates(self):
        engine = TemplateEngine(TEMPLATES_DIR, REPO_ROOT)
        choices = engine.choices()
        ids = {tid for tid, _ in choices}
        assert ids == EXPECTED_TEMPLATE_IDS

    def test_display_names_are_strings(self):
        engine = TemplateEngine(TEMPLATES_DIR, REPO_ROOT)
        for tid, display_name in engine.choices():
            assert isinstance(display_name, str) and display_name


class TestTemplateExecution:
    @pytest.fixture
    def engine(self):
        return TemplateEngine(TEMPLATES_DIR, REPO_ROOT)

    @pytest.fixture
    def pa(self):
        return Image.new("RGBA", (512, 256), color=(200, 100, 50, 255))

    @pytest.fixture
    def pb(self):
        return Image.new("RGBA", (512, 256), color=(50, 100, 200, 255))

    @pytest.mark.parametrize("template_id", sorted(EXPECTED_TEMPLATE_IDS))
    def test_template_executes_and_returns_image(self, engine, pa, pb, template_id):
        result = engine.execute(template_id, pa, pb)
        assert isinstance(result, Image.Image)

    @pytest.mark.parametrize("template_id", sorted(EXPECTED_TEMPLATE_IDS))
    def test_output_is_128x128(self, engine, pa, pb, template_id):
        result = engine.execute(template_id, pa, pb)
        assert result.size == (128, 128)

    @pytest.mark.parametrize("template_id", sorted(EXPECTED_TEMPLATE_IDS))
    def test_output_is_rgba(self, engine, pa, pb, template_id):
        result = engine.execute(template_id, pa, pb)
        assert result.mode == "RGBA"

    def test_unknown_template_raises_error(self, engine, pa, pb):
        with pytest.raises(TemplateError, match="Unknown conversion template"):
            engine.execute("nonexistent-template", pa, pb)

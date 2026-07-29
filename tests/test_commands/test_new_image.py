from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from models.commands.new_image import NewImageCommand
from models.commands.base import CommandError

ROOT = Path("/tmp")


class TestNewImageCommand:
    def setup_method(self):
        self.cmd = NewImageCommand()

    # ------------------------------------------------------------------
    # Successful execution
    # ------------------------------------------------------------------

    def test_creates_rgb_image(self):
        result = self.cmd.execute(
            {"mode": "RGB", "size": [100, 50], "color": (255, 0, 0)},
            last_output=None,
            resource_root=ROOT,
        )
        assert isinstance(result, Image.Image)
        assert result.mode == "RGB"
        assert result.size == (100, 50)

    def test_creates_rgba_image(self):
        result = self.cmd.execute(
            {"mode": "RGBA", "size": [32, 32], "color": (0, 128, 255, 200)},
            last_output=None,
            resource_root=ROOT,
        )
        assert result.mode == "RGBA"
        assert result.size == (32, 32)

    def test_creates_l_image(self):
        result = self.cmd.execute(
            {"mode": "L", "size": [8, 8], "color": 128},
            last_output=None,
            resource_root=ROOT,
        )
        assert result.mode == "L"

    def test_color_defaults_to_none(self):
        result = self.cmd.execute(
            {"mode": "RGB", "size": [4, 4]},
            last_output=None,
            resource_root=ROOT,
        )
        assert isinstance(result, Image.Image)

    def test_size_as_tuple(self):
        result = self.cmd.execute(
            {"mode": "RGB", "size": (16, 8)},
            last_output=None,
            resource_root=ROOT,
        )
        assert result.size == (16, 8)

    def test_float_size_values_are_truncated(self):
        result = self.cmd.execute(
            {"mode": "RGB", "size": [10.9, 4.1]},
            last_output=None,
            resource_root=ROOT,
        )
        assert result.size == (10, 4)

    def test_last_output_is_ignored(self):
        last = Image.new("RGB", (999, 999))
        result = self.cmd.execute(
            {"mode": "L", "size": [2, 2]},
            last_output=last,
            resource_root=ROOT,
        )
        assert result.size == (2, 2)

    # ------------------------------------------------------------------
    # Error conditions — mode
    # ------------------------------------------------------------------

    def test_raises_when_mode_missing(self):
        with pytest.raises(CommandError):
            self.cmd.execute({"size": [10, 10]}, last_output=None, resource_root=ROOT)

    def test_raises_when_mode_is_none(self):
        with pytest.raises(CommandError):
            self.cmd.execute({"mode": None, "size": [10, 10]}, last_output=None, resource_root=ROOT)

    def test_raises_when_mode_is_integer(self):
        with pytest.raises(CommandError):
            self.cmd.execute({"mode": 1, "size": [10, 10]}, last_output=None, resource_root=ROOT)

    # ------------------------------------------------------------------
    # Error conditions — size
    # ------------------------------------------------------------------

    def test_raises_when_size_missing(self):
        with pytest.raises(CommandError):
            self.cmd.execute({"mode": "RGB"}, last_output=None, resource_root=ROOT)

    def test_raises_when_size_has_one_element(self):
        with pytest.raises(CommandError):
            self.cmd.execute({"mode": "RGB", "size": [10]}, last_output=None, resource_root=ROOT)

    def test_raises_when_size_has_three_elements(self):
        with pytest.raises(CommandError):
            self.cmd.execute({"mode": "RGB", "size": [10, 10, 10]}, last_output=None, resource_root=ROOT)

    def test_raises_when_size_contains_string(self):
        with pytest.raises(CommandError):
            self.cmd.execute({"mode": "RGB", "size": ["a", "b"]}, last_output=None, resource_root=ROOT)

    def test_raises_when_size_contains_bool(self):
        with pytest.raises(CommandError):
            self.cmd.execute({"mode": "RGB", "size": [True, 10]}, last_output=None, resource_root=ROOT)

    def test_raises_when_size_is_not_list(self):
        with pytest.raises(CommandError):
            self.cmd.execute({"mode": "RGB", "size": "10x10"}, last_output=None, resource_root=ROOT)

    def test_name_attribute(self):
        assert self.cmd.name == "new-image"

    def test_parameters_attribute(self):
        assert self.cmd.parameters == {"mode", "size", "color"}

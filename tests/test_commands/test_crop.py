from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from models.commands.crop import CropCommand
from models.commands.base import CommandError

ROOT = Path("/tmp")


def _img(width=100, height=100, mode="RGB"):
    return Image.new(mode, (width, height), color=(0, 128, 255))


class TestCropCommand:
    def setup_method(self):
        self.cmd = CropCommand()

    # ------------------------------------------------------------------
    # Successful execution
    # ------------------------------------------------------------------

    def test_crops_to_expected_size(self):
        src = _img(100, 100)
        result = self.cmd.execute(
            {"source": src, "box": [10, 20, 60, 80]},
            last_output=None,
            resource_root=ROOT,
        )
        assert result.size == (50, 60)

    def test_crop_uses_last_output_when_source_omitted(self):
        last = _img(100, 100)
        result = self.cmd.execute(
            {"box": [0, 0, 50, 50]},
            last_output=last,
            resource_root=ROOT,
        )
        assert result.size == (50, 50)

    def test_explicit_source_overrides_last_output(self):
        src = _img(200, 200)
        last = _img(50, 50)
        result = self.cmd.execute(
            {"source": src, "box": [0, 0, 10, 10]},
            last_output=last,
            resource_root=ROOT,
        )
        assert result.size == (10, 10)

    def test_crop_corner_box(self):
        src = _img(100, 100)
        result = self.cmd.execute(
            {"source": src, "box": [0, 0, 1, 1]},
            last_output=None,
            resource_root=ROOT,
        )
        assert result.size == (1, 1)

    def test_float_box_values_are_truncated(self):
        src = _img(100, 100)
        result = self.cmd.execute(
            {"source": src, "box": [0.5, 0.5, 50.9, 50.9]},
            last_output=None,
            resource_root=ROOT,
        )
        assert result.size == (50, 50)

    # ------------------------------------------------------------------
    # Error conditions — box validation
    # ------------------------------------------------------------------

    def test_raises_when_box_has_equal_left_right(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"source": _img(), "box": [10, 0, 10, 50]},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_right_less_than_left(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"source": _img(), "box": [50, 0, 10, 50]},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_box_has_equal_top_bottom(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"source": _img(), "box": [0, 20, 50, 20]},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_bottom_less_than_top(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"source": _img(), "box": [0, 50, 50, 10]},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_box_has_three_elements(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"source": _img(), "box": [0, 0, 50]},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_box_has_five_elements(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"source": _img(), "box": [0, 0, 50, 50, 0]},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_box_contains_string(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"source": _img(), "box": [0, 0, "50", 50]},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_box_contains_bool(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"source": _img(), "box": [True, 0, 50, 50]},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_box_is_missing(self):
        with pytest.raises((CommandError, TypeError)):
            self.cmd.execute(
                {"source": _img()},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_no_source_and_no_last_output(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"box": [0, 0, 10, 10]},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_source_is_not_image(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"source": "not_an_image", "box": [0, 0, 10, 10]},
                last_output=None,
                resource_root=ROOT,
            )

    def test_name_attribute(self):
        assert self.cmd.name == "crop"

    def test_parameters_attribute(self):
        assert {"source", "box"}.issubset(self.cmd.parameters)

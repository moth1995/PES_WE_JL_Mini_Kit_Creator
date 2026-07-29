from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from models.commands.rotate import RotateCommand
from models.commands.base import CommandError

ROOT = Path("/tmp")


def _img(width=100, height=80, mode="RGB"):
    return Image.new(mode, (width, height), color=(255, 200, 100))


class TestRotateCommand:
    def setup_method(self):
        self.cmd = RotateCommand()

    # ------------------------------------------------------------------
    # Successful execution
    # ------------------------------------------------------------------

    def test_rotate_90_degrees(self):
        src = _img(100, 80)
        result = self.cmd.execute(
            {"source": src, "angle": 90},
            last_output=None,
            resource_root=ROOT,
        )
        assert isinstance(result, Image.Image)

    def test_rotate_0_degrees_returns_same_size(self):
        src = _img(100, 80)
        result = self.cmd.execute(
            {"source": src, "angle": 0},
            last_output=None,
            resource_root=ROOT,
        )
        assert result.size == (100, 80)

    def test_rotate_360_degrees(self):
        src = _img(50, 50)
        result = self.cmd.execute(
            {"source": src, "angle": 360},
            last_output=None,
            resource_root=ROOT,
        )
        assert result.size == (50, 50)

    def test_rotate_float_angle(self):
        src = _img()
        result = self.cmd.execute(
            {"source": src, "angle": 45.5},
            last_output=None,
            resource_root=ROOT,
        )
        assert isinstance(result, Image.Image)

    def test_rotate_negative_angle(self):
        src = _img()
        result = self.cmd.execute(
            {"source": src, "angle": -90},
            last_output=None,
            resource_root=ROOT,
        )
        assert isinstance(result, Image.Image)

    def test_expand_true_changes_size_for_90(self):
        src = _img(100, 60)
        result = self.cmd.execute(
            {"source": src, "angle": 90, "expand": True},
            last_output=None,
            resource_root=ROOT,
        )
        assert result.size == (60, 100)

    def test_expand_false_keeps_original_size(self):
        src = _img(100, 60)
        result = self.cmd.execute(
            {"source": src, "angle": 90, "expand": False},
            last_output=None,
            resource_root=ROOT,
        )
        assert result.size == (100, 60)

    def test_expand_defaults_to_false(self):
        src = _img(100, 60)
        result = self.cmd.execute(
            {"source": src, "angle": 90},
            last_output=None,
            resource_root=ROOT,
        )
        assert result.size == (100, 60)

    def test_fill_color_accepted(self):
        src = _img()
        result = self.cmd.execute(
            {"source": src, "angle": 45, "expand": False, "fill-color": (0, 0, 0)},
            last_output=None,
            resource_root=ROOT,
        )
        assert isinstance(result, Image.Image)

    def test_uses_last_output_when_source_omitted(self):
        last = _img(50, 50)
        result = self.cmd.execute(
            {"angle": 180},
            last_output=last,
            resource_root=ROOT,
        )
        assert isinstance(result, Image.Image)

    def test_explicit_source_overrides_last_output(self):
        src = _img(40, 40)
        last = _img(200, 200)
        result = self.cmd.execute(
            {"source": src, "angle": 0},
            last_output=last,
            resource_root=ROOT,
        )
        assert result.size == (40, 40)

    # ------------------------------------------------------------------
    # Error conditions — angle validation
    # ------------------------------------------------------------------

    def test_raises_when_angle_is_string(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"source": _img(), "angle": "90"},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_angle_is_none(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"source": _img(), "angle": None},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_angle_is_bool(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"source": _img(), "angle": True},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_angle_missing(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"source": _img()},
                last_output=None,
                resource_root=ROOT,
            )

    # ------------------------------------------------------------------
    # Error conditions — source
    # ------------------------------------------------------------------

    def test_raises_when_no_source_and_no_last_output(self):
        with pytest.raises(CommandError):
            self.cmd.execute({"angle": 90}, last_output=None, resource_root=ROOT)

    def test_raises_when_source_is_not_image(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"source": "bad", "angle": 90},
                last_output=None,
                resource_root=ROOT,
            )

    # ------------------------------------------------------------------
    # Error conditions — resample
    # ------------------------------------------------------------------

    def test_raises_on_unsupported_resample_mode(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"source": _img(), "angle": 45, "resample": "invalid"},
                last_output=None,
                resource_root=ROOT,
            )

    def test_name_attribute(self):
        assert self.cmd.name == "rotate"

    def test_parameters_attribute(self):
        assert {"source", "angle", "expand"}.issubset(self.cmd.parameters)

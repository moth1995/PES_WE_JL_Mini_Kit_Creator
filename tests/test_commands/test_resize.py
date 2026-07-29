from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from models.commands.resize import ResizeCommand
from models.commands.base import CommandError

ROOT = Path("/tmp")


def _img(width=100, height=100, mode="RGB"):
    return Image.new(mode, (width, height), color=(100, 150, 200))


class TestResizeCommand:
    def setup_method(self):
        self.cmd = ResizeCommand()

    # ------------------------------------------------------------------
    # Successful execution
    # ------------------------------------------------------------------

    def test_resizes_to_expected_dimensions(self):
        src = _img(100, 100)
        result = self.cmd.execute(
            {"source": src, "size": [50, 25]},
            last_output=None,
            resource_root=ROOT,
        )
        assert result.size == (50, 25)

    def test_uses_last_output_when_source_omitted(self):
        last = _img(80, 60)
        result = self.cmd.execute(
            {"size": [40, 30]},
            last_output=last,
            resource_root=ROOT,
        )
        assert result.size == (40, 30)

    def test_explicit_source_overrides_last_output(self):
        src = _img(200, 200)
        last = _img(10, 10)
        result = self.cmd.execute(
            {"source": src, "size": [64, 64]},
            last_output=last,
            resource_root=ROOT,
        )
        assert result.size == (64, 64)

    def test_resample_nearest(self):
        src = _img()
        result = self.cmd.execute(
            {"source": src, "size": [20, 20], "resample": "nearest"},
            last_output=None,
            resource_root=ROOT,
        )
        assert result.size == (20, 20)

    def test_resample_bilinear(self):
        src = _img()
        result = self.cmd.execute(
            {"source": src, "size": [20, 20], "resample": "bilinear"},
            last_output=None,
            resource_root=ROOT,
        )
        assert result.size == (20, 20)

    def test_resample_bicubic(self):
        src = _img()
        result = self.cmd.execute(
            {"source": src, "size": [20, 20], "resample": "bicubic"},
            last_output=None,
            resource_root=ROOT,
        )
        assert result.size == (20, 20)

    def test_resample_lanczos(self):
        src = _img()
        result = self.cmd.execute(
            {"source": src, "size": [20, 20], "resample": "lanczos"},
            last_output=None,
            resource_root=ROOT,
        )
        assert result.size == (20, 20)

    def test_resample_defaults_to_nearest_when_omitted(self):
        src = _img()
        result = self.cmd.execute(
            {"source": src, "size": [20, 20]},
            last_output=None,
            resource_root=ROOT,
        )
        assert result.size == (20, 20)

    def test_float_size_values_are_truncated(self):
        src = _img()
        result = self.cmd.execute(
            {"source": src, "size": [20.9, 10.1]},
            last_output=None,
            resource_root=ROOT,
        )
        assert result.size == (20, 10)

    def test_resample_case_insensitive(self):
        src = _img()
        result = self.cmd.execute(
            {"source": src, "size": [20, 20], "resample": "NEAREST"},
            last_output=None,
            resource_root=ROOT,
        )
        assert result.size == (20, 20)

    # ------------------------------------------------------------------
    # Error conditions — size validation
    # ------------------------------------------------------------------

    def test_raises_when_size_missing(self):
        with pytest.raises(CommandError):
            self.cmd.execute({"source": _img()}, last_output=None, resource_root=ROOT)

    def test_raises_when_width_is_zero(self):
        with pytest.raises((ValueError, CommandError)):
            self.cmd.execute(
                {"source": _img(), "size": [0, 10]},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_height_is_zero(self):
        with pytest.raises((ValueError, CommandError)):
            self.cmd.execute(
                {"source": _img(), "size": [10, 0]},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_width_is_negative(self):
        with pytest.raises((ValueError, CommandError)):
            self.cmd.execute(
                {"source": _img(), "size": [-5, 10]},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_size_has_one_element(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"source": _img(), "size": [50]},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_size_contains_string(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"source": _img(), "size": ["a", 10]},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_size_contains_bool(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"source": _img(), "size": [True, 10]},
                last_output=None,
                resource_root=ROOT,
            )

    # ------------------------------------------------------------------
    # Error conditions — resample validation
    # ------------------------------------------------------------------

    def test_raises_on_unsupported_resample_mode(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"source": _img(), "size": [10, 10], "resample": "box"},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_resample_is_numeric(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"source": _img(), "size": [10, 10], "resample": 1},
                last_output=None,
                resource_root=ROOT,
            )

    # ------------------------------------------------------------------
    # Error conditions — source
    # ------------------------------------------------------------------

    def test_raises_when_no_source_and_no_last_output(self):
        with pytest.raises(CommandError):
            self.cmd.execute({"size": [10, 10]}, last_output=None, resource_root=ROOT)

    def test_raises_when_source_is_not_image(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"source": "bad", "size": [10, 10]},
                last_output=None,
                resource_root=ROOT,
            )

    def test_name_attribute(self):
        assert self.cmd.name == "resize"

    def test_parameters_attribute(self):
        assert {"source", "size", "resample"}.issubset(self.cmd.parameters)

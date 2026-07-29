from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from models.commands.flip import FlipCommand
from models.commands.base import CommandError

ROOT = Path("/tmp")


def _img(width=40, height=20, mode="RGB"):
    img = Image.new(mode, (width, height))
    # Draw a recognizable asymmetric pattern so flips can be verified
    img.putpixel((0, 0), (255, 0, 0))
    img.putpixel((width - 1, height - 1), (0, 255, 0))
    return img


class TestFlipCommand:
    def setup_method(self):
        self.cmd = FlipCommand()

    # ------------------------------------------------------------------
    # Successful execution — horizontal
    # ------------------------------------------------------------------

    def test_horizontal_flip_returns_image(self):
        src = _img()
        result = self.cmd.execute(
            {"source": src, "direction": "horizontal"},
            last_output=None,
            resource_root=ROOT,
        )
        assert isinstance(result, Image.Image)

    def test_horizontal_flip_preserves_size(self):
        src = _img(60, 30)
        result = self.cmd.execute(
            {"source": src, "direction": "horizontal"},
            last_output=None,
            resource_root=ROOT,
        )
        assert result.size == (60, 30)

    def test_horizontal_flip_mirrors_pixels(self):
        src = _img(40, 20)
        result = self.cmd.execute(
            {"source": src, "direction": "horizontal"},
            last_output=None,
            resource_root=ROOT,
        )
        # Top-left pixel of source should appear at top-right after L-R flip
        assert result.getpixel((39, 0)) == src.getpixel((0, 0))

    # ------------------------------------------------------------------
    # Successful execution — vertical
    # ------------------------------------------------------------------

    def test_vertical_flip_returns_image(self):
        src = _img()
        result = self.cmd.execute(
            {"source": src, "direction": "vertical"},
            last_output=None,
            resource_root=ROOT,
        )
        assert isinstance(result, Image.Image)

    def test_vertical_flip_preserves_size(self):
        src = _img(60, 30)
        result = self.cmd.execute(
            {"source": src, "direction": "vertical"},
            last_output=None,
            resource_root=ROOT,
        )
        assert result.size == (60, 30)

    def test_vertical_flip_mirrors_pixels(self):
        src = _img(40, 20)
        result = self.cmd.execute(
            {"source": src, "direction": "vertical"},
            last_output=None,
            resource_root=ROOT,
        )
        # Top-left pixel of source should appear at bottom-left after T-B flip
        assert result.getpixel((0, 19)) == src.getpixel((0, 0))

    # ------------------------------------------------------------------
    # Fallback to last_output
    # ------------------------------------------------------------------

    def test_uses_last_output_when_source_omitted(self):
        last = _img()
        result = self.cmd.execute(
            {"direction": "horizontal"},
            last_output=last,
            resource_root=ROOT,
        )
        assert isinstance(result, Image.Image)

    def test_explicit_source_overrides_last_output(self):
        src = _img(10, 10)
        last = _img(80, 80)
        result = self.cmd.execute(
            {"source": src, "direction": "vertical"},
            last_output=last,
            resource_root=ROOT,
        )
        assert result.size == (10, 10)

    # ------------------------------------------------------------------
    # Error conditions — direction
    # ------------------------------------------------------------------

    def test_raises_on_invalid_direction(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"source": _img(), "direction": "diagonal"},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_direction_is_none(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"source": _img(), "direction": None},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_direction_is_missing(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"source": _img()},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_direction_has_wrong_case(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"source": _img(), "direction": "Horizontal"},
                last_output=None,
                resource_root=ROOT,
            )

    # ------------------------------------------------------------------
    # Error conditions — source
    # ------------------------------------------------------------------

    def test_raises_when_no_source_and_no_last_output(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"direction": "horizontal"},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_source_is_not_image(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"source": "not_an_image", "direction": "vertical"},
                last_output=None,
                resource_root=ROOT,
            )

    def test_name_attribute(self):
        assert self.cmd.name == "flip"

    def test_parameters_attribute(self):
        assert {"source", "direction"}.issubset(self.cmd.parameters)

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from models.commands.copy import CopyCommand
from models.commands.base import CommandError

ROOT = Path("/tmp")


def _img(width=10, height=10, mode="RGB"):
    return Image.new(mode, (width, height), color=(255, 0, 0))


class TestCopyCommand:
    def setup_method(self):
        self.cmd = CopyCommand()

    # ------------------------------------------------------------------
    # Successful execution
    # ------------------------------------------------------------------

    def test_returns_copy_of_source(self):
        src = _img()
        result = self.cmd.execute({"source": src}, last_output=None, resource_root=ROOT)
        assert result is not src
        assert result.size == src.size
        assert result.mode == src.mode

    def test_copy_pixel_data_matches(self):
        src = _img()
        result = self.cmd.execute({"source": src}, last_output=None, resource_root=ROOT)
        assert result.tobytes() == src.tobytes()

    def test_uses_last_output_when_source_omitted(self):
        last = _img(20, 20)
        result = self.cmd.execute({}, last_output=last, resource_root=ROOT)
        assert result is not last
        assert result.size == (20, 20)

    def test_explicit_source_takes_precedence_over_last_output(self):
        src = _img(10, 10)
        last = _img(30, 30)
        result = self.cmd.execute({"source": src}, last_output=last, resource_root=ROOT)
        assert result.size == (10, 10)

    def test_preserves_mode(self):
        for mode in ("RGB", "RGBA", "L"):
            src = Image.new(mode, (5, 5))
            result = self.cmd.execute({"source": src}, last_output=None, resource_root=ROOT)
            assert result.mode == mode

    # ------------------------------------------------------------------
    # Error conditions
    # ------------------------------------------------------------------

    def test_raises_when_no_source_and_no_last_output(self):
        with pytest.raises(CommandError):
            self.cmd.execute({}, last_output=None, resource_root=ROOT)

    def test_raises_when_source_is_not_image(self):
        with pytest.raises(CommandError):
            self.cmd.execute({"source": "not_an_image"}, last_output=None, resource_root=ROOT)

    def test_raises_when_last_output_is_not_image(self):
        with pytest.raises(CommandError):
            self.cmd.execute({}, last_output=42, resource_root=ROOT)

    def test_name_attribute(self):
        assert self.cmd.name == "copy"

    def test_parameters_attribute(self):
        assert "source" in self.cmd.parameters

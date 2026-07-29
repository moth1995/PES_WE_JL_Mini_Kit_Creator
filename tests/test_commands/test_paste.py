from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from models.commands.paste import PasteCommand
from models.commands.base import CommandError

ROOT = Path("/tmp")


def _img(width=100, height=100, mode="RGB", color=(0, 0, 0)):
    return Image.new(mode, (width, height), color=color)


class TestPasteCommand:
    def setup_method(self):
        self.cmd = PasteCommand()

    # ------------------------------------------------------------------
    # Successful execution
    # ------------------------------------------------------------------

    def test_paste_returns_image_with_target_size(self):
        target = _img(100, 100, color=(255, 255, 255))
        source = _img(20, 20, color=(255, 0, 0))
        result = self.cmd.execute(
            {"target": target, "source": source, "position": [10, 10]},
            last_output=None,
            resource_root=ROOT,
        )
        assert result.size == (100, 100)

    def test_paste_does_not_mutate_target(self):
        target = _img(100, 100, color=(255, 255, 255))
        source = _img(20, 20, color=(255, 0, 0))
        target_bytes_before = target.tobytes()
        self.cmd.execute(
            {"target": target, "source": source, "position": [0, 0]},
            last_output=None,
            resource_root=ROOT,
        )
        assert target.tobytes() == target_bytes_before

    def test_paste_modifies_correct_region(self):
        target = _img(100, 100, color=(255, 255, 255))
        source = _img(10, 10, color=(255, 0, 0))
        result = self.cmd.execute(
            {"target": target, "source": source, "position": [5, 5]},
            last_output=None,
            resource_root=ROOT,
        )
        assert result.getpixel((5, 5)) == (255, 0, 0)
        assert result.getpixel((0, 0)) == (255, 255, 255)

    def test_paste_with_rgba_mask(self):
        target = _img(50, 50, mode="RGBA", color=(0, 0, 0, 255))
        source = _img(10, 10, mode="RGBA", color=(255, 0, 0, 128))
        mask = _img(10, 10, mode="RGBA", color=(0, 0, 0, 128))
        result = self.cmd.execute(
            {"target": target, "source": source, "position": [0, 0], "mask": mask},
            last_output=None,
            resource_root=ROOT,
        )
        assert isinstance(result, Image.Image)

    def test_paste_at_origin(self):
        target = _img(50, 50, color=(255, 255, 255))
        source = _img(5, 5, color=(0, 0, 255))
        result = self.cmd.execute(
            {"target": target, "source": source, "position": [0, 0]},
            last_output=None,
            resource_root=ROOT,
        )
        assert result.getpixel((0, 0)) == (0, 0, 255)

    # ------------------------------------------------------------------
    # Fallback to last_output
    # ------------------------------------------------------------------

    def test_uses_last_output_as_target_when_omitted(self):
        last = _img(100, 100, color=(0, 255, 0))
        source = _img(10, 10, color=(255, 0, 0))
        result = self.cmd.execute(
            {"source": source, "position": [0, 0]},
            last_output=last,
            resource_root=ROOT,
        )
        assert result.size == (100, 100)

    def test_uses_last_output_as_source_when_omitted(self):
        target = _img(100, 100, color=(255, 255, 255))
        last = _img(10, 10, color=(0, 0, 255))
        result = self.cmd.execute(
            {"target": target, "position": [0, 0]},
            last_output=last,
            resource_root=ROOT,
        )
        assert result.getpixel((0, 0)) == (0, 0, 255)

    # ------------------------------------------------------------------
    # Error conditions
    # ------------------------------------------------------------------

    def test_raises_when_target_and_source_both_none(self):
        with pytest.raises((ValueError, CommandError)):
            self.cmd.execute(
                {"position": [0, 0]},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_position_missing(self):
        target = _img()
        source = _img(10, 10)
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"target": target, "source": source},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_position_has_one_element(self):
        target = _img()
        source = _img(10, 10)
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"target": target, "source": source, "position": [5]},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_position_has_three_elements(self):
        target = _img()
        source = _img(10, 10)
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"target": target, "source": source, "position": [5, 5, 0]},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_position_contains_string(self):
        target = _img()
        source = _img(10, 10)
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"target": target, "source": source, "position": ["x", "y"]},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_position_contains_bool(self):
        target = _img()
        source = _img(10, 10)
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"target": target, "source": source, "position": [True, 0]},
                last_output=None,
                resource_root=ROOT,
            )

    def test_name_attribute(self):
        assert self.cmd.name == "paste"

    def test_parameters_attribute(self):
        assert {"target", "source", "position", "mask"}.issubset(self.cmd.parameters)

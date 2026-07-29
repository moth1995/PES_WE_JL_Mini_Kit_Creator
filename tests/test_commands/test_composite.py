from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from models.commands.composite import CompositeCommand
from models.commands.base import CommandError

ROOT = Path("/tmp")


def _rgb(width=50, height=50, color=(255, 0, 0)):
    return Image.new("RGB", (width, height), color=color)


def _rgba(width=50, height=50, color=(255, 0, 0, 255)):
    return Image.new("RGBA", (width, height), color=color)


def _mask(width=50, height=50, value=128):
    """L-mode grayscale mask."""
    return Image.new("L", (width, height), color=value)


def _mask_rgba(width=50, height=50, alpha=128):
    """RGBA image that can serve as an alpha mask."""
    return Image.new("RGBA", (width, height), color=(0, 0, 0, alpha))


class TestCompositeCommand:
    def setup_method(self):
        self.cmd = CompositeCommand()

    # ------------------------------------------------------------------
    # Successful execution — alpha mode
    # ------------------------------------------------------------------

    def test_alpha_mode_returns_image(self):
        fg = _rgba(color=(255, 0, 0, 255))
        bg = _rgba(color=(0, 255, 0, 255))
        mask = _mask_rgba()
        result = self.cmd.execute(
            {"foreground": fg, "background": bg, "mask": mask, "mask-mode": "alpha"},
            last_output=None,
            resource_root=ROOT,
        )
        assert isinstance(result, Image.Image)
        assert result.size == (50, 50)

    def test_alpha_mode_is_default(self):
        fg = _rgba(color=(255, 0, 0, 255))
        bg = _rgba(color=(0, 255, 0, 255))
        mask = _mask_rgba()
        result = self.cmd.execute(
            {"foreground": fg, "background": bg, "mask": mask},
            last_output=None,
            resource_root=ROOT,
        )
        assert isinstance(result, Image.Image)

    # ------------------------------------------------------------------
    # Successful execution — grayscale mode
    # ------------------------------------------------------------------

    def test_grayscale_mode_returns_image(self):
        fg = _rgba(color=(255, 0, 0, 255))
        bg = _rgba(color=(0, 255, 0, 255))
        mask = _rgb()  # will be .convert("L") internally
        result = self.cmd.execute(
            {"foreground": fg, "background": bg, "mask": mask, "mask-mode": "grayscale"},
            last_output=None,
            resource_root=ROOT,
        )
        assert isinstance(result, Image.Image)
        assert result.size == (50, 50)

    def test_grayscale_mode_with_l_mask(self):
        fg = _rgba(color=(0, 0, 255, 255))
        bg = _rgba(color=(0, 255, 0, 255))
        mask = _mask(value=255)
        result = self.cmd.execute(
            {"foreground": fg, "background": bg, "mask": mask, "mask-mode": "grayscale"},
            last_output=None,
            resource_root=ROOT,
        )
        assert isinstance(result, Image.Image)

    # ------------------------------------------------------------------
    # Fallback to last_output
    # ------------------------------------------------------------------

    def test_uses_last_output_as_foreground(self):
        fg = _rgba(color=(255, 0, 0, 200))
        bg = _rgba(color=(0, 255, 0, 255))
        mask = _mask_rgba()
        result = self.cmd.execute(
            {"background": bg, "mask": mask},
            last_output=fg,
            resource_root=ROOT,
        )
        assert isinstance(result, Image.Image)

    def test_uses_last_output_as_background(self):
        fg = _rgba(color=(255, 0, 0, 200))
        bg = _rgba(color=(0, 255, 0, 255))
        mask = _mask_rgba()
        result = self.cmd.execute(
            {"foreground": fg, "mask": mask},
            last_output=bg,
            resource_root=ROOT,
        )
        assert isinstance(result, Image.Image)

    def test_uses_last_output_as_mask(self):
        fg = _rgba(color=(255, 0, 0, 200))
        bg = _rgba(color=(0, 255, 0, 255))
        mask = _mask_rgba()
        result = self.cmd.execute(
            {"foreground": fg, "background": bg},
            last_output=mask,
            resource_root=ROOT,
        )
        assert isinstance(result, Image.Image)

    # ------------------------------------------------------------------
    # Error conditions — missing inputs
    # ------------------------------------------------------------------

    def test_raises_when_all_omitted_and_no_last_output(self):
        with pytest.raises(CommandError):
            self.cmd.execute({}, last_output=None, resource_root=ROOT)

    def test_raises_when_foreground_is_none_and_no_last_output(self):
        bg = _rgba()
        mask = _mask_rgba()
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"background": bg, "mask": mask},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_background_is_none_and_no_last_output(self):
        fg = _rgba()
        mask = _mask_rgba()
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"foreground": fg, "mask": mask},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_mask_is_none_and_no_last_output(self):
        fg = _rgba()
        bg = _rgba()
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"foreground": fg, "background": bg},
                last_output=None,
                resource_root=ROOT,
            )

    # ------------------------------------------------------------------
    # Error conditions — invalid mask-mode
    # ------------------------------------------------------------------

    def test_raises_on_invalid_mask_mode(self):
        fg = _rgba()
        bg = _rgba()
        mask = _mask_rgba()
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"foreground": fg, "background": bg, "mask": mask, "mask-mode": "invalid"},
                last_output=None,
                resource_root=ROOT,
            )

    def test_raises_when_mask_mode_is_none(self):
        fg = _rgba()
        bg = _rgba()
        mask = _mask_rgba()
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"foreground": fg, "background": bg, "mask": mask, "mask-mode": None},
                last_output=None,
                resource_root=ROOT,
            )

    def test_name_attribute(self):
        assert self.cmd.name == "composite"

    def test_parameters_attribute(self):
        assert {"foreground", "background", "mask", "mask-mode"}.issubset(self.cmd.parameters)

from __future__ import annotations

import io
from pathlib import Path

import pytest
from PIL import Image

from models.commands.load_image import LoadImageCommand
from models.commands.base import CommandError

ROOT = Path("/tmp")


def _write_png(path: Path, size=(8, 8), mode="RGB"):
    img = Image.new(mode, size, color=0)
    img.save(str(path), format="PNG")


class TestLoadImageCommand:
    def setup_method(self):
        self.cmd = LoadImageCommand()
        self.resource_root = Path("/tmp/test_load_resources")
        self.resource_root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Successful execution
    # ------------------------------------------------------------------

    def test_loads_valid_image(self):
        img_path = self.resource_root / "test.png"
        _write_png(img_path)
        result = self.cmd.execute(
            {"path": "test.png"},
            last_output=None,
            resource_root=self.resource_root,
        )
        assert isinstance(result, Image.Image)
        assert result.size == (8, 8)

    def test_returns_copy_not_open_handle(self):
        img_path = self.resource_root / "copy_test.png"
        _write_png(img_path)
        result = self.cmd.execute(
            {"path": "copy_test.png"},
            last_output=None,
            resource_root=self.resource_root,
        )
        # The file should be fully loaded (copy) and independent of any file handle
        img_path.unlink()
        assert result.size == (8, 8)

    def test_loads_image_in_subdirectory(self):
        sub = self.resource_root / "sub"
        sub.mkdir(exist_ok=True)
        img_path = sub / "sub_test.png"
        _write_png(img_path)
        result = self.cmd.execute(
            {"path": "sub/sub_test.png"},
            last_output=None,
            resource_root=self.resource_root,
        )
        assert isinstance(result, Image.Image)

    def test_last_output_is_ignored(self):
        img_path = self.resource_root / "ignored_last.png"
        _write_png(img_path)
        last = Image.new("RGB", (999, 999))
        result = self.cmd.execute(
            {"path": "ignored_last.png"},
            last_output=last,
            resource_root=self.resource_root,
        )
        assert result.size == (8, 8)

    # ------------------------------------------------------------------
    # Error conditions — path validation
    # ------------------------------------------------------------------

    def test_raises_when_path_missing(self):
        with pytest.raises(CommandError):
            self.cmd.execute({}, last_output=None, resource_root=self.resource_root)

    def test_raises_when_path_is_none(self):
        with pytest.raises(CommandError):
            self.cmd.execute({"path": None}, last_output=None, resource_root=self.resource_root)

    def test_raises_when_path_is_empty_string(self):
        with pytest.raises(CommandError):
            self.cmd.execute({"path": ""}, last_output=None, resource_root=self.resource_root)

    def test_raises_when_path_is_not_string(self):
        with pytest.raises(CommandError):
            self.cmd.execute({"path": 42}, last_output=None, resource_root=self.resource_root)

    def test_raises_when_file_does_not_exist(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"path": "nonexistent.png"},
                last_output=None,
                resource_root=self.resource_root,
            )

    def test_raises_on_path_traversal(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"path": "../etc/passwd"},
                last_output=None,
                resource_root=self.resource_root,
            )

    def test_raises_on_absolute_path_traversal(self):
        with pytest.raises(CommandError):
            self.cmd.execute(
                {"path": "/etc/passwd"},
                last_output=None,
                resource_root=self.resource_root,
            )

    def test_name_attribute(self):
        assert self.cmd.name == "load-image"

    def test_parameters_attribute(self):
        assert "path" in self.cmd.parameters

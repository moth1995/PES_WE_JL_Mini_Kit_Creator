from .base import ImageCommand, source_image, CommandError
from PIL import Image


class CompositeCommand(ImageCommand):
    name = "composite"
    parameters = {"foreground", "background", "mask", "mask-mode"}

    def execute(self, options, *, last_output, resource_root):
        foreground = options.get("foreground", last_output)
        background = options.get("background", last_output)
        mask = options.get("mask", last_output)
        if foreground is None or background is None or mask is None:
            raise CommandError("composite requires foreground, background, and mask, or a previous output")
        mode = options.get("mask-mode", "alpha")
        if mode not in {"alpha", "grayscale"}:
            raise CommandError("composite mask-mode must be alpha or grayscale")
        return Image.composite(foreground, background, mask.convert("L") if mode == "grayscale" else mask)

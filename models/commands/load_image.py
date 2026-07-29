from .base import ImageCommand, resource_path
from PIL import Image


class LoadImageCommand(ImageCommand):
    name = "load-image"
    parameters = {"path"}

    def execute(self, options, *, last_output, resource_root):
        return Image.open(resource_path(resource_root, options.get("path"))).copy()

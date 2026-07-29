from .base import ImageCommand, as_int_tuple
from .base import CommandError
from PIL import Image


class NewImageCommand(ImageCommand):
    name = "new-image"
    parameters = {"mode", "size", "color"}

    def execute(self, options, *, last_output, resource_root):
        mode = options.get("mode")
        if not isinstance(mode, str):
            raise CommandError("new-image mode must be a string")
        return Image.new(mode=mode, size=as_int_tuple(options.get("size"), 2, "new-image size"), color=options.get("color"))

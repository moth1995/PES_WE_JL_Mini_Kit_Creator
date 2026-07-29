from .base import ImageCommand, as_int_tuple, source_image, CommandError


class CropCommand(ImageCommand):
    name = "crop"
    parameters = {"source", "box"}

    def execute(self, options, *, last_output, resource_root):
        left, top, right, bottom = as_int_tuple(options.get("box"), 4, "crop box")
        if right <= left or bottom <= top:
            raise CommandError("crop box must have positive width and height")
        return source_image(options, last_output, self.name).crop((left, top, right, bottom))

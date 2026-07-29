from .base import ImageCommand, source_image, CommandError
from PIL import Image


class FlipCommand(ImageCommand):
    name = "flip"
    parameters = {"source", "direction"}

    def execute(self, options, *, last_output, resource_root):
        operations = {"horizontal": Image.Transpose.FLIP_LEFT_RIGHT, "vertical": Image.Transpose.FLIP_TOP_BOTTOM}
        direction = options.get("direction")
        if direction not in operations:
            raise CommandError("flip direction must be horizontal or vertical")
        return source_image(options, last_output, self.name).transpose(operations[direction])

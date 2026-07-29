from .base import ImageCommand, as_int_tuple, resampling, source_image


class ResizeCommand(ImageCommand):
    name = "resize"
    parameters = {"source", "size", "resample"}

    def execute(self, options, *, last_output, resource_root):
        width, height = as_int_tuple(options.get("size"), 2, "resize size")
        if width <= 0 or height <= 0:
            raise ValueError("resize size must be positive")
        return source_image(options, last_output, self.name).resize((width, height), resampling(options.get("resample")))

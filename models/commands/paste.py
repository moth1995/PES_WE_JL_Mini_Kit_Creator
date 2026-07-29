from .base import ImageCommand, as_int_tuple, source_image


class PasteCommand(ImageCommand):
    name = "paste"
    parameters = {"target", "source", "position", "mask"}

    def execute(self, options, *, last_output, resource_root):
        target = options.get("target", last_output)
        source = options.get("source", last_output)
        if target is None or source is None:
            raise ValueError("paste requires target and source, or a previous command output")
        result = target.copy()
        result.paste(source, as_int_tuple(options.get("position"), 2, "paste position"), mask=options.get("mask"))
        return result

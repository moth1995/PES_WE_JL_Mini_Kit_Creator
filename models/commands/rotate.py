from .base import ImageCommand, resampling, source_image, CommandError


class RotateCommand(ImageCommand):
    name = "rotate"
    parameters = {"source", "angle", "expand", "resample", "fill-color"}

    def execute(self, options, *, last_output, resource_root):
        angle = options.get("angle")
        if isinstance(angle, bool) or not isinstance(angle, (int, float)):
            raise CommandError("rotate angle must be numeric")
        return source_image(options, last_output, self.name).rotate(
            angle,
            resample=resampling(options.get("resample")),
            expand=bool(options.get("expand", False)),
            fillcolor=options.get("fill-color"),
        )

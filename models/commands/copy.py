from .base import ImageCommand


class CopyCommand(ImageCommand):
    name = "copy"
    parameters = {"source"}

    def execute(self, options, *, last_output, resource_root):
        return self._source(options, last_output).copy()

    def _source(self, options, last_output):
        from .base import source_image
        return source_image(options, last_output, self.name)

from .copy import CopyCommand
from .new_image import NewImageCommand
from .load_image import LoadImageCommand
from .crop import CropCommand
from .resize import ResizeCommand
from .rotate import RotateCommand
from .flip import FlipCommand
from .paste import PasteCommand
from .composite import CompositeCommand

COMMANDS = {
    command.name: command()
    for command in (
        CopyCommand,
        NewImageCommand,
        LoadImageCommand,
        CropCommand,
        ResizeCommand,
        RotateCommand,
        FlipCommand,
        PasteCommand,
        CompositeCommand,
    )
}

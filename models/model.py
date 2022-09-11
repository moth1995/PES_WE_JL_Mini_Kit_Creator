from PIL import Image
from .mini_kit import MiniKit
import os
import sys

class Model():

    def check_kit_dimensions(self, kit:Image.Image):
        if kit.size == (512,256):
            return kit
        else:
            return kit.resize((512,256))

    def make_old_style(self, mini_kit:MiniKit, borders:bool, kit_3d_ver:int):
        if kit_3d_ver == 0:
            mini_kit.pes2013_kit()
        base_kit_2d = Image.open("resources/old_style_kit_2d.png")
        mini_kit.rotate_kits(0)
        mini_kit.resize_kits(0)
        mini_kit.make_old_style_mini_kit(base_kit_2d, borders)
        filename = "minikit.png" if borders else "minikit_no_bordes.png"
        mini_kit.mini_kit.save(filename)

    def make_new_style(self, mini_kit:MiniKit, borders:bool, kit_3d_ver:int):
        if kit_3d_ver == 0:
            mini_kit.pes2013_kit()
        base_kit_2d = Image.open("resources/new_style_kit_2d_128x128.png")
        mini_kit.rotate_kits(1)
        mini_kit.resize_kits(1)
        mini_kit.make_new_style_mini_kit(base_kit_2d, borders)
        filename = "minikit_new_style.png" if borders else "minikit_new_style_no_bordes.png"
        mini_kit.mini_kit.save(filename)

    def resource_path(self,relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)
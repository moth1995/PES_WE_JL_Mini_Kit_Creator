from views.view import View
from models.model import Model
from PIL import Image
from models.mini_kit import MiniKit

class Controller():
    def __init__(self, ):
        self.model = Model()
        self.view = View(self)

    @property
    def app_icon(self):
        return self.model.resource_path("resources/pes_indie.ico")

    def main(self):
        self.view.main()
        
    def on_drop(self):
        pa_3d = self.model.check_kit_dimensions(Image.open("test/kit.png"))
        pb_3d = self.model.check_kit_dimensions(Image.open("test/kit_1.png"))
        mini_kit = MiniKit(pa_3d, pb_3d)
        
        self.model.make_old_style(mini_kit, True, 0)
        self.model.make_new_style(mini_kit, True, 0)

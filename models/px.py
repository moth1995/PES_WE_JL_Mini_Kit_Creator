from PIL import Image

class PX():
    def __init__(self, parts_of_kit: "tuple[Image.Image, Image.Image, Image.Image, Image.Image, Image.Image]"):
        self.shirt, self.short, self.socks, self.left_sleeve, self.right_sleeve = parts_of_kit

    def rotate_sleeves_old_style(self):
        self.left_sleeve = self.left_sleeve.rotate(angle=-45, expand=True)
        self.right_sleeve = self.right_sleeve.rotate(angle=-135, expand=True)

    def resize_old_style(self):
        self.shirt = self.shirt.resize((28,38))
        self.short = self.short.resize((25,25))
        self.socks = self.socks.resize((19,33))
        self.left_sleeve = self.left_sleeve.resize((18,18))
        self.right_sleeve = self.right_sleeve.resize((18,18))

    def rotate_sleeves_new_style(self):
        self.left_sleeve = self.left_sleeve.rotate(angle=-90, expand=True)
        self.right_sleeve = self.right_sleeve.rotate(angle=-90, expand=True)

    def resize_new_style(self):
        self.shirt = self.shirt.resize((26,50))
        self.short = self.short.resize((33,26))
        self.socks = self.socks.resize((12,29))
        self.left_sleeve = self.left_sleeve.resize((14,16))
        self.right_sleeve = self.right_sleeve.resize((14,16))


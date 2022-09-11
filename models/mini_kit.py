from PIL import Image
from .px import PX

class MiniKit():
    
    mini_kit = Image.new(mode="RGBA", size=(128, 128))

    def __init__(self, pa:Image.Image, pb:Image.Image):
        self.pa_img = pa
        self.pb_img = pb

    def pes2013_kit(self):
        self.pa = PX(self.crop_kit_pes2013(self.pa_img))
        self.pb = PX(self.crop_kit_pes2013(self.pb_img))

    def rotate_kits(self, style:int):
        if style == 0:
            self.pa.rotate_sleeves_old_style()
            self.pb.rotate_sleeves_old_style()
        if style == 1:
            self.pa.rotate_sleeves_new_style()
            self.pb.rotate_sleeves_new_style()

    def resize_kits(self, style:int):
        if style ==0:
            self.pa.resize_old_style()
            self.pb.resize_old_style()
        if style ==1:
            self.pa.resize_new_style()
            self.pb.resize_new_style()

    def crop_kit_pes2013(self, kit:Image.Image):
        shirt_x = 40
        shirt_y = 0
        shirt_w = 114
        shirt_h = 143

        shirt = kit.crop(
            (
                shirt_x,
                shirt_y,
                shirt_x + shirt_w,
                shirt_y + shirt_h,
            )
        )

        short_x = 22
        short_y = 143
        short_w = 150
        short_h = 113

        short = kit.crop(
            (
                short_x,
                short_y,
                short_x + short_w,
                short_y + short_h
            )
        )

        socks_x = 413
        socks_y = 188
        socks_w = 98
        socks_h = 67
        socks = kit.crop(
            (
                socks_x, 
                socks_y, 
                socks_x + socks_w, 
                socks_y + socks_h,
            )
        )

        sleeves_x = 432
        sleeves_y = 93
        sleeves_w = 80
        sleeves_h = 95
        sleeves = kit.crop(
            (
                sleeves_x, 
                sleeves_y, 
                sleeves_x + sleeves_w, 
                sleeves_y + sleeves_h,
            )
        )
        left_sleeve = sleeves
        right_sleeve = sleeves

        return (shirt, short, socks, left_sleeve, right_sleeve)

    def make_old_style_mini_kit(self, mask:Image.Image, add_borders: bool):
        self.mini_kit.paste(self.pa.left_sleeve, (29,2))
        self.mini_kit.paste(self.pa.right_sleeve, (1,2))
        self.mini_kit.paste(self.pa.shirt, (10,1))
        self.mini_kit.paste(self.pa.short, (4,42))
        self.mini_kit.paste(self.pa.socks, (6,75))

        self.mini_kit.paste(self.pb.left_sleeve, (77,2))
        self.mini_kit.paste(self.pb.right_sleeve, (47,2))
        self.mini_kit.paste(self.pb.shirt, (58,1))
        self.mini_kit.paste(self.pb.short, (36,42))
        self.mini_kit.paste(self.pb.socks, (39,75))

        self.mini_kit = Image.composite(self.mini_kit, mask, mask)
        if add_borders:
            mask_grey_scale = mask.convert("L")
            self.mini_kit = Image.composite(self.mini_kit, mask, mask_grey_scale)

    def make_new_style_mini_kit(self, mask:Image.Image, add_borders: bool):
        self.mini_kit.paste(self.pa.left_sleeve, (12,9))
        self.mini_kit.paste(self.pa.right_sleeve, (39,9))
        self.mini_kit.paste(self.pa.shirt, (20,4))
        self.mini_kit.paste(self.pa.short, (15,54))
        self.mini_kit.paste(self.pa.socks, (39,85)) # left sock
        self.mini_kit.paste(self.pa.socks, (14,85)) # right sock

        self.mini_kit.paste(self.pb.left_sleeve, (76,9))
        self.mini_kit.paste(self.pb.right_sleeve, (103,9))
        self.mini_kit.paste(self.pb.shirt, (84,4))
        self.mini_kit.paste(self.pb.short, (80,54))
        self.mini_kit.paste(self.pb.socks, (103,85)) # left sock
        self.mini_kit.paste(self.pb.socks, (78,85)) # right sock

        self.mini_kit = Image.composite(self.mini_kit, mask, mask)
        if add_borders:
            mask_grey_scale = mask.convert("L")
            self.mini_kit = Image.composite(self.mini_kit, mask, mask_grey_scale)

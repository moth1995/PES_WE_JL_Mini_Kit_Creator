from PIL import Image
from .mini_kit import MiniKit
import os
import sys
from tkinter import filedialog

class Model():

    def check_kit_dimensions(self, kit:Image.Image):
        if kit.size == (512,256):
            return kit
        else:
            return kit.resize((512,256))

    def make_old_style(self, mini_kit:MiniKit, output_dir:str, borders:bool, kit_3d_ver:int):
        if output_dir == "": raise Exception("You must select first the output directory")
        if kit_3d_ver == 0: mini_kit.pes2013_kit()
        elif kit_3d_ver == 1: mini_kit.we10_kit()
        else: raise Exception("Unsuported input version")
        base_kit_2d = Image.open(self.resource_path("resources/old_style_kit_2d.png"))
        mini_kit.rotate_kits(0)
        mini_kit.resize_kits(0)
        mini_kit.make_old_style_mini_kit(base_kit_2d, borders)
        filename = "minikit.png" if borders else "minikit_no_bordes.png"
        
        mini_kit.mini_kit.save(output_dir + "/" + filename)

    def make_new_style(self, mini_kit:MiniKit, output_dir:str, borders:bool, kit_3d_ver:int):
        if output_dir == "": raise Exception("You must select first the output directory")
        if kit_3d_ver == 0: mini_kit.pes2013_kit()
        elif kit_3d_ver == 1: mini_kit.we10_kit()
        else: raise Exception("Unsuported input version")
        base_kit_2d = Image.open(self.resource_path("resources/new_style_kit_2d_128x128.png"))
        mini_kit.rotate_kits(1)
        mini_kit.resize_kits(1)
        mini_kit.make_new_style_mini_kit(base_kit_2d, borders)
        filename = "minikit_new_style.png" if borders else "minikit_new_style_no_bordes.png"
        mini_kit.mini_kit.save(output_dir + "/" + filename)

    def resource_path(self,relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)
    
    def verify_dropped_files(self, dropped_data:tuple):
        if len(dropped_data) == 1 and os.path.isdir(dropped_data[0]): return "Folder"
        elif len(dropped_data) == 2 and os.path.isfile(dropped_data[0]) and os.path.isfile(dropped_data[0]): return "Files"
        else: raise Exception("Unsupported files dropped format")

    def filter_kits(self, folder):
        filtered_kits = []
        filtered_folders = []
        for dirpath,_,filenames in os.walk(folder):
            for f in filenames:
                full_path_fname = str(os.path.abspath(os.path.join(dirpath, f))).lower()
                if full_path_fname.endswith("\\pa\\kit.png") or full_path_fname.endswith("\\pb\\kit.png"):
                    filtered_kits.append(full_path_fname)
        for file in filtered_kits:
            filtered_folders.append(file.split("kit.png")[0][:-4])
        for folder in filtered_folders:
            if filtered_folders.count(folder) != 2:
                print(f"removing {folder}")
                filtered_folders.remove(folder)
        final_filtered_folder = []
        [final_filtered_folder.append(x) for x in filtered_folders if x not in final_filtered_folder]
        return final_filtered_folder
                
    def select_output_dir(self, root):
        return filedialog.askdirectory(parent=root, initialdir=".",title="Please select a directory")
    
    def make_mini_kits(self, pa_3d: Image.Image, pb_3d: Image.Image, mini_kit_style_version:int, output_dir:str, input_ver:int):
            mini_kit = MiniKit(pa_3d, pb_3d)
            if mini_kit_style_version == 0:
                self.make_old_style(mini_kit, output_dir, True, input_ver)
            elif mini_kit_style_version == 1:
                self.make_new_style(mini_kit, output_dir, True, input_ver)
    
    def create_output_folder(self, folder):
        if not os.path.exists(folder):
            os.makedirs(folder)






import os
from tkinter import messagebox
from views.view import View
from models.model import Model
from PIL import Image

class Controller():
    output_dir = ""
    kit_input_supported_versions = [
        "PES 2013",
        "PES 5 / WE 10"
    ]
    mini_kit_output_supported_versions = [
        "Old Style",
        "PES14 Style-Like",
    ]

    def __init__(self, ):
        self.model = Model()
        self.view = View(self)
        # register the entry as a drop target
        self.view.entry_drop.drop_target_register('DND_Files')
        self.view.entry_drop.dnd_bind('<<Drop>>', self.on_drop)
        self.view.input_kit_cmb_ver.current(0)
        self.view.mini_kit_out_ver_cmb.current(0)
        self.view.output_folder_btn.config(command = lambda: self.on_click_on_select_output_directory())
        

    @property
    def app_icon(self):
        return self.model.resource_path("resources/pes_indie.ico")

    def main(self):
        self.view.main()

    def on_click_on_select_output_directory(self):
        self.output_dir = self.model.select_output_dir(self.view)
        
    def on_drop(self, event):
        dropped_data = self.view.tk.splitlist(event.data)
        type_of_dropped_files = self.model.verify_dropped_files(dropped_data)

        kit_3d_input_ver = self.view.input_kit_cmb_ver.current()
        mini_kit_style_version = self.view.mini_kit_out_ver_cmb.current()

        if type_of_dropped_files == "Folder":
            if self.output_dir == "": raise ValueError("You must select first the output directory")
            filtered_folders = self.model.filter_kits(dropped_data[0])
            for folder in filtered_folders:
                pa_3d = self.model.check_kit_dimensions(Image.open(folder + "\\pa\\kit.png"))
                pb_3d = self.model.check_kit_dimensions(Image.open(folder + "\\pb\\kit.png"))
                minikit_output_folder = self.output_dir + "\\" + os.path.basename(os.path.normpath(folder))
                self.model.create_output_folder(minikit_output_folder)
                self.model.make_mini_kits(pa_3d, pb_3d, mini_kit_style_version, minikit_output_folder, kit_3d_input_ver)
            messagebox.showinfo(
                self.view.appname, 
                f"All files converted and saved at {self.output_dir}!"
            )
        elif type_of_dropped_files == "Files":
            pa_3d = self.model.check_kit_dimensions(Image.open(dropped_data[0]))
            pb_3d = self.model.check_kit_dimensions(Image.open(dropped_data[1]))
            self.model.make_mini_kits(pa_3d, pb_3d, mini_kit_style_version, self.output_dir, kit_3d_input_ver)
            messagebox.showinfo(
                self.view.appname, 
                f"All files converted and saved at {self.output_dir}!"
            )







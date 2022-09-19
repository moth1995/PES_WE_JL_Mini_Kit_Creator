from tkinterdnd2 import TkinterDnD
from tkinter import Button, Label, Menu, messagebox, ttk
import traceback

class View(TkinterDnD.Tk):
    def __init__(self, controller):
        super().__init__()
        w = 400 # width for the Tk root
        h = 400 # height for the Tk root
        ws = self.winfo_screenwidth() # width of the screen
        hs = self.winfo_screenheight() # height of the screen
        # calculate x and y coordinates for the Tk root window
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        # set the dimensions of the screen 
        # and where it is placed
        self.geometry('%dx%d+%d+%d' % (w, h, x, y))

        self.controller = controller
        self.appname = "Mini Kit Creator"
        self.version = "1.0.0"
        self.author = "PES Indie Team"
        self.title(f"{self.appname} {self.version} By {self.author}")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.iconbitmap(default=self.controller.app_icon)

        self.entry_drop = Label(
            self, 
            anchor = "center", 
            text = "Drop here", 
            relief = "solid", 
            width = 20,
            height = 10,
        )

        self.entry_drop.grid(
            row = 0, 
            column = 0, 
            sticky = "nwse", 
            padx= 130, 
            pady= 20,
            columnspan= 2,
        )

        self.input_ver_lbl = Label(self, text="Input kit version")
        self.input_ver_lbl.grid(
            row = 1, 
            column = 0, 
            sticky = "nwse", 
            padx= 20, 
        )

        self.input_kit_cmb_ver = ttk.Combobox(
            self, 
            state= "readonly",
            values = self.controller.kit_input_supported_versions,
            width = 20,
        )
        self.input_kit_cmb_ver.grid(
            row = 2, 
            column = 0, 
            sticky = "nwse", 
            padx= 20, 
            pady= 20,
        )

        self.output_ver_lbl = Label(self, text="Output Style")
        self.output_ver_lbl.grid(
            row = 1, 
            column = 1, 
            sticky = "nwse", 
            padx= 20, 
        )

        
        self.mini_kit_out_ver_cmb = ttk.Combobox(
            self, 
            state= "readonly",
            values = self.controller.mini_kit_output_supported_versions,
            width = 20,
        )
        self.mini_kit_out_ver_cmb.grid(
            row = 2, 
            column = 1, 
            sticky = "nwse", 
            padx= 20, 
            pady= 20,

        )

        
        self.output_folder_btn = Button(
            self, 
            text = "Select Output Folder",
            command = None,
            width = 20,
        )
        self.output_folder_btn.grid(
            row = 4, 
            column = 0, 
            sticky = "nwse", 
            padx= 130, 
            pady= 20,
            columnspan= 2,

        )
        
        self.__make_file_menu()


    def __make_file_menu(self):
        self.main_menu=Menu(self.master)
        self.config(menu=self.main_menu)
        self.file_menu = Menu(self.main_menu, tearoff=0)
        self.edit_menu = Menu(self.main_menu, tearoff=0)
        self.help_menu = Menu(self.main_menu, tearoff=0)

        self.main_menu.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open Folder", command=lambda : None)
        self.file_menu.add_command(label="Exit", command= lambda : self.destroy())

        self.main_menu.add_cascade(label="Help", menu=self.help_menu)
        self.help_menu.add_command(label="Manual", command=None)
        self.help_menu.add_command(label="About", command=None)


    def report_callback_exception(self, *args):
        err = traceback.format_exception(*args)
        messagebox.showerror(self.appname + " Error Message", " ".join(err))


    def main(self):
        self.mainloop()


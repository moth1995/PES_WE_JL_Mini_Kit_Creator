from tkinterdnd2 import TkinterDnD

class View(TkinterDnD.Tk):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.appname = 'Mini Kit Creator'
        self.version = '1.0.0'
        self.author = 'PES Indie Team'
        self.title(f"{self.appname} {self.version} By {self.author}")
        #self.resizable(False, False)
        self.attributes("-topmost", True)
        self.iconbitmap(default=self.controller.app_icon)

    def main(self):
        self.mainloop()


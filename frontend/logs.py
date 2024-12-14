from common import *


class GUILogs(ctk.CTkFrame):
    def __init__(self, master, root):
        super().__init__(master)
        self.configure(fg_color=color_bg_br, bg_color="transparent", corner_radius=10)
        self.logs_label = ctk.CTkLabel(self, text="Logs Tab Content Here")
        self.logs_label.pack(pady=5)

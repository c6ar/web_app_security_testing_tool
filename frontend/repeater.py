import customtkinter as ctk


class GUIRepeater(ctk.CTkFrame):
    def __init__(self, master, root):
        super().__init__(master)
        self.configure(fg_color="transparent")
        self.inspect_label = ctk.CTkLabel(self, text="Repeater Tab Content Here")
        self.inspect_label.pack(pady=5)
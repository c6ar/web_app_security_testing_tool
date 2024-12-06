import customtkinter as ctk


class GUILogs(ctk.CTkFrame):
    def __init__(self, master, root):
        super().__init__(master)
        self.configure(fg_color="transparent")
        self.logs_label = ctk.CTkLabel(self, text="Logs Tab Content Here")
        self.logs_label.pack(pady=5)

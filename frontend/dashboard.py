import customtkinter as ctk


class GUIDash(ctk.CTkFrame):
    def __init__(self, master, root):
        super().__init__(master)
        self.configure(fg_color="transparent")
        self.target_title = ctk.CTkLabel(self, text="DASHBOARD PLACEHOLDER.")
        self.intercepting_check = ctk.CTkLabel(self, text=f"Intercept: {root.intercepting}.")
        self.target_title.pack(pady=5)
        self.intercepting_check.pack(pady=5)

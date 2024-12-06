import customtkinter as ctk


class GUIRepeater(ctk.CTkFrame):
    def __init__(self, master, root):
        super().__init__(master)
        self.configure(fg_color="transparent")
        self.inspect_label = ctk.CTkLabel(self, text="Inspecting HTTP requests and responses...")
        self.inspect_label.pack(pady=5)
        self.inspect_button = ctk.CTkButton(self, text="Start Inspection", command=self.inspect)
        self.inspect_button.pack(pady=5)

    def inspect(self):
        self.inspect_label.configure(text="Inspection started...")
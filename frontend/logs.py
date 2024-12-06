import customtkinter as ctk


class GUILogs(ctk.CTkFrame):
    def __init__(self, master, root):
        super().__init__(master)
        self.configure(fg_color="transparent")

        self.logs_label = ctk.CTkLabel(self, text="Displaying logs...")
        self.logs_label.pack(pady=5)
        self.logs_button = ctk.CTkButton(self, text="Show Logs", command=self.show_logs_content)
        self.logs_button.pack(pady=5)

    def show_logs_content(self):
        self.logs_label.pack_forget()
        self.logs_label.configure(text="Logs displayed.")
        self.logs_button.pack(pady=25)
        self.logs_label.pack(pady=5)
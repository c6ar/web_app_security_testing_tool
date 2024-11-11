import tkinter as tk
import customtkinter as ctk


class ResizableApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Resizable Panes Example")
        self.geometry("800x600")

        # Main PanedWindow container
        self.paned_window = tk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill="both", expand=True)

        # Left pane (vertical)
        self.left_pane = ctk.CTkFrame(self.paned_window)
        self.paned_window.add(self.left_pane, stretch="always")

        # Right PanedWindow (vertical orientation)
        self.right_paned_window = tk.PanedWindow(self.paned_window, orient=tk.VERTICAL)
        self.paned_window.add(self.right_paned_window, stretch="always")

        # Top right pane
        self.top_right_pane = ctk.CTkFrame(self.right_paned_window)
        self.right_paned_window.add(self.top_right_pane, stretch="always")

        # Bottom right pane
        self.bottom_right_pane = ctk.CTkFrame(self.right_paned_window)
        self.right_paned_window.add(self.bottom_right_pane, stretch="always")

        # Example content for the panes
        self.left_label = ctk.CTkLabel(self.left_pane, text="Left Pane", anchor="center")
        self.left_label.pack(fill="both", expand=True, padx=10, pady=10)

        self.top_right_label = ctk.CTkLabel(self.top_right_pane, text="Top Right Pane", anchor="center")
        self.top_right_label.pack(fill="both", expand=True, padx=10, pady=10)

        self.bottom_right_label = ctk.CTkLabel(self.bottom_right_pane, text="Bottom Right Pane", anchor="center")
        self.bottom_right_label.pack(fill="both", expand=True, padx=10, pady=10)


if __name__ == "__main__":
    app = ResizableApp()
    app.mainloop()

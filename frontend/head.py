import customtkinter as ctk
from pathlib import Path

color_bg = "#222"
color_bg_br = "#333"
color_acc = "#d68f13"
color_acc2 = "#ffab17"

HOST = '127.0.0.1'  # Ten sam adres IP, co w serwerze
PORT_SERVER = 65432  # Do komunikacji proxy.py -> GUI
PORT_GUI = 65433  # Do komunikacji GUIT -> proxy.py

CURRENT_DIR = f"{Path.cwd()}"
ASSET_DIR = f"{Path.cwd()}\\assets"


class NavButton(ctk.CTkFrame):
    def __init__(self, master, text, command, font):
        super().__init__(master)

        text_width = font.measure(text)
        button_width = text_width + 25

        self.main_button = ctk.CTkButton(self)
        self.main_button.configure(
            width=button_width,
            corner_radius=0,
            fg_color=color_bg,
            bg_color=color_bg,
            hover_color=color_acc,
            text=text,
            command=command,
            font=font)
        self.main_button.pack()

        self.bottom_border = ctk.CTkFrame(self, height=3, width=self.main_button.winfo_reqwidth(), fg_color=color_bg)
        self.bottom_border.pack(side="bottom", fill="x")

        self.selected = False

    def set_selected(self, value):
        self.selected = value
        if self.selected:
            self.main_button.configure(fg_color=color_bg_br)
            self.bottom_border.configure(fg_color=color_acc)
        else:
            self.main_button.configure(fg_color=color_bg)
            self.bottom_border.configure(fg_color=color_bg)

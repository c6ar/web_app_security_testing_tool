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
    def __init__(self, master, text, command, font, background=color_bg, background_selected=color_bg_br):
        super().__init__(master)

        self.bg = background
        self.bg_sel = background_selected

        text_width = font.measure(text)
        button_width = text_width + 25

        self.configure(
            bg_color="transparent",
            fg_color="transparent"
        )

        self.main_button = ctk.CTkButton(self)
        self.main_button.configure(
            border_width=0,
            width=button_width,
            corner_radius=10,
            bg_color=self.bg,
            fg_color=self.bg,
            hover_color=color_acc,
            text=text,
            command=command,
            font=font,
            background_corner_colors=(self.bg,self.bg,self.bg,self.bg)
        )
        self.main_button.pack(padx=3)
        self.selected = False

    def set_selected(self, value):
        self.selected = value
        if self.selected:
            self.main_button.configure(
                fg_color=self.bg_sel,
                background_corner_colors=(self.bg,self.bg,self.bg_sel,self.bg_sel)
            )
        else:
            self.main_button.configure(
                fg_color=self.bg,
                background_corner_colors=(self.bg,self.bg,self.bg,self.bg)
            )

import customtkinter as ctk
from pathlib import Path
from PIL import Image, ImageTk
from backend.global_setup import  *

from PIL import Image, ImageTk
color_bg = "#222"
color_bg_br = "#333"
ctk.set_default_color_theme("dark-blue")
color_acc = ctk.ThemeManager.theme["CTkButton"]["fg_color"][1]
color_acc2 = ctk.ThemeManager.theme["CTkButton"]["hover_color"][1]
color_acc3 = "#d1641b"
color_acc4 = "#924511"

HOST = '127.0.0.1'  # Ten sam adres IP, co w serwerze
PORT_SERVER = 65432  # Do komunikacji proxy.py -> GUI
PORT_GUI = 65433  # Do komunikacji GUIT -> proxy.py

CURRENT_DIR = f"{Path.cwd()}"
ASSET_DIR = f"{Path.cwd()}\\assets"


class NavButton(ctk.CTkFrame):
    def __init__(self, master, text, command, font, background=color_bg, background_selected=color_bg_br, close=False, close_command=None):
        super().__init__(master)

        self.bg = background
        self.bg_sel = background_selected

        text_width = font.measure(text)
        button_width = text_width + 25

        self.configure(
            corner_radius=10,
            bg_color=self.bg,
            fg_color=self.bg,
            background_corner_colors=(self.bg, self.bg, self.bg, self.bg)
        )

        self.main_button = ctk.CTkButton(self)
        self.main_button.configure(
            border_width=0,
            border_spacing=0,
            width=button_width,
            corner_radius=10,
            bg_color="transparent",
            fg_color="transparent",
            hover_color=self.bg_sel,
            text_color_disabled="white",
            text=text,
            command=command,
            font=font
        )
        if close:
            self.configure(
                width=button_width - 10
            )
            self.main_button.configure(
                width=button_width - 25
            )
        self.main_button.pack(side="left", padx=3)

        if close:
            icon_delete = ctk.CTkImage(
                light_image=Image.open(f"{ASSET_DIR}\\icon_close.png"),
                dark_image=Image.open(f"{ASSET_DIR}\\icon_close.png"), size=(10, 10))
            self.close_button = ctk.CTkButton(self)
            self.close_button.configure(
                border_width=0,
                border_spacing=0,
                width=5,
                corner_radius=10,
                bg_color="transparent",
                fg_color="transparent",
                hover=False,
                image=icon_delete,
                text="",
                command=close_command
            )
            self.close_button.pack(side="left")

        self.selected = False

    def set_selected(self, value):
        self.selected = value
        if self.selected:
            self.configure(
                fg_color=self.bg_sel,
                background_corner_colors=(self.bg, self.bg, self.bg_sel, self.bg_sel)
            )
            self.main_button.configure(
                state="disabled"
            )
            if hasattr(self,"close_button"):
                self.close_button.configure(
                    background_corner_colors=(self.bg_sel, self.bg, self.bg_sel, self.bg_sel)
                )
        else:
            self.configure(
                fg_color=self.bg,
                background_corner_colors=(self.bg, self.bg, self.bg, self.bg)
            )
            self.main_button.configure(
                state="normal"
            )
            if hasattr(self,"close_button"):
                self.close_button.configure(
                    background_corner_colors=(self.bg, self.bg, self.bg, self.bg)
                )


class HeaderTitle(ctk.CTkLabel):

    def __init__(self, master, text):
        super().__init__(
            master,
            text=text,
            font=ctk.CTkFont(family="Calibri", size=24, weight="bold"),
            anchor="w",
            padx=10,
            pady=10,
            height=20,
            fg_color="transparent",
            bg_color="transparent",
            corner_radius=0
        )
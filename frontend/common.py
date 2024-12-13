import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from pathlib import Path
import pyperclip
from collections.abc import Iterable
import ctypes
import time
from PIL import Image, ImageTk
from backend.global_setup import *

# TODO Global variables to be moved to common.conf file once settings implemented
color_bg = "#222"
color_bg_br = "#333"
ctk.set_default_color_theme("dark-blue")
color_acc = ctk.ThemeManager.theme["CTkButton"]["fg_color"][1]
color_acc2 = ctk.ThemeManager.theme["CTkButton"]["hover_color"][1]
color_acc3 = "#d1641b"
color_acc4 = "#924511"

CURRENT_DIR = f"{Path.cwd()}"
ASSET_DIR = f"{Path.cwd()}\\assets"

icon_toggle_on = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_toggle_on.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_toggle_on.png"), size=(20, 20))
icon_toggle_off = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_toggle_off.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_toggle_off.png"), size=(20, 20))
icon_arrow_up = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_arrow_up.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_arrow_up.png"), size=(20, 20))
icon_arrow_down = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_arrow_down.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_arrow_down.png"), size=(20, 20))
icon_random = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_random.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_random.png"), size=(20, 20))
icon_browser = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_browser.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_browser.png"), size=(20, 20))
icon_delete = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_delete.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_delete.png"), size=(20, 20))
icon_settings = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_settings.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_settings.png"), size=(20, 20))
icon_add = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_add.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_add.png"), size=(20, 20))
icon_info = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_info.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_info.png"), size=(20, 20))
icon_attack = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_attack.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_attack.png"), size=(20, 20))


class ActionButton(ctk.CTkButton):
    # TODO FRONTEND: Stop flickering!
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        if "font" not in kwargs:
            kwargs['font'] = ctk.CTkFont(family="Calibri", size=14)
            self.configure(font=kwargs['font'])
        if "corner_radius" not in kwargs:
            self.configure(corner_radius=32)
        text_width = kwargs["font"].measure(kwargs["text"])
        self.button_width = text_width + 20 + 25
        if self.button_width < 100:
            self.button_width = 100
        self.configure(width=self.button_width)


class NavButton(ctk.CTkFrame):
    # TODO FRONTEND: Stop flickering!
    def __init__(self, master, text, command, icon=None, compound="left", font=None, background=color_bg, background_selected=color_bg_br):
        super().__init__(master)

        self.bg = background
        self.bg_sel = background_selected

        if font is None:
            font = ctk.CTkFont(family="Calibri", size=15, weight="bold")

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
        if icon is not None:
            icon.configure(size=(15,15))
            self.main_button.configure(
                image = icon,
                compound = compound
            )

        self.main_button.pack(side="left", padx=3)
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
        else:
            self.configure(
                fg_color=self.bg,
                background_corner_colors=(self.bg, self.bg, self.bg, self.bg)
            )
            self.main_button.configure(
                state="normal"
            )


class HeaderTitle(ctk.CTkLabel):

    def __init__(self, master, text, size=24, padx=10, pady=10, height=20):
        super().__init__(
            master,
            text=text,
            font=ctk.CTkFont(family="Calibri", size=size, weight="bold"),
            anchor="w",
            padx=padx,
            pady=pady,
            height=height,
            fg_color="transparent",
            bg_color="transparent",
            corner_radius=0
        )


class ConfirmDialog(ctk.CTkToplevel):

    def __init__(self,
                 master,
                 prompt="Are you sure you want to continue?",
                 action1="Yes", command1=None,
                 action2=None, command2=None,
                 action3=None, command3=None):
        super().__init__(master)
        self.title("Confirm")
        self.geometry("300x100")
        self.attributes("-topmost", True)

        label = ctk.CTkLabel(self, text=prompt, wraplength=250)
        label.pack(pady=(10, 5), padx=10)

        yes_button = ctk.CTkButton(self, text=action1, command=command1, corner_radius=32)
        yes_button.pack(side="left", fill=tk.X, padx=10, pady=(5, 10), anchor="e")

        if action2 is not None:
            no_button = ctk.CTkButton(self, text=action2, command=command2, corner_radius=32)
            no_button.pack(side="left", fill=tk.X, padx=10, pady=(5, 10), anchor="w")

        if action3 is not None:
            no_button = ctk.CTkButton(self, text=action3, command=command3, corner_radius=32)
            no_button.pack(side="left", fill=tk.X, padx=10, pady=(5, 10), anchor="w")


class TextBox(ctk.CTkTextbox):
    """
    TextBox based on customtkinter's CTkTextbox with monoscape font and custom insert and get text methods.

    Args:
        master (CTkBaseClass)
        root (CTkBaseClass)
        text (str)
    """

    def __init__(self, master, root, text=""):
        super().__init__(master)
        self.root = root
        self.monoscape_font = ctk.CTkFont(family="Courier New", size=14, weight="normal")
        self.monoscape_font_italic = ctk.CTkFont(family="Courier New", size=14, weight="normal", slant="italic")
        self.configure(wrap="none", font=self.monoscape_font, state="normal", padx=5, pady=5)

        self.insert_text(text)

    def insert_text(self, text):
        """
        Inserting text into the TextBox by completely replacing it.

        Args:
            text (str): Text to be inserted into TextBox.
        """
        self.delete("0.0", "end")
        self.insert("1.0", text)

    def get_text(self):
        """
        Retrieving the current text content from the entire TextBox. With method .stip() applied on it.

        Returns:
            str: content from the TextBox stripped from leading and trailing whitespace.
        """
        return self.get("1.0", "end").strip()  # Use `self.get` directly.

class ItemList(ttk.Treeview):
    """
    Request List class
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.popup_menu = tk.Menu(self, tearoff=0)
        self.bind("<Button-3>", self.popup)

        treestyle = ttk.Style()
        treestyle.theme_use('default')
        treestyle.configure("Treeview", background=color_bg, foreground="white", fieldbackground=color_bg,
                            borderwidth=0)
        treestyle.configure("Treeview.Heading", background=color_bg, foreground="white", borderwidth=0)
        treestyle.map('Treeview', background=[('selected', color_acc)], foreground=[('selected', 'white')])
        treestyle.map("Treeview.Heading", background=[('active', color_bg)])

    def popup(self, event):
        """
            Show right-click menu.
        """
        try:
            self.popup_menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.popup_menu.grab_release()

    def select_all(self):
        """
            Select all items in the list
        """
        for item in self.get_children():
            self.selection_add(item)

    def delete_selected(self):
        """
            Delete a selected items from the list, select the last item in the list afterward.
        """
        for item in self.selection():
            self.delete(item)

        if len(self.get_children()) > 0 and len(self.selection()) == 0:
            self.selection_add(self.get_children()[-1])

    def delete_all(self):
        """
            Delete all items in the list
        """
        for item in self.get_children():
            self.delete(item)

    def copy_value(self, index=0):
        """
            Copies values at the given indexes of the last selected item in selection.
        """
        if len(self.selection()) > 0:
            selected_item = self.selection()[-1]
            content = ""
            if isinstance(index, Iterable):
                for i in index:
                    content += self.item(selected_item)['values'][i] + "\n"
            elif isinstance(index, int):
                content = self.item(selected_item)['values'][index]
            # print(f'DEBUG/FRONTEND/PROXY: selected_item = {selected_item}\n\nits values = {self.item(selected_item)['values']}')
            # print(f"DEBUG/FRONTEND/PROXY: Copied {content}")
            pyperclip.copy(content.strip())
#
# Loading moduels and libraries
#
# noinspection PyUnresolvedReferences
from backend.global_setup import *
# noinspection PyUnresolvedReferences
from backend.Request import *
from collections.abc import Iterable
# noinspection PyUnresolvedReferences
import ctypes
import customtkinter as ctk
# noinspection PyUnresolvedReferences
from customtkinter import ThemeManager, AppearanceModeTracker
# noinspection PyUnresolvedReferences
from datetime import datetime
# noinspection PyUnresolvedReferences
from flask import request
# noinspection PyUnresolvedReferences
from http import HTTPStatus
# noinspection PyUnresolvedReferences
from idlelib.rpc import response_queue
# noinspection PyUnresolvedReferences
import json
# noinspection PyUnresolvedReferences
from operator import truediv
# noinspection PyUnresolvedReferences
import os
from pathlib import Path
# noinspection PyUnresolvedReferences
import pickle
# noinspection PyUnresolvedReferences
from PIL import Image, ImageTk
import pyperclip
# noinspection PyUnresolvedReferences
import random
# noinspection PyUnresolvedReferences
import re
# noinspection PyUnresolvedReferences
import socket
# noinspection PyUnresolvedReferences
import subprocess
# noinspection PyUnresolvedReferences
import threading
# noinspection PyUnresolvedReferences
import time
import tkinter as tk
from tkinter import ttk
# noinspection PyUnresolvedReferences
from tkinter import filedialog
# noinspection PyUnresolvedReferences
from utils.request_methods import *
# noinspection PyUnresolvedReferences
from utils.get_domain import *
import tkinterweb

#
# Global settings and variables
#
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")
if ctk.get_appearance_mode() == "Light":
    color_text = "#000"
    color_text_br = "#333"
    color_text_warn = "#924511"
    color_bg = "#dcdcdc"
    color_bg_br = "#eee"
else:
    color_text = "#eee"
    color_text_br = "#ccc"
    color_text_warn = "#d1641b"
    color_bg = "#222"
    color_bg_br = "#333"
ctk.set_default_color_theme("dark-blue")
color_acc = ctk.ThemeManager.theme["CTkButton"]["fg_color"][1]
color_acc2 = ctk.ThemeManager.theme["CTkButton"]["hover_color"][1]
color_acc3 = "#d1641b"
color_acc4 = "#924511"
color_green = "#228600"
color_green_dk = "#186000"
color_red = "#c81800"
color_red_dk = "#911100"

CURRENT_DIR = f"{Path.cwd()}"
ASSET_DIR = f"{Path.cwd()}\\assets"

#
# Icon and image assets loading
#
icon_proxy = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_proxy_light.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_proxy.png"), size=(20, 20))
icon_intercept = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_traffic_light.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_traffic.png"), size=(60, 60))
icon_intruder = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_intruder_light.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_intruder.png"), size=(20, 20))
icon_repeater = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_repeater_light.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_repeater.png"), size=(20, 20))
icon_logs = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_logs_light.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_logs.png"), size=(20, 20))
icon_settings = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_settings_light.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_settings.png"), size=(20, 20))
icon_info = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_info_light.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_info.png"), size=(20, 20))
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
icon_arrow_left = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_arrow_left.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_arrow_left.png"), size=(20, 20))
icon_arrow_right = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_arrow_right.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_arrow_right.png"), size=(20, 20))
icon_random = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_random.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_random.png"), size=(20, 20))
icon_browser = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_browser.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_browser.png"), size=(20, 20))
icon_delete = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_delete.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_delete.png"), size=(20, 20))
icon_load_file = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_load_file.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_load_file.png"), size=(20, 20))
icon_add = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_add.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_add.png"), size=(20, 20))
icon_attack = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_attack.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_attack.png"), size=(20, 20))
icon_reload = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_reload.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_reload.png"), size=(20, 20))
intercept_off_image = ctk.CTkImage(light_image=Image.open(f"{ASSET_DIR}\\intercept_off_light.png"),
                                   dark_image=Image.open(f"{ASSET_DIR}\\intercept_off.png"),
                                   size=(87, 129))
intercept_on_image = ctk.CTkImage(light_image=Image.open(f"{ASSET_DIR}\\intercept_on_light.png"),
                                  dark_image=Image.open(f"{ASSET_DIR}\\intercept_on.png"), size=(87, 129))

# TODO FRONTEND P3: Add confirm dialog to close the app with data getting lost.
#  - Option to disable the dialog in the config.
# TODO FRONTEND P3: Add translation support only for locales: EN and PL.
#
# Common functions
#
def load_config():
    # TODO OTHER P2: Actual implmentation of config logic in the app
    default_config = {
        "theme": "system",
        "lang": "en",
        "proxy_host_address": "127.0.0.1",
        "proxy_port": 8082,
        "BACK_FRONT_HISTORYREQUESTS_PORT": 65432,
        "BACK_FRONT_SCOPEREQUESTS_PORT": 65433,
        "FRONT_BACK_DROPREQUEST_PORT": 65434,
        "FRONT_BACK_SCOPEUPDATE_PORT": 65430,
        "FRONT_BACK_FORWARDBUTTON_PORT": 65436,
        "FRONT_BACK_INTERCEPTBUTTON_PORT": 65437,
        "REPEATER_BACK_SENDHTTPMESSAGE_PORT": 65438,
        "FRONT_BACK_SENDTOREPEATER_PORT": 65439,
        "BACK_REPEATER_FLOWSEND_PORT": 65440,
        "BACK_REPEATER_RESPONSESEND_PORT": 65441,
        "debug_mode": False,
        "proxy_console": False
    }
    config = default_config.copy()
    try:
        with open("app.conf", "r") as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    if "#" in value:
                        value, _ = value.split("#", 1)
                    value = value.strip().lower()
                    key = key.strip().lower()

                    if key.endswith("port"):
                        try:
                            value = int(value)
                        except ValueError:
                            print("CONFIG ERROR: Incorrect value given, where int expected.")
                            continue

                    if key in ("debug_mode", "proxy_console"):
                        if value not in (1, 0, "1", "0", "true", "false"):
                            print("CONFIG ERROR: Incorrect value given, where bool expected (false, true, 0 or 1).")
                            continue

                    if value in (1, "1", "true"):
                        value = True
                    if value in (0, "0", "false"):
                        value = False

                    config[key] = value
    except FileNotFoundError:
        print("CONFIG ERROR: App config file could not be open. Default settings have been loaded.")
    return config


RUNNING_CONFIG = load_config()
if RUNNING_CONFIG["debug_mode"]:
    print("Debug mode on.")
    print("Running config")
    for key, value in RUNNING_CONFIG.items():
        print(f"\t{key}: {value}")


def save_config(config):
    try:
        with open("app.conf", "r") as file:
            lines = file.readlines()

        updated_lines = []
        keys_found = set()
        for line in lines:
            if line.strip() and not line.strip().startswith("#"):
                key, value = line.split("=", 1)
                key = key.strip()
                if key in config:
                    updated_lines.append(f"{key} = {config[key]}\n")
                    keys_found.add(key)
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)

        for key, value in config.items():
            if key not in keys_found:
                updated_lines.append(f"{key} = {value}\n")

        with open("app.conf", "w") as file:
            file.writelines(updated_lines)
            load_config()
    except Exception as e:
        print(f"Error during saving a config: {e}")


def center_window(root_window, window, width, height):
    """
    Centers TopLevel window relatively to its parent.
    """
    parent_x = root_window.winfo_x()
    parent_y = root_window.winfo_y()
    parent_width = root_window.winfo_width()
    parent_height = root_window.winfo_height()

    position_right = parent_x + int(parent_width / 2 - width / 2)
    position_down = parent_y + int(parent_height / 2 - height / 2)

    window.geometry(f"{width}x{height}+{position_right}+{position_down}")


class ActionButton(ctk.CTkButton):
    """
    A preset action button based on CTkButton.
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        if "corner_radius" not in kwargs:
            self.configure(corner_radius=10)
        if "width" not in kwargs:
            self.configure(width=120)

    def toggle_state(self, state="normal"):
        self.configure(state=state)


class NavButton(ctk.CTkFrame):
    """
    A preset tab navigation button based on CTkButton.
    """
    def __init__(self, master, text, command, icon=None, compound="left", font=None, background=color_bg, background_selected=color_bg_br):
        super().__init__(master)

        self.bg = background
        self.bg_sel = background_selected

        if font is None:
            font = ctk.CTkFont(family="Calibri", size=15, weight="bold")

        text_width = font.measure(text)
        button_width = text_width + 25

        self.configure(
            border_width=0,
            corner_radius=10,
            fg_color=self.bg,
            bg_color="transparent",
            background_corner_colors=(self.bg, self.bg, self.bg, self.bg)
        )

        self.main_button = ctk.CTkButton(self)
        self.main_button.configure(
            border_width=0,
            border_spacing=0,
            width=button_width,
            corner_radius=10,
            text_color=color_text,
            bg_color="transparent",
            fg_color="transparent",
            hover_color=self.bg_sel,
            text_color_disabled=color_text,
            text=text,
            command=command,
            font=font
        )
        if icon is not None:
            try:
                icon.configure(size=(15, 15))
            except Exception as e:
                print(e)
            self.main_button.configure(
                image=icon,
                compound=compound
            )

        self.main_button.pack(side="left", padx=3, pady=(1, 5))
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
    """
    A preset title for section / module headers.
    """
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
            corner_radius=10
        )


class ConfirmDialog(ctk.CTkToplevel):
    """
    A custom Confirm dialog class based on customtkinter's Top Level widget.
    """
    def __init__(self,
                 master, root,
                 prompt="Are you sure you want to continue?", title="Confirm",
                 action1="Yes", command1=None,
                 action2=None, command2=None,
                 action3=None, command3=None):
        super().__init__(master)
        self.title(title)
        self.geometry("300x100")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        center_window(root, self, 300, 100)

        # TODO FRONTEND: Add Enter, Space to run command1 and Escape to destroy the window.
        label = ctk.CTkLabel(self, text=prompt, wraplength=250)
        label.pack(pady=(10, 5), padx=10)

        yes_button = ctk.CTkButton(self, text=action1, command=command1, corner_radius=32)

        if action2 is not None:
            yes_button.pack(side="left", fill=tk.X, padx=10, pady=(5, 10), anchor="e")
            a_button2 = ctk.CTkButton(self, text=action2, command=command2, corner_radius=32)
            if action3 is not None:
                a_button2.pack(side="left", fill=tk.X, padx=10, pady=(5, 10), anchor="w")
                a_button3 = ctk.CTkButton(self, text=action3, command=command3, corner_radius=32)
                a_button3.pack(side="right", fill=tk.X, padx=10, pady=(5, 10), anchor="w")
            else:
                a_button2.pack(side="right", fill=tk.X, padx=10, pady=(5, 10), anchor="w")
        else:
            yes_button.pack(side="top", fill=tk.X, padx=10, pady=(5, 10), anchor="e")


class TextBox(ctk.CTkTextbox):
    """
    Custom TextBox class based on customtkinter's CTkTextbox with monoscape font and custom insert and get text methods.

    Args:
        master (CTkBaseClass)
        text (str)
    """
    def __init__(self, master, text="", **kwargs):
        super().__init__(master, **kwargs)
        self.monoscape_font = ctk.CTkFont(family="Courier New", size=14, weight="normal")
        self.monoscape_font_italic = ctk.CTkFont(family="Courier New", size=14, weight="normal", slant="italic")
        self.configure(wrap="none", font=self.monoscape_font, state="normal", padx=5, pady=5, fg_color=color_bg_br, text_color=color_text)

        self.popup_menu = tk.Menu(self, tearoff=0)
        self.bind("<Button-3>", self.popup)

        self.insert_text(text)

    def popup(self, event):
        """
            Show right-click menu.
        """
        try:
            self.popup_menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.popup_menu.grab_release()

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
    Custom Item List class
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.popup_menu = tk.Menu(self, tearoff=0)
        self.bind("<Button-3>", self.popup)

        treestyle = ttk.Style()
        treestyle.theme_use('default')
        treestyle.configure("Treeview", background=color_bg, foreground=color_text, fieldbackground=color_bg,
                            borderwidth=0, highlightthickness=0, bd=0)
        treestyle.configure("Treeview.Heading", background=color_bg, foreground=color_text, borderwidth=0)
        treestyle.map('Treeview', background=[('selected', color_acc)], foreground=[('selected', 'white')])
        treestyle.map("Treeview.Heading", background=[('active', color_bg_br)])

        treestyle.configure("Treeview2.Treeview", background=color_bg_br, foreground=color_text, fieldbackground=color_bg_br,
                            borderwidth=0, highlightthickness=0, bd=0)
        treestyle.configure("Treeview2.Treeview.Heading", background=color_bg_br, foreground=color_text, borderwidth=0)
        treestyle.map('Treeview2.Treeview', background=[('selected', color_acc)], foreground=[('selected', 'white')])
        treestyle.map("Treeview2.Treeview.Heading", background=[('active', color_bg_br)])

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
            print(f"deleted {item}")

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

class TextEntry(ctk.CTkEntry):
    """
    Custom TextEntry class
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.configure(border_width=0,
                       text_color=color_text,
                       fg_color=color_bg_br,
                       bg_color="transparent")


class Label(ctk.CTkLabel):
    """
    Custom Label class
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.configure(corner_radius=10,
                       text_color=color_text,
                       fg_color="transparent",
                       bg_color="transparent")

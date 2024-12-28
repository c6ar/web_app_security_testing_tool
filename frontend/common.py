# ================================================
# Imports of common modules and libraries
# ================================================
# noinspection PyUnresolvedReferences
from backend.Request import *
# noinspection PyUnresolvedReferences
from collections.abc import Iterable
# noinspection PyUnresolvedReferences
import ctypes
# noinspection PyUnresolvedReferences
import customtkinter as ctk
# noinspection PyUnresolvedReferences
from customtkinter import ThemeManager, AppearanceModeTracker
# noinspection PyUnresolvedReferences
from datetime import datetime
# noinspection PyUnresolvedReferences
from flask import request
# noinspection PyUnresolvedReferences
from http.server import HTTPServer, SimpleHTTPRequestHandler
# noinspection PyUnresolvedReferences
from idlelib.rpc import response_queue
# noinspection PyUnresolvedReferences
import json
# noinspection PyUnresolvedReferences
from mitmproxy.http import Response
# noinspection PyUnresolvedReferences
from operator import truediv
# noinspection PyUnresolvedReferences
import os
# noinspection PyUnresolvedReferences
from pathlib import Path
# noinspection PyUnresolvedReferences
import pickle
# noinspection PyUnresolvedReferences
from PIL import Image, ImageTk
# noinspection PyUnresolvedReferences
import pyperclip
# noinspection PyUnresolvedReferences
import queue
# noinspection PyUnresolvedReferences
import random
# noinspection PyUnresolvedReferences
import re
# noinspection PyUnresolvedReferences
import socket
# noinspection PyUnresolvedReferences
import subprocess
# noinspection PyUnresolvedReferences
import sys
# noinspection PyUnresolvedReferences
import threading
# noinspection PyUnresolvedReferences
from threading import Thread, Event
# noinspection PyUnresolvedReferences
import time
# noinspection PyUnresolvedReferences
import tkinter as tk
# noinspection PyUnresolvedReferences
from tkinter import ttk
# noinspection PyUnresolvedReferences
from tkinter import filedialog
# noinspection PyUnresolvedReferences
from typing import Dict, Union
# noinspection PyUnresolvedReferences
from utils.request_methods import *
# noinspection PyUnresolvedReferences
import tkinterweb

from config import RUNNING_CONFIG

# ================================================
# Global variables
# ================================================
CURRENT_DIR = f"{Path.cwd()}"
ASSET_DIR = f"{Path.cwd()}\\assets"
ctk.set_appearance_mode(RUNNING_CONFIG["theme"])
ctk.set_default_color_theme("dark-blue")
if ctk.get_appearance_mode() == "Light":
    color_text = "#111"
    color_text_br = "#333"
    color_text_warn = "#924511"
    color_bg = "#ddd"
    color_bg_br = "#eee"
else:
    color_text = "#eee"
    color_text_br = "#ccc"
    color_text_warn = "#d1641b"
    color_bg = "#222"
    color_bg_br = "#333"
color_acc = ctk.ThemeManager.theme["CTkButton"]["fg_color"][1]
color_acc2 = ctk.ThemeManager.theme["CTkButton"]["hover_color"][1]
color_acc3 = "#d1641b"
color_acc4 = "#924511"
color_green = "#228600"
color_green_dk = "#186000"
color_red = "#c81800"
color_red_dk = "#911100"
color_highlight = "#72f24b"
color_highlight_bg = "#9e0b69"
today = datetime.now().strftime("%Y-%m-%d")

# ================================================
# Icon and image assets loading
# ================================================
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
icon_start = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_start.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_start.png"), size=(20, 20))
icon_pause = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_pause.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_pause.png"), size=(20, 20))
icon_abort = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_abort.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_abort.png"), size=(20, 20))
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
    light_image=Image.open(f"{ASSET_DIR}\\icon_add_light.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_add.png"), size=(20, 20))
icon_attack = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_attack.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_attack.png"), size=(20, 20))
icon_folder = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_folder.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_folder.png"), size=(20, 20))
icon_reload = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_reload.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_reload.png"), size=(20, 20))

big_icon_info = ctk.CTkImage(
    light_image=Image.open(f"{ASSET_DIR}\\icon_info_light.png"),
    dark_image=Image.open(f"{ASSET_DIR}\\icon_info.png"), size=(30, 30))

intercept_off_image = ctk.CTkImage(light_image=Image.open(f"{ASSET_DIR}\\intercept_off_light.png"),
                                   dark_image=Image.open(f"{ASSET_DIR}\\intercept_off.png"),
                                   size=(87, 129))
intercept_on_image = ctk.CTkImage(light_image=Image.open(f"{ASSET_DIR}\\intercept_on_light.png"),
                                  dark_image=Image.open(f"{ASSET_DIR}\\intercept_on.png"), size=(87, 129))


# ================================================
# Common functions
# ================================================
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


def dprint(*args):
    """
    Prints a message to the console if debug mode is enabled in the config.
    """
    if RUNNING_CONFIG["debug_mode"]:
        print(*args)


def show_response_view(gui, hostname=None, html_content=None, url=None):
    """
    Opens a separate CTk window to display the response HTML content.
    """
    response_view = ctk.CTk()
    width = int(gui.winfo_width() * 0.9)
    height = int(gui.winfo_height() * 0.9)
    response_view.geometry(f"{width}x{height}")
    response_view.focus_set()
    response_view.iconbitmap(f"{ASSET_DIR}\\wastt.ico")
    center_window(gui, response_view, width, height)
    response_view.title("WASTT")

    response_webview = tkinterweb.HtmlFrame(response_view, messages_enabled=False)

    if html_content is not None and len(html_content) > 0:
        html_content = html_content.replace("src=\"/", f"src=\"{hostname}/")
        html_content = html_content.replace("href=\"/", f"href=\"{hostname}/")
        response_webview.load_html(html_content)
        response_webview.current_url = hostname

    elif url is not None and len(url) > 0:
        response_webview.load_url(url)

    response_webview.pack(pady=0, padx=0, fill="both", expand=True)
    response_view.mainloop()


# ================================================
# Common classes
# ================================================
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


class InfoButton(ActionButton):
    """
    A preset info button based on ActionButton.
    """
    def __init__(self, parent, gui, link, fg_color=color_bg, hover_color=color_bg, *args, **kwargs):
        super().__init__(
            parent,
            text="",
            image=big_icon_info,
            width=20,
            fg_color=fg_color,
            hover_color=hover_color,
            command=lambda: show_response_view(gui, url=link),
            *args,
            **kwargs,
        )


class NavButton(ctk.CTkFrame):
    """
    A preset tab navigation button based on CTkButton.
    """

    def __init__(self, master, text, command, icon=None, compound="left", font=None, background=color_bg,
                 background_selected=color_bg_br):
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

    def select(self, val=True):
        self.selected = val
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
                 action3=None, command3=None,
                 width=300, height=100):
        super().__init__(master)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        self.transient(master)
        self.attributes("-topmost", True)
        self.after(250, self.iconbitmap, f"{ASSET_DIR}\\wastt.ico", "")
        center_window(root, self, width, height)

        label = ctk.CTkLabel(self, text=prompt, wraplength=(width - 20))
        label.grid(column=0, row=0, pady=(10, 5), padx=10, sticky=tk.NSEW)

        buttons = ctk.CTkFrame(self, fg_color="transparent", bg_color="transparent")
        buttons.grid(column=0, row=1, pady=(0, 10), padx=10, sticky=tk.NSEW)

        button1 = ctk.CTkButton(buttons, text=action1, command=command1, corner_radius=32)
        button1.grid(column=0, row=0, padx=10, pady=(5, 10))

        buttons.grid_columnconfigure(0, weight=1)
        buttons.grid_rowconfigure(0, weight=1)

        if action2 is not None:
            button2 = ctk.CTkButton(buttons, text=action2, command=command2, corner_radius=32)
            button2.grid(column=1, row=0, padx=10, pady=(5, 10))
            buttons.grid_columnconfigure(1, weight=1)

        if action3 is not None:
            button3 = ctk.CTkButton(buttons, text=action3, command=command3, corner_radius=32)
            button3.grid(column=2, row=0, padx=10, pady=(5, 10))
            buttons.grid_columnconfigure(2, weight=1)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.bind("<Return>", lambda event: self.run_command(command1))
        self.bind("<space>", lambda event: self.run_command(command1))
        self.bind("<Escape>", lambda event: self.destroy())

    def run_command(self, command):
        if command:
            command()
        self.destroy()


class ErrorDialog(ConfirmDialog):
    """
    ConfirmDialog sub class for error message display.
    """
    def __init__(self, master, root, prompt="Error", title="Error!"):
        super().__init__(
            master=master,
            root=root,
            prompt=prompt,
            title=title,
            action1="OK",
            command1=lambda: self.destroy()
        )


class TextBox(ctk.CTkTextbox):
    """
    Custom CTkTextbox class based on customtkinter's CTkTextbox with monoscape font and custom insert and get text methods.

    Args:
        master (CTkBaseClass)
        text (str)
    """

    def __init__(self, master, text="", **kwargs):
        super().__init__(master, **kwargs)
        self.monoscape_font = ctk.CTkFont(family="Courier New", size=14, weight="normal")
        self.monoscape_font_italic = ctk.CTkFont(family="Courier New", size=14, weight="normal", slant="italic")
        self.configure(wrap="none", font=self.monoscape_font, state="normal", padx=5, pady=5, fg_color=color_bg_br,
                       text_color=color_text)

        self.popup_menu = tk.Menu(self, tearoff=0)
        self.bind("<Button-3>", self.popup)
        self.popup_menu.add_command(
            label="Select all",
            command=self.select_all_text
        )
        self.popup_menu.add_command(
            label="Copy",
            command=self.copy_text
        )
        self.popup_menu.add_command(
            label="Copy",
            command=lambda: self.copy_text(cut=True)
        )
        self.popup_menu.add_command(
            label="Paste",
            command=self.paste_text
        )
        self.popup_menu.add_command(
            label="Clear selected",
            command=self.clear_selected_text
        )
        self.popup_menu.add_command(
            label="Clear all",
            command=self.clear_all_text
        )

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
        self.delete("0.0", tk.END)
        self.insert("1.0", text)

    def get_text(self):
        """
        Retrieving the current text content from the entire TextBox. With method .stip() applied on it.

        Returns:
            str: content from the TextBox stripped from leading and trailing whitespace.
        """
        return self.get("1.0", "end").strip()  # Use `self.get` directly.

    def select_all_text(self):
        self.tag_add(tk.SEL, "1.0", tk.END)
        self.mark_set(tk.INSERT, "1.0")
        self.see(tk.INSERT)

    def copy_text(self, cut=False):
        try:
            start_index, end_index = self.tag_ranges('sel')
            selected_text = self.get(start_index, end_index)
            if cut:
                self.delete(start_index, end_index)
        except ValueError:
            selected_text = self.get("1.0", tk.END + "-1c")
            if cut:
                self.delete("1.0", tk.END)

        pyperclip.copy(selected_text)

    def paste_text(self):
        clipboard_text = pyperclip.paste()
        try:
            start_index, end_index = self.tag_ranges(tk.SEL)
            self.delete(start_index, end_index)
            self.insert(start_index, clipboard_text)
        except ValueError:
            try:
                cursor_index = self.index(tk.INSERT)
                self.insert(cursor_index, clipboard_text)
            except (ValueError, tk.TclError):
                self.insert(tk.END, clipboard_text)

    def clear_selected_text(self):
        try:
            start_index, end_index = self.tag_ranges(tk.SEL)
            self.delete(start_index, end_index)
        except (ValueError, tk.TclError):
            pass

    def clear_all_text(self):
        self.delete("0.0", tk.END)


class ItemList(ttk.Treeview):
    """
    Custom TkTreeview class expanded with built-in pop method and custom methods to manipulate items.
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

        treestyle.configure("Treeview2.Treeview", background=color_bg_br, foreground=color_text,
                            fieldbackground=color_bg_br,
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
            dprint(f"DEBUG/FRONTEND: selected_item = {selected_item}\n\nits values = {self.item(selected_item)['values']}")
            dprint(f"DEBUG/FRONTEND: Copied {content}")
            pyperclip.copy(content.strip())


class TextEntry(ctk.CTkEntry):
    """
    Custom CTkEntry class with bright background.
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.configure(border_width=0,
                       text_color=color_text,
                       fg_color=color_bg_br,
                       bg_color="transparent")


class Label(ctk.CTkLabel):
    """
    Custom CTkLabel class with transparent background.
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.configure(corner_radius=10,
                       text_color=color_text,
                       fg_color="transparent",
                       bg_color="transparent")


class Box(ctk.CTkFrame):
    """
    Custom CTkFrame class with transparent background.
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.configure(corner_radius=10,
                       fg_color="transparent",
                       bg_color="transparent")


class DarkBox(Box):
    """
    Custom CTkFrame class with darker background.
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.configure(fg_color=color_bg)


class BrightBox(Box):
    """
    Custom CTkFrame class with brighter background.
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.configure(fg_color=color_bg_br)

import time

from head import *
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from customtkinter import ThemeManager
import pyperclip
import socket
import subprocess
import threading
from PIL import Image, ImageTk
from test_functions import *
import json

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
import threading

default_fg_color = ThemeManager.theme["CTkButton"]["fg_color"]
accent_fg_color = "#d1641b"


class ActionButton(ctk.CTkButton):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        if "font" not in kwargs:
            kwargs["font"] = ctk.CTkFont(family="Calibri", size=14)
        text_width = kwargs["font"].measure(kwargs["text"])
        button_width = text_width + 20 + 25
        if button_width < 100:
            button_width = 90
        self.configure(width=button_width)


class RequestList(ttk.Treeview):
    """
    Request List class
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.popup_menu = tk.Menu(self, tearoff=0)
        self.popup_menu.add_command(label="Drop selected", command=self.drop_selected)
        self.popup_menu.add_command(label="Select all", command=self.select_all)
        self.popup_menu.add_command(label="Copy", command=self.copy_selected)
        self.bind("<Button-3>", self.popup)  # Right-click event

    def popup(self, event):
        """
        Right click menu
        """
        try:
            self.popup_menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.popup_menu.grab_release()

    def drop_selected(self):
        """
        Drop selected request
        """
        for item in self.selection():
            self.delete(item)

    def select_all(self):
        """
        Select all requests in the list
        """
        for item in self.get_children():
            self.selection_add(item)

    def copy_selected(self):
        """
        Copy values of selected requests
        """
        selected_items = self.selection()
        copied_text = ""
        for item in selected_items:
            values = self.item(item, 'values')
            copied_text += ", ".join(values) + "\n"
        pyperclip.copy(copied_text.strip())


class RequestContent(ctk.CTkScrollableFrame):
    """
    Request content class
    """
    def __init__(self, master, root, text=""):
        super().__init__(master)
        self.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self.grid_columnconfigure(1, weight=1)

        monoscape_font = ctk.CTkFont(family="Courier New", size=14, weight="normal")
        self.line_numbers = ctk.CTkLabel(self, text="", font=monoscape_font, anchor="nw", padx=6, pady=6)
        self.line_numbers.grid(row=0, column=0, sticky="ns")
        self.text_widget = ctk.CTkTextbox(self, wrap="none", font=monoscape_font, state="normal", padx=0, pady=0, activate_scrollbars=False)
        self.text_widget.grid(row=0, column=1, sticky="nsew")

        self.insert_text(text)

    def insert_text(self, text):
        """
        Inserting text
        """
        print(text)
        self.text_widget.configure(state='normal')
        self.text_widget.delete("0.0", "end")
        self.text_widget.insert("1.0", text)
        self.text_widget.configure(state='disabled')
        self.update_line_numbers()

    def update_line_numbers(self):
        """
        Updating line numbers
        """
        line_count = int(self.text_widget.index('end-1c').split('.')[0])
        line_numbers_string = "\n".join(str(i) for i in range(1, line_count + 1))
        self.line_numbers.configure(text=line_numbers_string)


class GUIProxy(ctk.CTkFrame):
    """
    Proxy Tab GUI class
    """
    def __init__(self, master, root):
        super().__init__(master)
        self.configure(fg_color="transparent")
        self.root = root
        self.intercepting = root.intercepting

        self.top_bar = ctk.CTkFrame(self, height=50)
        self.top_bar.pack(side=tk.TOP, fill=tk.X)

        self.icon_toggle_on = ctk.CTkImage(
            light_image=Image.open(f"{ASSET_DIR}/icon_toggle_on.png"), dark_image=Image.open(f"{ASSET_DIR}/icon_toggle_on.png"), size=(20,20))
        self.icon_toggle_off = ctk.CTkImage(
            light_image=Image.open(f"{ASSET_DIR}/icon_toggle_off.png"), dark_image=Image.open(f"{ASSET_DIR}/icon_toggle_off.png"), size=(20,20))
        self.toggle_intercept_button = ActionButton(
            self.top_bar, text="Intercept off", image=self.icon_toggle_off, command=self.toggle_intercept, fg_color="#d1641b", compound="left")
        self.toggle_intercept_button.pack(side=tk.LEFT, padx=15, pady=5)

        self.icon_foward = ctk.CTkImage(
            light_image=Image.open(f"{ASSET_DIR}/icon_arrow_up.png"),
            dark_image=Image.open(f"{ASSET_DIR}/icon_arrow_up.png"), size=(20, 20))
        self.forward_button = ActionButton(self.top_bar, text=f"Forward", image=self.icon_foward, state=tk.DISABLED, compound="left")
        self.forward_button.pack(side=tk.LEFT, padx=5, pady=15)

        self.icon_drop = ctk.CTkImage(
            light_image=Image.open(f"{ASSET_DIR}/icon_arrow_down.png"),
            dark_image=Image.open(f"{ASSET_DIR}/icon_arrow_down.png"), size=(20, 20))
        self.drop_button = ActionButton(
            self.top_bar, text=f"Drop", image=self.icon_drop, state=tk.DISABLED, command=self.drop_request, compound="left")
        self.drop_button.pack(side=tk.LEFT, padx=5, pady=15)

        self.send_to_repeater_button = ActionButton(self.top_bar, text=f"Send to repeater", state=tk.DISABLED)
        self.send_to_repeater_button.pack(side=tk.LEFT, padx=5, pady=15)

        self.send_to_intruder_button = ActionButton(self.top_bar, text=f"Send to intruder", state=tk.DISABLED)
        self.send_to_intruder_button.pack(side=tk.LEFT, padx=5, pady=15)

        self.icon_random = ctk.CTkImage(
            light_image=Image.open(f"{ASSET_DIR}/icon_random.png"),
            dark_image=Image.open(f"{ASSET_DIR}/icon_random.png"), size=(20, 20))
        self.add_random_entry = ActionButton(
            self.top_bar, text=f"Add random entry", image=self.icon_random, command=self.add_random_request, compound="left")
        self.add_random_entry.pack(side=tk.LEFT, padx=5, pady=15)

        self.icon_browser = ctk.CTkImage(
            light_image=Image.open(f"{ASSET_DIR}/icon_browser.png"), dark_image=Image.open(f"{ASSET_DIR}/icon_browser.png"), size=(20,20))
        self.browser_button = ActionButton(
            self.top_bar, text="Open browser", image=self.icon_browser, command=self.root.start_browser_thread, compound="left")
        self.browser_button.pack(side=tk.RIGHT, padx=5, pady=15)

        self.icon_settings = ctk.CTkImage(
            light_image=Image.open(f"{ASSET_DIR}/icon_settings.png"), dark_image=Image.open(f"{ASSET_DIR}/icon_settings.png"), size=(20,20))
        self.settings_button = ActionButton(self.top_bar, text="Proxy settings", image=self.icon_settings, compound="left")
        self.settings_button.pack(side=tk.RIGHT, padx=5, pady=15)

        self.paned_window = tk.PanedWindow(self, orient=tk.VERTICAL)
        self.paned_window.pack(fill=tk.BOTH, expand=1)

        self.top_pane = ctk.CTkFrame(self.paned_window)
        self.bottom_pane = ctk.CTkFrame(self.paned_window)

        self.paned_window.add(self.top_pane, height=400)
        self.paned_window.add(self.bottom_pane)

        bg_color = self._apply_appearance_mode(ThemeManager.theme["CTkFrame"]["fg_color"])
        text_color = self._apply_appearance_mode(ThemeManager.theme["CTkLabel"]["text_color"])
        selected_color = self._apply_appearance_mode(ThemeManager.theme["CTkButton"]["fg_color"])

        treestyle = ttk.Style()
        treestyle.theme_use('default')
        treestyle.configure("Treeview", background=bg_color, foreground=text_color, fieldbackground=bg_color,
                            borderwidth=0)
        treestyle.map('Treeview', background=[('selected', selected_color)], foreground=[('selected', 'white')])

        columns = ("Time", "Type", "Direction", "Method", "URL", "Status code", "Length")
        self.requests_list = RequestList(self.top_pane, columns=columns, show="headings", style="Treeview")
        self.requests_list.bind("<<TreeviewSelect>>", self.show_request)
        for col in columns:
            self.requests_list.heading(col, text=col)
            self.requests_list.column(col, width=100)
        self.requests_list.pack(fill=tk.BOTH, expand=True)

        self.placeholder_frame = ctk.CTkFrame(self.top_pane, fg_color="transparent")
        self.placeholder_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.intercept_off_image = ctk.CTkImage(light_image=Image.open(f"{ASSET_DIR}/intercept_off.png"), dark_image=Image.open(f"{ASSET_DIR}/intercept_off.png"), size=(107,181))
        self.intercept_on_image = ctk.CTkImage(light_image=Image.open(f"{ASSET_DIR}/intercept_on.png"), dark_image=Image.open(f"{ASSET_DIR}/intercept_on.png"), size=(107,181))
        self.placeholder_image = ctk.CTkLabel(self.placeholder_frame, image=self.intercept_off_image, text="")
        self.placeholder_image.pack(pady=5)
        self.placeholder_label = ctk.CTkLabel(self.placeholder_frame, text="Intercept is off")
        self.placeholder_label.pack(pady=5,expand=True)

        self.check_requests_list_empty()

        self.request_wrapper = ctk.CTkFrame(self.bottom_pane)
        self.request_wrapper.pack(fill="both",expand=True)
        self.request_wrapper.grid_columnconfigure(0, weight=1)
        self.request_wrapper.grid_rowconfigure(1, weight=1)

        self.request_wrapper_header = ctk.CTkLabel(self.request_wrapper, text="Request",
                                         font=ctk.CTkFont(family="Calibri", size=24, weight="bold"), anchor="w",
                                         padx=15, pady=15)
        self.request_wrapper_header.grid(row=0, column=0, sticky="ew")

        self.request_content = RequestContent(self.request_wrapper, self, "Select request to display its contents.")

        self.requests = []

        while self.root.browser_opened:
            print("Text")
            print(self.requests)

        self.update_thread = threading.Thread(target=self.receive_requests)
        self.update_thread.daemon = True
        self.update_thread.start()

    def toggle_intercept(self):
        if self.intercepting:
            self.toggle_intercept_button.configure(text="Intercept off", image=self.icon_toggle_off, fg_color=accent_fg_color)
            self.intercepting = False
            self.placeholder_label.configure(text="Intercept is off.")
            self.placeholder_image.configure(image=self.intercept_off_image)
            print("Turning intercept off.")
        else:
            self.toggle_intercept_button.configure(text="Intercept on", image=self.icon_toggle_on, fg_color=default_fg_color)
            self.intercepting = True
            self.placeholder_label.configure(text="Intercept is on.")
            self.placeholder_image.configure(image=self.intercept_on_image)
            print("Turning intercept on.")

            path = r"backend"
            command = f"start cmd /K mitmdump -s proxy.py "
            command = f"start cmd /K mitmdump -s proxy.py --listen-port 8082"

            try:
                subprocess.Popen(command, cwd=path, shell=True)
                print(f"Uruchomiono: {command}")
            except Exception as e:
                print(f"Error starting mitmdump: {e}")

        self.check_requests_list_empty()

    def browser_button_update(self):
        if self.root.browser_opened:
            self.browser_button.configure(text="Go to browser")
        else:
            self.browser_button.configure(text="Open browser")

    def requests_update(self):
        """
        Funkcja testowa do pobierania logoów z otwartej przeglądarki.
        """
        if self.root.requests is not None:
            for req in self.root.requests:
                print(json.dumps(json.loads(req["message"]), indent=5))

    def receive_requests(self):
        """
        Funkcja do odbierania żądań z serwera.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT_SERVER))
            s.listen()
            while True:
                conn, addr = s.accept()
                with conn:
                    request_data = conn.recv(1024).decode('utf-8')
                    if request_data:
                        self.add_request(request_data)

    def add_request(self, request_info):
        """
        Funkcja do dodawania żądań do listy w GUI.
        """
        self.requests_list.insert("", tk.END, values=request_info.split('\n'))

    def add_random_request(self):
        """
        Funkcja do dodawania losowego żądania do listy w GUI.
        """
        self.requests_list.insert("", tk.END, values=generate_random_reqeust())
        self.requests_list.selection_remove(self.requests_list.get_children())
        self.requests_list.selection_add(self.requests_list.get_children()[-1])
        self.check_requests_list_empty()

    def drop_request(self):
        """
        Funkcja do usuwania żądania do listy w GUI.
        """
        self.requests_list.drop_selected()
        if len(self.requests_list.get_children()) > 0:
            self.requests_list.selection_add(self.requests_list.get_children()[-1])
        self.check_requests_list_empty()

    def check_requests_list_empty(self):
        """
        Funkcja do sprawdzenia czy lista w GUI jest pusta.
        """
        if len(self.requests_list.get_children()) == 0:
            self.placeholder_frame.lift()
            self.forward_button.configure(state=tk.DISABLED)
            self.drop_button.configure(state=tk.DISABLED)
            self.send_to_intruder_button.configure(state=tk.DISABLED)
            self.send_to_repeater_button.configure(state=tk.DISABLED)
        else:
            self.placeholder_frame.lower()
            self.forward_button.configure(state=tk.NORMAL)
            self.drop_button.configure(state=tk.NORMAL)
            self.send_to_intruder_button.configure(state=tk.NORMAL)
            self.send_to_repeater_button.configure(state=tk.NORMAL)

    def show_request(self, event):
        """
        Funkcja do wyświetlania zawartości wybranego żądania.
        """
        if len(self.requests_list.get_children()) > 0:
            selected_item = self.requests_list.selection()[0]
            item = self.requests_list.item(selected_item)['values']
            self.request_content.insert_text('\n'.join(item))
        else:
            self.request_content.insert_text("Select request to display its contents.")

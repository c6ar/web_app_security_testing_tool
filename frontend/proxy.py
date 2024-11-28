from head import *
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from customtkinter import ThemeManager
import pyperclip
import socket
import subprocess
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

        treestyle = ttk.Style()
        treestyle.theme_use('default')
        treestyle.configure("Treeview", background=color_bg, foreground="white", fieldbackground=color_bg,
                            borderwidth=0)
        treestyle.configure("Treeview.Heading", background=color_bg, foreground="white", borderwidth=0)
        treestyle.map('Treeview', background=[('selected', color_acc)], foreground=[('selected', 'white')])
        treestyle.map("Treeview.Heading", background=[('active', color_acc)])

        self.configure(style="Treeview")

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

    def delete_all(self):
        for item in self.get_children():
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


class RequestTextBox(ctk.CTkTextbox):
    """
    Request content class
    """

    def __init__(self, master, root, text=""):
        super().__init__(master)
        self.root = root
        monoscape_font = ctk.CTkFont(family="Courier New", size=14, weight="normal")
        self.configure(wrap="none", font=monoscape_font, state="normal", padx=5, pady=5)

        self.insert_text(text)

    def insert_text(self, text):
        """
        Inserting text
        """
        self.delete("0.0", "end")
        self.insert("1.0", text)


class GUIProxy(ctk.CTkFrame):
    """
    Proxy Tab GUI class
    """

    def __init__(self, master, root):
        super().__init__(master)
        self.configure(fg_color="transparent")
        self.root = root
        self.intercepting = root.intercepting

        """
         > Sub navigation tabs of Proxy GUI
        """
        self.subnav = ctk.CTkFrame(self, fg_color="transparent")
        self.http_history_tab_button = NavButton(self.subnav, text="HTTP History", command=self.show_http_history_tab,
                                                 font=ctk.CTkFont(family="Calibri", size=14, weight="normal"),
                                                 background=color_bg_br, background_selected=color_bg)
        self.scope_tab_button = NavButton(self.subnav, text="Scope", command=self.show_scope_tab,
                                          font=ctk.CTkFont(family="Calibri", size=14, weight="normal"),
                                          background=color_bg_br, background_selected=color_bg)

        self.subnav.pack(side="top", fill="x", padx=15, pady=(10, 0))
        self.scope_tab_button.pack(side="left")
        self.http_history_tab_button.pack(side="left")

        """
         > Scope Frame starts here.
        """
        self.scope_frame = ctk.CTkFrame(self, fg_color="transparent")

        self.sf_top_bar = ctk.CTkFrame(self.scope_frame, height=50, corner_radius=10)
        self.sf_top_bar.pack(side=tk.TOP, fill=tk.X, pady=(0, 5), padx=5)

        self.icon_toggle_on = ctk.CTkImage(
            light_image=Image.open(f"{ASSET_DIR}\\icon_toggle_on.png"),
            dark_image=Image.open(f"{ASSET_DIR}\\icon_toggle_on.png"), size=(20, 20))
        self.icon_toggle_off = ctk.CTkImage(
            light_image=Image.open(f"{ASSET_DIR}\\icon_toggle_off.png"),
            dark_image=Image.open(f"{ASSET_DIR}\\icon_toggle_off.png"), size=(20, 20))
        self.toggle_intercept_button = ActionButton(
            self.sf_top_bar, text="Intercept off", image=self.icon_toggle_off, command=self.toggle_intercept,
            fg_color="#d1641b", compound="left", corner_radius=32)
        self.toggle_intercept_button.pack(side=tk.LEFT, padx=(10, 15), pady=15)

        self.icon_foward = ctk.CTkImage(
            light_image=Image.open(f"{ASSET_DIR}\\icon_arrow_up.png"),
            dark_image=Image.open(f"{ASSET_DIR}\\icon_arrow_up.png"), size=(20, 20))
        self.forward_button = ActionButton(self.sf_top_bar, text=f"Forward", image=self.icon_foward, state=tk.DISABLED,
                                           compound="left", corner_radius=32)
        self.forward_button.pack(side=tk.LEFT, padx=5, pady=15)

        self.icon_drop = ctk.CTkImage(
            light_image=Image.open(f"{ASSET_DIR}\\icon_arrow_down.png"),
            dark_image=Image.open(f"{ASSET_DIR}\\icon_arrow_down.png"), size=(20, 20))
        self.drop_button = ActionButton(
            self.sf_top_bar, text=f"Drop", image=self.icon_drop, state=tk.DISABLED, command=self.drop_request,
            compound="left", corner_radius=32)
        self.drop_button.pack(side=tk.LEFT, padx=5, pady=15)

        self.send_to_repeater_button = ActionButton(self.sf_top_bar, text=f"Send to repeater", state=tk.DISABLED,
                                                    corner_radius=32)
        self.send_to_repeater_button.pack(side=tk.LEFT, padx=5, pady=15)

        self.send_to_intruder_button = ActionButton(self.sf_top_bar, text=f"Send to intruder", state=tk.DISABLED,
                                                    corner_radius=32)
        self.send_to_intruder_button.pack(side=tk.LEFT, padx=5, pady=15)

        self.icon_random = ctk.CTkImage(
            light_image=Image.open(f"{ASSET_DIR}\\icon_random.png"),
            dark_image=Image.open(f"{ASSET_DIR}\\icon_random.png"), size=(20, 20))
        self.add_random_entry = ActionButton(
            self.sf_top_bar, text=f"Add random entry", image=self.icon_random, command=self.add_random_request,
            compound="left", corner_radius=32)
        self.add_random_entry.pack(side=tk.LEFT, padx=5, pady=15)

        self.icon_browser = ctk.CTkImage(
            light_image=Image.open(f"{ASSET_DIR}\\icon_browser.png"),
            dark_image=Image.open(f"{ASSET_DIR}\\icon_browser.png"), size=(20, 20))
        self.browser_button = ActionButton(
            self.sf_top_bar, text="Open browser", image=self.icon_browser, command=self.root.start_browser_thread,
            compound="left", corner_radius=32)
        self.browser_button.pack(side=tk.RIGHT, padx=(5, 10), pady=15)

        self.icon_settings = ctk.CTkImage(
            light_image=Image.open(f"{ASSET_DIR}\\icon_settings.png"),
            dark_image=Image.open(f"{ASSET_DIR}\\icon_settings.png"), size=(20, 20))
        self.settings_button = ActionButton(self.sf_top_bar, text="Proxy settings", image=self.icon_settings,
                                            compound="left", corner_radius=32)
        self.settings_button.pack(side=tk.RIGHT, padx=5, pady=15)

        self.sf_paned_window = tk.PanedWindow(self.scope_frame, orient=tk.VERTICAL, sashwidth=10,
                                              background=color_bg_br)
        self.sf_paned_window.pack(fill=tk.BOTH, expand=1, padx=5, pady=5)

        """
         >> Top Pane of Scope Frame starts here.
        """
        self.sf_top_pane = ctk.CTkFrame(self.sf_paned_window, corner_radius=10)
        self.sf_paned_window.add(self.sf_top_pane, height=350)

        columns = ("Time", "Type", "Direction", "Method", "URL", "Status code", "Length")
        self.requests_list = RequestList(self.sf_top_pane, columns=columns, show="headings", style="Treeview")
        self.requests_list.bind("<<TreeviewSelect>>", self.show_request)
        for col in columns:
            self.requests_list.heading(col, text=col)
            self.requests_list.column(col, width=100)
        self.requests_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.placeholder_frame = ctk.CTkFrame(self.sf_top_pane, fg_color="transparent")
        self.placeholder_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.intercept_off_image = ctk.CTkImage(light_image=Image.open(f"{ASSET_DIR}\\intercept_off.png"),
                                                dark_image=Image.open(f"{ASSET_DIR}\\intercept_off.png"),
                                                size=(81, 136))
        self.intercept_on_image = ctk.CTkImage(light_image=Image.open(f"{ASSET_DIR}\\intercept_on.png"),
                                               dark_image=Image.open(f"{ASSET_DIR}\\intercept_on.png"), size=(81, 136))
        self.placeholder_image = ctk.CTkLabel(self.placeholder_frame, image=self.intercept_off_image, text="")
        self.placeholder_image.pack(pady=5)
        self.placeholder_label = ctk.CTkLabel(self.placeholder_frame, text="Intercept is off")
        self.placeholder_label.pack(pady=5, expand=True)

        self.check_requests_list_empty()

        """
         >> Bottom Pane of Scope Frame starts here.
        """
        self.sf_bottom_pane = ctk.CTkFrame(self.sf_paned_window, corner_radius=10)
        self.sf_paned_window.add(self.sf_bottom_pane)

        self.request_wrapper = ctk.CTkFrame(self.sf_bottom_pane, fg_color="transparent")
        self.request_wrapper.pack(fill="both", expand=True, padx=10, pady=10)
        self.request_wrapper.grid_columnconfigure(0, weight=1)
        self.request_wrapper.grid_rowconfigure(0, weight=1)

        self.request_wrapper_header = ctk.CTkLabel(self.request_wrapper, text="Request",
                                                   font=ctk.CTkFont(family="Calibri", size=24, weight="bold"),
                                                   anchor="w",
                                                   padx=10, pady=10, height=20, fg_color=color_bg)
        self.request_wrapper_header.pack(fill=tk.X)

        self.request_content = RequestTextBox(self.request_wrapper, self, "Select request to display its contents.")
        self.request_content.pack(pady=10, padx=10, fill="both", expand=True)
        # while self.root.browser_opened:
        #     print("Text")
        #     print(self.requests)

        """
         > HTTP History Frame starts here.
        """
        self.http_history_frame = ctk.CTkFrame(self, fg_color="transparent")

        self.hhf_top_bar = ctk.CTkFrame(self.http_history_frame, height=50, corner_radius=10)
        self.hhf_top_bar.pack(side=tk.TOP, fill=tk.X, pady=(0, 5), padx=5)
        self.icon_delete = ctk.CTkImage(
            light_image=Image.open(f"{ASSET_DIR}\\icon_delete.png"),
            dark_image=Image.open(f"{ASSET_DIR}\\icon_delete.png"), size=(20, 20))
        self.hhf_delete_requests_button = ActionButton(
            self.hhf_top_bar, text="Delete all requests", image=self.icon_delete, command=self.delete_all_requests,
            fg_color="#d1641b", compound="left", corner_radius=32)
        self.hhf_delete_requests_button.pack(side=tk.LEFT, padx=(10, 15), pady=15)

        self.hhf_paned_window = tk.PanedWindow(self.http_history_frame, orient=tk.VERTICAL, sashwidth=10,
                                               background=color_bg_br)
        self.hhf_paned_window.pack(fill=tk.BOTH, expand=1, padx=5, pady=5)

        """
         >> Top Pane of HTTP History Frame starts here.
        """
        self.hhf_top_pane = ctk.CTkFrame(self.hhf_paned_window, corner_radius=10)
        self.hhf_paned_window.add(self.hhf_top_pane, height=350)

        hhf_columns = ("Time", "Type", "Direction", "Method", "URL", "Other columns")
        self.hhf_requests_list = RequestList(self.hhf_top_pane, columns=hhf_columns, show="headings", style="Treeview")
        self.hhf_requests_list.bind("<<TreeviewSelect>>", self.show_request)
        for col in hhf_columns:
            self.hhf_requests_list.heading(col, text=col)
            self.hhf_requests_list.column(col, width=100)
        self.hhf_requests_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        """
         >> Bottom Pane of HTTP History Frame starts here.
        """
        self.hhf_bottom_pane = ctk.CTkFrame(self.hhf_paned_window, corner_radius=10)
        self.hhf_paned_window.add(self.hhf_bottom_pane)

        self.hhf_bottom_pane.grid_columnconfigure(0, weight=1)
        self.hhf_bottom_pane.grid_columnconfigure(1, weight=1)
        self.hhf_bottom_pane.grid_rowconfigure(0, weight=1)

        self.hh_request_frame = ctk.CTkFrame(self.hhf_bottom_pane, fg_color=color_bg)
        self.hh_request_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.hh_request_header = ctk.CTkLabel(
            self.hh_request_frame,
            text="Request",
            font=ctk.CTkFont(family="Calibri", size=24, weight="bold"),
            anchor="w",
            padx=10,
            pady=10,
            height=20,
            fg_color=color_bg
        )
        self.hh_request_header.pack(fill=tk.X)

        self.hh_request_textbox = RequestTextBox(self.hh_request_frame, self, "Select request to display its contents.")
        self.hh_request_textbox.pack(pady=10, padx=10, fill="both", expand=True)

        self.hh_response_frame = ctk.CTkFrame(self.hhf_bottom_pane, fg_color=color_bg)
        self.hh_response_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.hh_response_header = ctk.CTkLabel(
            self.hh_response_frame,
            text="Response",
            font=ctk.CTkFont(family="Calibri", size=24, weight="bold"),
            anchor="w",
            padx=10,
            pady=10,
            height=20,
            fg_color=color_bg
        )
        self.hh_response_header.pack(fill=tk.X)

        self.hh_response_textbox = RequestTextBox(self.hh_response_frame, self,
                                                  "Select request to display its response's contents.")
        self.hh_response_textbox.pack(pady=10, padx=10, fill="both", expand=True)

        """
        Actual initialising of the Proxy GUI.
        """
        self.requests = []

        self.update_thread = threading.Thread(target=self.receive_requests)
        self.update_thread.daemon = True
        self.update_thread.start()

        self.show_scope_tab()

    def show_scope_tab(self):
        self.http_history_frame.pack_forget()
        self.http_history_tab_button.set_selected(False)
        self.scope_tab_button.set_selected(True)
        self.scope_frame.pack(side="top", fill="both", expand=True)

    def show_http_history_tab(self):
        self.scope_frame.pack_forget()
        self.http_history_tab_button.set_selected(True)
        self.scope_tab_button.set_selected(False)
        self.http_history_frame.pack(side="top", fill="both", expand=True)

    def toggle_intercept(self):
        if self.intercepting:
            self.toggle_intercept_button.configure(text="Intercept off", image=self.icon_toggle_off,
                                                   fg_color=accent_fg_color)
            self.intercepting = False
            self.placeholder_label.configure(text="Intercept is off.")
            self.placeholder_image.configure(image=self.intercept_off_image)
            print("Turning intercept off.")
        else:
            self.toggle_intercept_button.configure(text="Intercept on", image=self.icon_toggle_on,
                                                   fg_color=default_fg_color)
            self.intercepting = True
            self.placeholder_label.configure(text="Intercept is on.")
            self.placeholder_image.configure(image=self.intercept_on_image)
            print("Turning intercept on.")

            path = r"backend"
            # command = f"start cmd /K mitmdump -s proxy.py "
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

    def delete_all_requests(self):
        self.hhf_requests_list.delete_all()

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

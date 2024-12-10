import os
import pickle
import random
from idlelib.rpc import response_queue
from flask import request
from backend.Request import *
import dill
import time
from operator import truediv
from backend.Request import Request2
from mitmproxy.http import Headers, Request, Response
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
import json
import threading

i = 0

default_fg_color = ThemeManager.theme["CTkButton"]["fg_color"]
accent_fg_color = "#d1641b"


class ActionButton(ctk.CTkButton):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        if "font" not in kwargs:
            kwargs["font"] = ctk.CTkFont(family="Calibri", size=14)
        text_width = kwargs["font"].measure(kwargs["text"])
        self.button_width = text_width + 20 + 25
        if self.button_width < 100:
            self.button_width = 100
        self.configure(width=self.button_width)


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
        treestyle.map("Treeview.Heading", background=[('active', color_bg)])

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
        self.monoscape_font = ctk.CTkFont(family="Courier New", size=14, weight="normal")
        self.monoscape_font_italic = ctk.CTkFont(family="Courier New", size=14, weight="normal", slant="italic")
        self.configure(wrap="none", font=self.monoscape_font, state="normal", padx=5, pady=5)

        self.insert_text(text)

    def insert_text(self, text):
        """
        Inserting text
        """
        self.delete("0.0", "end")
        self.insert("1.0", text)

    def get_text(self):
        """
        Retrieve the current text content from the text box.
        """
        return self.get("1.0", "end").strip()  # Use `self.get` directly.


class GUIProxy(ctk.CTkFrame):
    """
    Proxy Tab GUI class
    """

    def __init__(self, master, root):
        super().__init__(master)
        self.process = None
        self.configure(fg_color="transparent")
        self.root = root
        self.intercepting = root.intercepting

        """
         > Sub navigation tabs of Proxy GUI
        """
        self.subnav = ctk.CTkFrame(self, fg_color="transparent")
        self.http_history_tab_button = NavButton(self.subnav, text="HTTP Traffic", command=self.show_http_history_tab,
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
            fg_color=color_acc3, hover_color=color_acc4, compound="left", corner_radius=32)

        self.icon_foward = ctk.CTkImage(
            light_image=Image.open(f"{ASSET_DIR}\\icon_arrow_up.png"),
            dark_image=Image.open(f"{ASSET_DIR}\\icon_arrow_up.png"), size=(20, 20))

        self.icon_drop = ctk.CTkImage(
            light_image=Image.open(f"{ASSET_DIR}\\icon_arrow_down.png"),
            dark_image=Image.open(f"{ASSET_DIR}\\icon_arrow_down.png"), size=(20, 20))
        self.drop_button = ActionButton(
            self.sf_top_bar, text=f"Drop", image=self.icon_drop, state=tk.NORMAL, command=self.drop_request,
            compound="left", corner_radius=32)

        self.send_to_repeater_button = ActionButton(self.sf_top_bar, text=f"Send to repeater", state=tk.DISABLED,
                                                    corner_radius=32)

        self.send_to_intruder_button = ActionButton(self.sf_top_bar, text=f"Send to intruder", state=tk.DISABLED,
                                                    corner_radius=32)

        self.icon_random = ctk.CTkImage(
            light_image=Image.open(f"{ASSET_DIR}\\icon_random.png"),
            dark_image=Image.open(f"{ASSET_DIR}\\icon_random.png"), size=(20, 20))
        self.add_random_entry = ActionButton(
            self.sf_top_bar, text=f"Random request", image=self.icon_random, command=self.generate_random_request,
            compound="left", corner_radius=32)

        self.icon_browser = ctk.CTkImage(
            light_image=Image.open(f"{ASSET_DIR}\\icon_browser.png"),
            dark_image=Image.open(f"{ASSET_DIR}\\icon_browser.png"), size=(20, 20))
        self.browser_button = ActionButton(
            self.sf_top_bar, text="Open browser", image=self.icon_browser, command=self.root.start_browser_thread,
            compound="left", corner_radius=32)

        self.icon_settings = ctk.CTkImage(
            light_image=Image.open(f"{ASSET_DIR}\\icon_settings.png"),
            dark_image=Image.open(f"{ASSET_DIR}\\icon_settings.png"), size=(20, 20))
        self.settings_button = ActionButton(
            self.sf_top_bar, text="Proxy settings", image=self.icon_settings, command=self.open_settings_window,
            compound="left", corner_radius=32)
        self.settings_window = None
        self.settings_entries = {}
        self.running_conf = self.load_config()

        self.sf_paned_window = tk.PanedWindow(self.scope_frame, orient=tk.VERTICAL, sashwidth=10,
                                              background=color_bg_br)
        self.sf_paned_window.pack(fill=tk.BOTH, expand=1, padx=5, pady=5)

        """
         >> Top Pane of Scope Frame starts here.
        """
        self.sf_top_pane = ctk.CTkFrame(self.sf_paned_window, corner_radius=10)
        self.sf_paned_window.add(self.sf_top_pane, height=350)

        columns = ("Host", "URL", "Method", "Content")
        self.sf_requests_list = RequestList(self.sf_top_pane, columns=columns, show="headings", style="Treeview",
                                            selectmode="none")
        self.sf_requests_list.bind("<<TreeviewSelect>>", self.show_scope_request_content)
        for col in columns:
            self.sf_requests_list.heading(col, text=col)
            self.sf_requests_list.column(col, width=100)
        self.sf_requests_list.column("Content", width=0, stretch=tk.NO)
        self.sf_requests_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.sf_intercept_placeholder = ctk.CTkFrame(self.sf_top_pane, fg_color="transparent")
        self.sf_intercept_placeholder.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.intercept_off_image = ctk.CTkImage(light_image=Image.open(f"{ASSET_DIR}\\intercept_off.png"),
                                                dark_image=Image.open(f"{ASSET_DIR}\\intercept_off.png"),
                                                size=(81, 136))
        self.intercept_on_image = ctk.CTkImage(light_image=Image.open(f"{ASSET_DIR}\\intercept_on.png"),
                                               dark_image=Image.open(f"{ASSET_DIR}\\intercept_on.png"), size=(81, 136))
        self.sf_placeholder_image = ctk.CTkLabel(self.sf_intercept_placeholder, image=self.intercept_off_image, text="")
        self.sf_placeholder_image.pack(pady=5)
        self.sf_placeholder_label = ctk.CTkLabel(self.sf_intercept_placeholder, text="Intercept is off")
        self.sf_placeholder_label.pack(pady=5, expand=True)

        """
         >> Bottom Pane of Scope Frame starts here.
        """
        self.sf_bottom_pane = ctk.CTkFrame(self.sf_paned_window, corner_radius=10)
        self.sf_paned_window.add(self.sf_bottom_pane)

        self.sf_request_wrapper = ctk.CTkFrame(self.sf_bottom_pane, fg_color="transparent")
        self.sf_request_wrapper.pack(fill="both", expand=True, padx=10, pady=10)
        self.sf_request_wrapper.grid_columnconfigure(0, weight=1)
        self.sf_request_wrapper.grid_rowconfigure(0, weight=1)

        self.sf_request_wrapper_header = ctk.CTkLabel(self.sf_request_wrapper, text="Request",
                                                      font=ctk.CTkFont(family="Calibri", size=24, weight="bold"),
                                                      anchor="w",
                                                      padx=10, pady=10, height=20, fg_color=color_bg)
        self.sf_request_wrapper_header.pack(fill=tk.X)

        self.sf_request_content = RequestTextBox(self.sf_request_wrapper, self,
                                                 "Select request to display its contents.")
        self.sf_request_content.pack(pady=10, padx=10, fill="both", expand=True)

        self.forward_button = ActionButton(self.sf_top_bar, text=f"Forward", image=self.icon_foward, state=tk.DISABLED,
                                           compound="left", corner_radius=32, command=self.send_reqeust_from_scope)

        self.toggle_intercept_button.pack(side=tk.LEFT, padx=(10, 15), pady=15)
        self.drop_button.pack(side=tk.LEFT, padx=5, pady=15)
        self.forward_button.pack(side=tk.LEFT, padx=5, pady=15)
        self.send_to_repeater_button.pack(side=tk.LEFT, padx=5, pady=15)
        self.send_to_intruder_button.pack(side=tk.LEFT, padx=5, pady=15)
        self.add_random_entry.pack(side=tk.LEFT, padx=5, pady=15)
        self.browser_button.pack(side=tk.RIGHT, padx=(5, 10), pady=15)
        self.settings_button.pack(side=tk.RIGHT, padx=5, pady=15)

        """
         > HTTP History Frame starts here.
        """
        self.http_history_frame = ctk.CTkFrame(self, fg_color="transparent")

        self.hhf_top_bar = ctk.CTkFrame(self.http_history_frame, height=50, corner_radius=10)
        self.hhf_top_bar.pack(side=tk.TOP, fill=tk.X, pady=(0, 5), padx=5)

        self.icon_delete = ctk.CTkImage(
            light_image=Image.open(f"{ASSET_DIR}\\icon_delete.png"),
            dark_image=Image.open(f"{ASSET_DIR}\\icon_delete.png"), size=(20, 20))
        self.icon_send = ctk.CTkImage(
            light_image=Image.open(f"{ASSET_DIR}\\icon_arrow_up.png"),
            dark_image=Image.open(f"{ASSET_DIR}\\icon_arrow_up.png"), size=(20, 20))

        self.hhf_send_requests_to_scope_button = ActionButton(
            self.hhf_top_bar, text="Send to scope", image=self.icon_send, command=self.send_request_to_filter,
            fg_color=color_acc, hover_color=color_acc2, compound="left", corner_radius=32)
        self.hhf_delete_requests_button = ActionButton(
            self.hhf_top_bar, text="Delete all requests", image=self.icon_delete,
            command=self.delete_all_requests_in_http_traffic,
            fg_color=color_acc3, hover_color=color_acc4, compound="left", corner_radius=32)
        self.hhf_browser_button = ActionButton(
            self.hhf_top_bar, text="Open browser", image=self.icon_browser, command=self.root.start_browser_thread,
            compound="left", corner_radius=32)

        self.hhf_send_requests_to_scope_button.pack(side=tk.LEFT, padx=(10, 5), pady=15)
        self.hhf_delete_requests_button.pack(side=tk.LEFT, padx=5, pady=15)
        self.hhf_browser_button.pack(side=tk.RIGHT, padx=(10, 5), pady=15)

        self.hhf_paned_window = tk.PanedWindow(self.http_history_frame, orient=tk.VERTICAL, sashwidth=10,
                                               background=color_bg_br)
        self.hhf_paned_window.pack(fill=tk.BOTH, expand=1, padx=5, pady=5)

        """
         >> Top Pane of HTTP History Frame starts here.
        """
        self.hhf_top_pane = ctk.CTkFrame(self.hhf_paned_window, corner_radius=10)
        self.hhf_paned_window.add(self.hhf_top_pane, height=350)

        hhf_columns = ("Host", "URL", "Method", "Request", "Status code", "Title", "Length", "Response")
        self.hhf_requests_list = RequestList(self.hhf_top_pane, columns=hhf_columns, show="headings", style="Treeview")
        self.hhf_requests_list.bind("<<TreeviewSelect>>", self.show_history_request_content)
        for col in hhf_columns:
            self.hhf_requests_list.heading(col, text=col)
            self.hhf_requests_list.column(col, width=100)
        self.hhf_requests_list.column("Request", width=0, stretch=tk.NO)
        self.hhf_requests_list.column("Response", width=0, stretch=tk.NO)
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
                                                  "Select request to display its response contents.")
        self.hh_response_textbox.configure(state=tk.DISABLED)
        self.hh_response_textbox.pack(pady=10, padx=10, fill="both", expand=True)

        """
        Actual initialising of the Proxy GUI.
        """
        self.requests = []

        self.update_thread_scope = threading.Thread(target=self.receive_and_add_to_scope)
        self.update_thread_scope.daemon = True
        self.update_thread_scope.start()
        self.update_thread_traffic = threading.Thread(target=self.receive_and_add_to_http_traffic)
        self.update_thread_traffic.daemon = True
        self.update_thread_traffic.start()
        self.deserialized_flow = None
        self.show_scope_tab()

        self.check_requests_list_empty()

        """
        Run mitmproxy at start
        """
        if not self.process:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.join(current_dir, "..", "backend")
            proxy_script = os.path.join(backend_dir, "proxy.py")
            command = ["mitmdump", "-s", proxy_script, "--listen-port", "8082"]

            threading.Thread(target=self.run_mitmdump, args=(command, backend_dir)).start()
        self.intercepting = True

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
        if self.root.intercepting:
            self.toggle_intercept_button.configure(text="Intercept off", image=self.icon_toggle_off,
                                                   fg_color=color_acc3, hover_color=color_acc4)
            self.root.intercepting = False
            self.sf_placeholder_label.configure(text="Intercept is off.")
            self.sf_placeholder_image.configure(image=self.intercept_off_image)
            print("Turning intercept off.")
            self.change_intercept_state()
        else:
            self.toggle_intercept_button.configure(text="Intercept on", image=self.icon_toggle_on,
                                                   fg_color=color_acc, hover_color=color_acc2)
            self.root.intercepting = True
            self.sf_placeholder_label.configure(text="Intercept is on.")
            self.sf_placeholder_image.configure(image=self.intercept_on_image)
            print("Turning intercept on.")
            self.change_intercept_state()
        self.check_requests_list_empty()

    def change_intercept_state(self):
        flag = "Change state"
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, FRONT_BACK_INTERCEPTBUTTON_PORT))
                serialized_flag = flag.encode("utf-8")
                s.sendall(serialized_flag)
        except Exception as e:
            print(f"Error while sending change intercept state flag: {e}")

    def run_mitmdump(self, command, cwd):
        try:
            self.process = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = self.process.communicate()

            if stdout:
                print(f"Mitmdump stdout:\n{stdout.decode('utf-8', errors='ignore')}")
            if stderr:
                print(f"Mitmdump stderr:\n{stderr.decode('utf-8', errors='ignore')}")

        except Exception as e:
            print(f"Error while turn on Proxy: {e}")
        finally:
            self.process = None

    def browser_button_update(self):
        if self.root.browser_opened:
            self.browser_button.configure(text="Go to browser")
            self.hhf_browser_button.configure(text="Go to browser")
        else:
            self.browser_button.configure(text="Open browser")
            self.hhf_browser_button.configure(text="Open browser")

    def check_requests_list_empty(self):
        """
        Checks if lists in Gui are empty
        """
        if len(self.sf_requests_list.get_children()) == 0:
            self.sf_intercept_placeholder.lift()
            self.forward_button.configure(state=tk.DISABLED)
            self.drop_button.configure(state=tk.DISABLED)
            self.send_to_intruder_button.configure(state=tk.DISABLED)
            self.send_to_repeater_button.configure(state=tk.DISABLED)
        else:
            self.sf_intercept_placeholder.lower()
            self.forward_button.configure(state=tk.NORMAL)
            self.drop_button.configure(state=tk.NORMAL)
            self.send_to_intruder_button.configure(state=tk.NORMAL)
            self.send_to_repeater_button.configure(state=tk.NORMAL)

        if len(self.hhf_requests_list.get_children()) == 0:
            self.hhf_send_requests_to_scope_button.configure(state=tk.DISABLED)
            self.hhf_delete_requests_button.configure(state=tk.DISABLED)
        else:
            self.hhf_send_requests_to_scope_button.configure(state=tk.NORMAL)
            self.hhf_delete_requests_button.configure(state=tk.NORMAL)

    def show_history_request_content(self, event):
        """
        Shows HTTP message of a request in textbox in history tab.
        """
        if len(self.hhf_requests_list.selection()) > 0:
            selected_item = self.hhf_requests_list.selection()[0]
            request_string = self.hhf_requests_list.item(selected_item)['values'][3]
            if len(self.hhf_requests_list.item(selected_item)['values']) == 8:
                response_string = self.hhf_requests_list.item(selected_item)['values'][7]
            elif len(self.hhf_requests_list.item(selected_item)['values']) == 5:
                response_string = self.hhf_requests_list.item(selected_item)['values'][5]
            else:
                response_string = "Request got no response."
            self.hh_request_textbox.configure(state=tk.NORMAL, font=self.hh_request_textbox.monoscape_font)
            self.hh_request_textbox.insert_text(request_string)
            self.hh_response_textbox.configure(state=tk.NORMAL, font=self.hh_request_textbox.monoscape_font)
            self.hh_response_textbox.insert_text(response_string)
            self.hh_response_textbox.configure(state=tk.DISABLED)

        else:
            self.hh_request_textbox.configure(state=tk.NORMAL)
            self.hh_request_textbox.insert_text("Select a request to display its contents.")
            self.hh_request_textbox.configure(state=tk.DISABLED, font=self.hh_request_textbox.monoscape_font_italic)
            self.hh_response_textbox.configure(state=tk.NORMAL)
            self.hh_response_textbox.insert_text("Select a request to display contents of its response.")
            self.hh_response_textbox.configure(state=tk.DISABLED, font=self.hh_request_textbox.monoscape_font_italic)

    def show_scope_request_content(self, event):
        """
        Shows HTTP message of a request in textbox in scope tab.
        """
        if len(self.sf_requests_list.selection()) > 0:
            selected_item = self.sf_requests_list.selection()[0]
            request_string = self.sf_requests_list.item(selected_item)['values'][3]
            self.sf_request_content.configure(state=tk.NORMAL, font=self.hh_request_textbox.monoscape_font)
            self.sf_request_content.insert_text(request_string)
        else:
            self.sf_request_content.configure(state=tk.NORMAL)
            self.sf_request_content.insert_text("Select a request to display its contents.")
            self.sf_request_content.configure(state=tk.DISABLED, font=self.hh_request_textbox.monoscape_font_italic)

    def receive_and_add_to_http_traffic(self):
        """
            Receives tab = [flow.request, flow.response] from backend.proxy.WebRequestInterceptor.send_flow_to_http_trafic_tab
            and adds it to HTTP traffic tab.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, BACK_FRONT_HISTORYREQUESTS_PORT))
            s.listen()
            while True:
                conn, addr = s.accept()
                with conn:
                    serialized_flow = conn.recv(4096)
                    if serialized_flow:
                        try:
                            flow_tab = pickle.loads(serialized_flow)
                            if isinstance(flow_tab, list) and len(flow_tab) == 2:
                                request2 = Request2.from_request(flow_tab[0])
                                response = flow_tab[1]
                                # print(f"REQUEST AND RESPONSE\n\tRequest:\n\t\t{request2}\tResponse:\n\t\t{response}")
                                self.add_reqeust_to_http_traffic_tab(request2, response)
                            else:
                                # print(f"REQUEST ONLY\n\tRequest:\n\t\t{request2}")
                                self.add_reqeust_to_http_traffic_tab(request2)
                            self.check_requests_list_empty()
                        except Exception as e:
                            if str(e) != "pickle data was truncated":  #cannot pickle "cryptography.hazmat.bindings._rust.x509.Certificate"
                                print(f"Error while deserialization request to http traffic: {e}")

    def receive_and_add_to_scope(self):
        """
           Receives request from flow.request and adds it to scope tab.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, BACK_FRONT_SCOPEREQUESTS_PORT))
            s.listen()

            while True:
                conn, addr = s.accept()

                with conn:
                    serialized_reqeust = conn.recv(4096)
                    if serialized_reqeust:
                        try:
                            deserialized_request = pickle.loads(serialized_reqeust)
                            request2 = Request2.from_request(deserialized_request)
                            self.add_request_to_scope_tab(request2)
                        except Exception as e:
                            print(f"Error while deserialization recieved in scope: {e}")

                        self.check_requests_list_empty()

    def add_reqeust_to_http_traffic_tab(self, req, resp=None):
        """
        Adds request to HTTP traffic list in GUI.
        """
        host = req.host
        url = req.path
        method = req.method
        request_content = req.return_http_message()
        if resp is None:
            code = ""
            title = ""
            length = 0
            response_content = ""
        else:
            code = resp.status_code
            title = ""
            response_content = resp.content.decode('utf-8')
            length = len(response_content)
        values = (host, url, method, request_content, code, title, length, response_content)

        self.hhf_requests_list.insert("", tk.END, values=values)

        if len(self.hhf_requests_list.selection()) == 0:
            self.hhf_requests_list.selection_add(self.hhf_requests_list.get_children()[0])

    def add_request_to_scope_tab(self, req=None):
        """
            Adds request to scope list in GUI tab.
        """
        if req is None:
            if len(self.hhf_requests_list.get_children()) > 0:
                selected_item = self.hhf_requests_list.selection()[0]
                host = self.hhf_requests_list.item(selected_item)['values'][0]
                url = self.hhf_requests_list.item(selected_item)['values'][1]
                method = self.hhf_requests_list.item(selected_item)['values'][2]
                request_content = self.hh_request_textbox.get_text()
                values = (host, url, method, request_content)

                self.sf_requests_list.insert("", 0, values=values)
        else:
            host = req.host
            url = req.path
            method = req.method
            request_content = req.return_http_message()
            values = (host, url, method, request_content)

            self.sf_requests_list.insert("", 0, values=values)

        if len(self.sf_requests_list.selection()) == 0:
            self.sf_requests_list.selection_add(self.sf_requests_list.get_children()[0])

    def send_reqeust_from_scope(self):
        """
        Sends request made from scope tab textbox, request is forwarded to web browser.
        """
        request2 = Request2.from_http_message(self.sf_request_content.get_text())
        request = request2.to_request()
        serialized_reqeust = pickle.dumps(request)

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, FRONT_BACK_FORWARDBUTTON_PORT))
                s.sendall(serialized_reqeust)
        except Exception as e:
            print(f"Error while sending after Forward button: {e}")

        self.sf_requests_list.drop_selected()
        self.check_requests_list_empty()
        if len(self.sf_requests_list.get_children()) > 0:
            self.sf_requests_list.selection_add(self.sf_requests_list.get_children()[-1])

    def generate_random_request(self):
        """
        Adds random request in scope tab
        """
        url = f"http://{random.choice(['example', 'test', 'check', 'domain'])}.{random.choice(['org', 'com', 'pl', 'eu'])}/"
        path = f"/{random.choice(['entry', 'page', '', 'test', 'subpage'])}"
        method = random.choice(["GET", "POST", "PUT", "DELETE"])
        content = f'{method} {path} HTTP/1.1\nHost: {url}\nProxy-Connection: keep-alive\nrandom stuff here'
        random_request = [url, path, method, content]

        self.sf_requests_list.insert("", 0, values=random_request)
        self.hhf_requests_list.insert("", tk.END, values=random_request)
        self.sf_requests_list.selection_remove(self.sf_requests_list.get_children())
        self.sf_requests_list.selection_add(self.sf_requests_list.get_children()[-1])
        self.check_requests_list_empty()

    def drop_request(self):
        """
            Removes an request from list in GUI, request is dropped, proxy sends "request dropped info".
        """
        flag = "True"
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, FRONT_BACK_DROPREQUEST_PORT))
                serialized_flag = flag.encode("utf-8")
                s.sendall(serialized_flag)
        except Exception as e:
            print(f"Error while sending flag to kill process: {e}")

        self.sf_requests_list.drop_selected()
        try:
            if self.root.browser is not None:
                if len(self.root.browser.window_handles) > 0:
                    self.root.browser.execute_script("alert('WASTT: Request has been dropped by user. Please close this page.');")
        except Exception as e:
            print(f"Error while letting know about dropped request: {e}")

        if len(self.sf_requests_list.get_children()) > 0:
            self.sf_requests_list.selection_add(self.sf_requests_list.get_children()[-1])

        self.check_requests_list_empty()

    def delete_all_requests_in_http_traffic(self):
        """
            Deletes all requests from HTTP Traffic list.
        """
        self.hhf_requests_list.delete_all()
        self.check_requests_list_empty()

    def send_request_to_filter(self):
        """
            Updates filtering in backend logic, sends hostname
            Adds request to scope tab list
        """
        request2 = Request2.from_http_message(self.hh_request_textbox.get_text())
        request = request2.to_request()
        serialized_reqeust = pickle.dumps(request)

        self.add_request_to_scope_tab()
        self.check_requests_list_empty()

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, FRONT_BACK_SCOPEUPDATE_PORT))
                s.sendall(serialized_reqeust)
        except Exception as e:
            print(f"Error while sendind request to filter: {e}")

        # if request is not None:
        #
        #     request2 = Request2.from_http_message(request_info)
        #     self.sf_requests_list.insert("", tk.END, values=request_info.split('\n'))
        #     serialized_reqeust2 = pickle.dumps(request2)
        #     try:
        #         with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        #             s.connect((HOST, PORT_INTERCEPT))
        #             s.sendall(serialized_reqeust2)
        #     except Exception as e:
        #         print(f"Błąd przy wysyłaniu żądania do PROXY: {e}")
        # else:

    def send_to_repeater(self):
        pass

    def open_settings_window(self):
        self.settings_window = ctk.CTkToplevel(self.root)
        self.settings_window.title("Proxy Settings")
        self.settings_window.attributes("-topmost", True)

        for key, value in self.running_conf.items():
            label = ctk.CTkLabel(self.settings_window, text=key)
            label.pack()
            entry = ctk.CTkEntry(self.settings_window)
            entry.insert(0, value)
            entry.pack()
            self.settings_entries[key] = entry

        save_button = ctk.CTkButton(self.settings_window, text="Save", command=self.save_settings, fg_color=color_acc3, hover_color=color_acc4, corner_radius=32)
        save_button.pack(side=tk.LEFT, padx=10, pady=10)

        cancel_button = ctk.CTkButton(self.settings_window, text="Cancel", command=self.settings_window.destroy, corner_radius=32)
        cancel_button.pack(side=tk.RIGHT, padx=10, pady=10)

        self.settings_window.lift()

    def save_settings(self):
        for key, entry in self.settings_entries.items():
            self.running_conf[key] = entry.get()
        self.save_config(self.running_conf)
        self.settings_window.destroy()

    def load_config(self):
        default_config = {
            "host_address": "127.0.0.1",
            "port": 8082
        }
        config = default_config.copy()
        try:
            with open("proxy.conf", "r") as file:
                for line in file:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        config[key.strip()] = value.strip()
        except FileNotFoundError:
            print("Proxy config file could not be open. Default settings loaded.")
        return config

    def save_config(self, config):
        try:
            with open("proxy.conf", "r") as file:
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

            with open("proxy.conf", "w") as file:
                file.writelines(updated_lines)
                self.load_config()
        except Exception as e:
            print(f"Error during saving a config: {e}")


    # TODO Synching of threads(?)
    # TODO Actual implmentation of config logic in the app
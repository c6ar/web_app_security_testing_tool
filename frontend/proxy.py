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
from common import *
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

    # TODO FRONTEND: Rework the popmenu 3 scenarios: HTTP Traffics historical requests, Intercepted requests, Scope urls
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

        if len(self.get_children()) > 0 and len(self.selection()) == 0:
            self.selection_add(self.get_children()[-1])

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
        self.intercept_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.http_traffic_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.scope_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.tabs = {
            "HTTP Traffic": self.http_traffic_frame,
            "Intercept": self.intercept_frame,
            "Scope": self.scope_frame,
        }
        self.tab_nav = ctk.CTkFrame(self, fg_color="transparent")
        self.tab_nav.pack(side="top", fill="x", padx=15, pady=(10, 0))
        self.tab_nav_buttons = {}
        for tab in self.tabs.keys():
            self.tab_nav_buttons[tab] = NavButton(self.tab_nav, text=tab, command=lambda t=tab: self.switch_tab(t),
                                                  font=ctk.CTkFont(family="Calibri", size=14, weight="normal"),
                                                  background=color_bg_br, background_selected=color_bg)
            self.tab_nav_buttons[tab].pack(side="left")

        """
         > Intercept tab starts here.
        """
        self.if_top_bar = ctk.CTkFrame(self.intercept_frame, height=50, corner_radius=10)
        self.if_top_bar.pack(side=tk.TOP, fill=tk.X, pady=(0, 5), padx=5)
        
        self.if_toggle_intercept_button = ActionButton(
            self.if_top_bar, text="Intercept off", image=icon_toggle_off, command=self.toggle_intercept,
            fg_color=color_acc3, hover_color=color_acc4)
        self.if_drop_button = ActionButton(
            self.if_top_bar, text=f"Drop", image=icon_arrow_down, command=self.drop_request)
        self.if_send_to_repeater_button = ActionButton(
            self.if_top_bar, text=f"Send to repeater", command=lambda: self.send_to_repeater(self.if_request_textbox, self.if_request_list),
            state=tk.DISABLED)
        self.if_send_to_intruder_button = ActionButton(
            self.if_top_bar, text=f"Send to intruder", command=lambda: self.send_to_intruder(self.if_request_textbox, self.if_request_list), state=tk.DISABLED)
        self.if_add_random_entry = ActionButton(
            self.if_top_bar, text=f"Random request", image=icon_random, command=self.generate_random_request)
        self.if_browser_button = ActionButton(
            self.if_top_bar, text="Open browser", image=icon_browser, command=self.root.start_browser_thread)

        self.if_paned_window = tk.PanedWindow(self.intercept_frame, orient=tk.VERTICAL, sashwidth=10, background=color_bg_br)
        self.if_paned_window.pack(fill=tk.BOTH, expand=1, padx=5, pady=5)

        """
         >> Top pane of Intercept tab starts here.
        """
        self.if_top_pane = ctk.CTkFrame(self.if_paned_window, corner_radius=10)
        self.if_paned_window.add(self.if_top_pane, height=350)

        if_columns = ("Host", "URL", "Method", "Content", "RealURL")
        self.if_request_list = RequestList(self.if_top_pane, columns=if_columns, show="headings", style="Treeview",
                                           selectmode="none")
        self.if_request_list.bind("<<TreeviewSelect>>", self.show_scope_request_content)
        for col in if_columns:
            self.if_request_list.heading(col, text=col)
            self.if_request_list.column(col, width=100)
        self.if_request_list.column("Content", width=0, stretch=tk.NO)
        self.if_request_list.column("RealURL", width=0, stretch=tk.NO)
        self.if_request_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.if_intercept_placeholder = ctk.CTkFrame(self.if_top_pane, fg_color="transparent")
        self.if_intercept_placeholder.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.intercept_off_image = ctk.CTkImage(light_image=Image.open(f"{ASSET_DIR}\\intercept_off.png"),
                                                dark_image=Image.open(f"{ASSET_DIR}\\intercept_off.png"),
                                                size=(81, 136))
        self.intercept_on_image = ctk.CTkImage(light_image=Image.open(f"{ASSET_DIR}\\intercept_on.png"),
                                               dark_image=Image.open(f"{ASSET_DIR}\\intercept_on.png"), size=(81, 136))
        self.if_placeholder_image = ctk.CTkLabel(self.if_intercept_placeholder, image=self.intercept_off_image, text="")
        self.if_placeholder_image.pack(pady=5)
        self.if_placeholder_label = ctk.CTkLabel(self.if_intercept_placeholder, text="Intercept is off")
        self.if_placeholder_label.pack(pady=5, expand=True)

        """
         >> Bottom pane of Intercept tab starts here.
        """
        self.if_bottom_pane = ctk.CTkFrame(self.if_paned_window, corner_radius=10)
        self.if_paned_window.add(self.if_bottom_pane)

        self.if_request_wrapper = ctk.CTkFrame(self.if_bottom_pane, fg_color="transparent")
        self.if_request_wrapper.pack(fill="both", expand=True, padx=10, pady=10)
        self.if_request_wrapper.grid_columnconfigure(0, weight=1)
        self.if_request_wrapper.grid_rowconfigure(0, weight=1)

        self.if_request_wrapper_header = ctk.CTkLabel(self.if_request_wrapper, text="Request",
                                                      font=ctk.CTkFont(family="Calibri", size=24, weight="bold"),
                                                      anchor="w",
                                                      padx=10, pady=10, height=20, fg_color=color_bg)
        self.if_request_wrapper_header.pack(fill=tk.X)

        self.if_request_textbox = TextBox(self.if_request_wrapper, self, "Select request to display its contents.")
        self.if_request_textbox.pack(pady=10, padx=10, fill="both", expand=True)

        self.if_forward_button = ActionButton(self.if_top_bar, text=f"Forward", image=icon_arrow_up, state=tk.DISABLED,
                                              compound="left", corner_radius=32, command=self.send_reqeust_from_intercept)

        self.if_toggle_intercept_button.pack(side=tk.LEFT, padx=(10, 15), pady=15)
        self.if_drop_button.pack(side=tk.LEFT, padx=5, pady=15)
        self.if_forward_button.pack(side=tk.LEFT, padx=5, pady=15)
        self.if_send_to_repeater_button.pack(side=tk.LEFT, padx=5, pady=15)
        self.if_send_to_intruder_button.pack(side=tk.LEFT, padx=5, pady=15)
        self.if_add_random_entry.pack(side=tk.LEFT, padx=5, pady=15)
        self.if_browser_button.pack(side=tk.RIGHT, padx=(5, 10), pady=15)
        
        """
         > HTTP Taffic tab starts here.
        """
        self.htf_top_bar = ctk.CTkFrame(self.http_traffic_frame, height=50, corner_radius=10)
        self.htf_top_bar.pack(side=tk.TOP, fill=tk.X, pady=(0, 5), padx=5)

        self.htf_send_requests_to_scope_button = ActionButton(
            self.htf_top_bar, text="Add to scope", image=icon_arrow_up, command=self.add_url_to_scope,
            fg_color=color_acc, hover_color=color_acc2, compound="left", corner_radius=32)
        self.htf_send_requests_to_repeater_button = ActionButton(
            self.htf_top_bar, text="Send to repeater", image=icon_arrow_up, command=lambda: self.send_to_repeater(self.htf_request_textbox, self.htf_request_list),
            fg_color=color_acc, hover_color=color_acc2, compound="left", corner_radius=32)
        self.htf_delete_requests_button = ActionButton(
            self.htf_top_bar, text="Delete all requests", image=icon_delete,
            command=self.delete_all_requests_in_http_traffic,
            fg_color=color_acc3, hover_color=color_acc4, compound="left", corner_radius=32)
        self.htf_browser_button = ActionButton(
            self.htf_top_bar, text="Open browser", image=icon_browser, command=self.root.start_browser_thread,
            compound="left", corner_radius=32)

        self.htf_send_requests_to_scope_button.pack(side=tk.LEFT, padx=(10, 5), pady=15)
        self.htf_send_requests_to_repeater_button.pack(side=tk.LEFT, padx=5, pady=15)
        self.htf_delete_requests_button.pack(side=tk.LEFT, padx=5, pady=15)
        self.htf_browser_button.pack(side=tk.RIGHT, padx=(5, 10), pady=15)

        self.htf_paned_window = tk.PanedWindow(self.http_traffic_frame, orient=tk.VERTICAL, sashwidth=10,
                                               background=color_bg_br)
        self.htf_paned_window.pack(fill=tk.BOTH, expand=1, padx=5, pady=5)

        """
         >> Top pane of HTTP Traffic tab starts here.
        """
        self.htf_top_pane = ctk.CTkFrame(self.htf_paned_window, corner_radius=10)
        self.htf_paned_window.add(self.htf_top_pane, height=350)

        htf_columns = ("Host", "URL", "Method", "Request", "Status code", "Title", "Length", "Response", "RealURL")
        self.htf_request_list = RequestList(self.htf_top_pane, columns=htf_columns, show="headings", style="Treeview")
        self.htf_request_list.bind("<<TreeviewSelect>>", self.show_history_request_content)
        for col in htf_columns:
            self.htf_request_list.heading(col, text=col)
            self.htf_request_list.column(col, width=100)
        self.htf_request_list.column("Request", width=0, stretch=tk.NO)
        self.htf_request_list.column("Response", width=0, stretch=tk.NO)
        self.htf_request_list.column("RealURL", width=0, stretch=tk.NO)
        self.htf_request_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        """
         >> Bottom pane of HTTP Traffic tab starts here.
        """
        self.htf_bottom_pane = ctk.CTkFrame(self.htf_paned_window, corner_radius=10)
        self.htf_paned_window.add(self.htf_bottom_pane)

        self.htf_bottom_pane.grid_columnconfigure(0, weight=1)
        self.htf_bottom_pane.grid_columnconfigure(1, weight=1)
        self.htf_bottom_pane.grid_rowconfigure(0, weight=1)

        self.htf_request_frame = ctk.CTkFrame(self.htf_bottom_pane, fg_color=color_bg)
        self.htf_request_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.htf_request_header = HeaderTitle(self.htf_request_frame, "Request")
        self.htf_request_header.pack(fill=tk.X)

        self.htf_request_textbox = TextBox(self.htf_request_frame, self, "Select request to display its contents.")
        self.htf_request_textbox.pack(pady=10, padx=10, fill="both", expand=True)

        self.htf_response_frame = ctk.CTkFrame(self.htf_bottom_pane, fg_color=color_bg)
        self.htf_response_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.htf_response_header = HeaderTitle(self.htf_response_frame, "Response")
        self.htf_response_header.pack(fill=tk.X)

        self.htf_response_textbox = TextBox(self.htf_response_frame, self, "Select request to display its response contents.")
        self.htf_response_textbox.configure(state=tk.DISABLED)
        self.htf_response_textbox.pack(pady=10, padx=10, fill="both", expand=True)

        """
         > Scope tab starts here.
        """
        self.sf_wrapper = ctk.CTkFrame(self.scope_frame, fg_color=color_bg, corner_radius=10)
        self.sf_wrapper.pack(fill=tk.X, padx=10, pady=0)

        self.sf_header = HeaderTitle(self.sf_wrapper, "Scope")
        self.sf_header.pack(fill=tk.X, padx=10, pady=0)

        sf_columns = ("Enable", "Host prefix")
        self.sf_url_list = RequestList(
            self.sf_wrapper,
            columns=sf_columns,
            show="headings", style="Treeview", selectmode="browse")
        self.sf_url_list.heading("Enable", text="Enable?")
        self.sf_url_list.column("Enable", width=25)
        self.sf_url_list.heading("Host prefix", text="Host prefix")
        self.sf_url_list.pack(side="left", fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.sf_buttons = ctk.CTkFrame(self.sf_wrapper, fg_color="transparent")
        self.sf_buttons.pack(side="right", fill=tk.Y, padx=(0, 10))

        self.sf_add_button = ActionButton(self.sf_buttons, text="Add URL", command=self.add_url_to_scope_dialog)
        self.sf_add_button.pack(side="top", padx=5, pady=10)
        self.sf_add_url_dialog = None

        self.sf_remove_button = ActionButton(self.sf_buttons, text="Remove URL", command=self.remove_url_from_scope)
        self.sf_remove_button.pack(side="top", padx=5, pady=10)

        self.sf_clear_button = ActionButton(self.sf_buttons, text="Clear URLs", command=self.clear_scope)
        self.sf_clear_button.pack(side="top", padx=5, pady=10)

        """
        Actual initialising of the Proxy GUI.
        """
        self.update_thread_scope = threading.Thread(target=self.receive_and_add_to_scope)
        self.update_thread_scope.daemon = True
        self.update_thread_scope.start()
        self.update_thread_traffic = threading.Thread(target=self.receive_and_add_to_http_traffic)
        self.update_thread_traffic.daemon = True
        self.update_thread_traffic.start()
        self.deserialized_flow = None

        self.switch_tab("HTTP Traffic")

        self.check_request_lists_empty()

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
            print(f"Error while turning on Proxy process: {e}")
        finally:
            self.process = None

    def switch_tab(self, selected_tab):
        for tab_name, tab in self.tabs.items():
            if tab_name == selected_tab:
                # print(f"Debug Proxy/Tabs: Switching to {tab_name} tab")
                tab.pack(side="top", fill="both", expand=True)
                self.tab_nav_buttons[tab_name].set_selected(True)
            else:
                # print(f"Debug Proxy/Tabs: Hiding {tab_name} tab")
                tab.pack_forget()
                self.tab_nav_buttons[tab_name].set_selected(False)

    def toggle_intercept(self):
        if self.root.intercepting:
            self.if_toggle_intercept_button.configure(text="Intercept off", image=icon_toggle_off,
                                                      fg_color=color_acc3, hover_color=color_acc4)
            self.root.intercepting = False
            self.if_placeholder_label.configure(text="Intercept is off.")
            self.if_placeholder_image.configure(image=self.intercept_off_image)
            print("Turning intercept off.")
            self.change_intercept_state()
        else:
            self.if_toggle_intercept_button.configure(text="Intercept on", image=icon_toggle_on,
                                                      fg_color=color_acc, hover_color=color_acc2)
            self.root.intercepting = True
            self.if_placeholder_label.configure(text="Intercept is on.")
            self.if_placeholder_image.configure(image=self.intercept_on_image)
            print("Turning intercept on.")
            self.change_intercept_state()
        self.check_request_lists_empty()

    def change_intercept_state(self):
        flag = "Change state"
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, FRONT_BACK_INTERCEPTBUTTON_PORT))
                serialized_flag = flag.encode("utf-8")
                s.sendall(serialized_flag)
        except Exception as e:
            print(f"Error while sending change intercept state flag: {e}")

    def browser_button_update(self):
        if self.root.browser_opened:
            self.if_browser_button.configure(text="Go to browser")
            self.htf_browser_button.configure(text="Go to browser")
        else:
            self.if_browser_button.configure(text="Open browser")
            self.htf_browser_button.configure(text="Open browser")

    def check_request_lists_empty(self):
        """
        Checks if lists in Gui are empty
        """
        if len(self.if_request_list.get_children()) == 0:
            self.if_intercept_placeholder.lift()
            self.if_forward_button.configure(state=tk.DISABLED)
            self.if_drop_button.configure(state=tk.DISABLED)
            self.if_send_to_intruder_button.configure(state=tk.DISABLED)
            self.if_send_to_repeater_button.configure(state=tk.DISABLED)
        else:
            self.if_intercept_placeholder.lower()
            self.if_forward_button.configure(state=tk.NORMAL)
            self.if_drop_button.configure(state=tk.NORMAL)
            self.if_send_to_intruder_button.configure(state=tk.NORMAL)
            self.if_send_to_repeater_button.configure(state=tk.NORMAL)

        if len(self.htf_request_list.get_children()) == 0:
            self.htf_send_requests_to_scope_button.configure(state=tk.DISABLED)
            self.htf_send_requests_to_repeater_button.configure(state=tk.DISABLED)
            self.htf_delete_requests_button.configure(state=tk.DISABLED)
        else:
            self.htf_send_requests_to_scope_button.configure(state=tk.NORMAL)
            self.htf_send_requests_to_repeater_button.configure(state=tk.NORMAL)
            self.htf_delete_requests_button.configure(state=tk.NORMAL)

    def show_history_request_content(self, event):
        """
        Shows HTTP message of a request in textbox in history tab.
        """
        if len(self.htf_request_list.selection()) > 0:
            selected_item = self.htf_request_list.selection()[0]
            request_string = self.htf_request_list.item(selected_item)['values'][3]
            if len(self.htf_request_list.item(selected_item)['values']) == 8:
                response_string = self.htf_request_list.item(selected_item)['values'][7]
            elif len(self.htf_request_list.item(selected_item)['values']) == 5:
                response_string = self.htf_request_list.item(selected_item)['values'][5]
            else:
                response_string = "Request got no response."
            self.htf_request_textbox.configure(state=tk.NORMAL, font=self.htf_request_textbox.monoscape_font)
            self.htf_request_textbox.insert_text(request_string)
            self.htf_response_textbox.configure(state=tk.NORMAL, font=self.htf_request_textbox.monoscape_font)
            self.htf_response_textbox.insert_text(response_string)
            self.htf_response_textbox.configure(state=tk.DISABLED)

        else:
            self.htf_request_textbox.configure(state=tk.NORMAL)
            self.htf_request_textbox.insert_text("Select a request to display its contents.")
            self.htf_request_textbox.configure(state=tk.DISABLED, font=self.htf_request_textbox.monoscape_font_italic)
            self.htf_response_textbox.configure(state=tk.NORMAL)
            self.htf_response_textbox.insert_text("Select a request to display contents of its response.")
            self.htf_response_textbox.configure(state=tk.DISABLED, font=self.htf_request_textbox.monoscape_font_italic)

    def show_scope_request_content(self, event):
        """
        Shows HTTP message of a request in textbox in scope tab.
        """
        if len(self.if_request_list.selection()) > 0:
            selected_item = self.if_request_list.selection()[0]
            request_string = self.if_request_list.item(selected_item)['values'][3]
            self.if_request_textbox.configure(state=tk.NORMAL, font=self.htf_request_textbox.monoscape_font)
            self.if_request_textbox.insert_text(request_string)
        else:
            self.if_request_textbox.configure(state=tk.NORMAL)
            self.if_request_textbox.insert_text("Select a request to display its contents.")
            self.if_request_textbox.configure(state=tk.DISABLED, font=self.htf_request_textbox.monoscape_font_italic)

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
                            self.check_request_lists_empty()
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
                            self.add_request_to_intercept_tab(request2)
                        except Exception as e:
                            print(f"Error while deserialization recieved in scope: {e}")

                        self.check_request_lists_empty()

    def add_reqeust_to_http_traffic_tab(self, req, resp=None):
        """
        Adds request to HTTP traffic list in GUI.
        """
        real_url=req.url
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
        values = (host, url, method, request_content, code, title, length, response_content, real_url)

        self.htf_request_list.insert("", tk.END, values=values)

        if len(self.htf_request_list.selection()) == 0:
            self.htf_request_list.selection_add(self.htf_request_list.get_children()[0])

    def add_request_to_intercept_tab(self, req=None):
        """
            Adds request to scope list in GUI tab.
        """
        if req is None:
            if len(self.htf_request_list.get_children()) > 0:
                selected_item = self.htf_request_list.selection()[0]
                host = self.htf_request_list.item(selected_item)['values'][0]
                url = self.htf_request_list.item(selected_item)['values'][1]
                method = self.htf_request_list.item(selected_item)['values'][2]
                real_url = self.htf_request_list.item(selected_item)['values'][8]
                request_content = self.htf_request_textbox.get_text()
                values = (host, url, method, request_content, real_url)

                self.if_request_list.insert("", 0, values=values)
        else:
            host = req.host
            url = req.path
            method = req.method
            request_content = req.return_http_message()
            values = (host, url, method, request_content)

            self.if_request_list.insert("", 0, values=values)

        if len(self.if_request_list.selection()) == 0:
            self.if_request_list.selection_add(self.if_request_list.get_children()[0])

    def send_reqeust_from_intercept(self):
        """
        Sends request made from scope tab textbox, request is forwarded to web browser.
        """
        request2 = Request2.from_http_message(self.if_request_textbox.get_text())
        request = request2.to_request()
        serialized_reqeust = pickle.dumps(request)

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, FRONT_BACK_FORWARDBUTTON_PORT))
                s.sendall(serialized_reqeust)
        except Exception as e:
            print(f"Error while sending after Forward button: {e}")

        self.if_request_list.drop_selected()
        self.check_request_lists_empty()
        if len(self.if_request_list.get_children()) > 0:
            self.if_request_list.selection_add(self.if_request_list.get_children()[-1])

    def generate_random_request(self):
        """
        Adds random request in scope tab
        """
        url = f"http://{random.choice(['example', 'test', 'check', 'domain'])}.{random.choice(['org', 'com', 'pl', 'eu'])}/"
        path = f"/{random.choice(['entry', 'page', '', 'test', 'subpage'])}"
        method = random.choice(["GET", "POST", "PUT", "DELETE"])
        content = f'{method} {path} HTTP/1.1\nHost: {url}\nProxy-Connection: keep-alive\nrandom stuff here'
        random_request = [url, path, method, content]

        self.if_request_list.insert("", 0, values=random_request)
        self.htf_request_list.insert("", tk.END, values=random_request)
        self.if_request_list.selection_remove(self.if_request_list.get_children())
        self.if_request_list.selection_add(self.if_request_list.get_children()[-1])
        self.check_request_lists_empty()

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

        self.if_request_list.drop_selected()
        try:
            if self.root.browser is not None:
                if len(self.root.browser.window_handles) > 0:
                    self.root.browser.execute_script(
                        "alert('WASTT: Request has been dropped by user. Please close this page.');")
        except Exception as e:
            print(f"Error while letting know about dropped request: {e}")

        if len(self.if_request_list.get_children()) > 0:
            self.if_request_list.selection_add(self.if_request_list.get_children()[-1])

        self.check_request_lists_empty()

    def delete_all_requests_in_http_traffic(self):
        """
            Deletes all requests from HTTP Traffic list.
        """
        self.htf_request_list.delete_all()
        self.check_request_lists_empty()

    def add_url_to_scope_dialog(self):
        self.sf_add_url_dialog = ctk.CTkToplevel(self)
        self.sf_add_url_dialog.title("Add URL to Scope")
        self.sf_add_url_dialog.geometry("300x150")
        self.sf_add_url_dialog.attributes("-topmost", True)

        url_label = ctk.CTkLabel(self.sf_add_url_dialog, text="Enter URL:", anchor="w")
        url_label.pack(pady=(10, 5), padx=10, fill="x")

        self.url_entry = ctk.CTkEntry(self.sf_add_url_dialog)
        self.url_entry.pack(pady=(5, 10), padx=10, fill="x")

        submit_button = ctk.CTkButton(self.sf_add_url_dialog, text="Submit", command=self.submit_url)
        submit_button.pack(pady=10)

    def submit_url(self):
        url = self.url_entry.get()
        self.add_url_to_scope(url)
        self.sf_add_url_dialog.destroy()

    def add_url_to_scope(self, url=None):
        """
            Updates filtering in backend logic, sends hostname
            Adds request to scope tab list
        """
        if url is not None: # Temporal if solution to be implementing old backend logic
            self.sf_url_list.insert("", "end", values=(True, url))
            # TODO BACKEND: Sending url inserted to the list to the backend proxy to add it to the filter.
        else:
            # TODO BACKEND: Change backend logic beind it to be only receiving url to the proxy.
            request2 = Request2.from_http_message(self.htf_request_textbox.get_text())
            request = request2.to_request()
            serialized_reqeust = pickle.dumps(request)

            self.sf_url_list.insert("", tk.END, values=(True, request.host))
            self.check_request_lists_empty()

            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((HOST, FRONT_BACK_SCOPEUPDATE_PORT))
                    s.sendall(serialized_reqeust)
            except Exception as e:
                print(f"Error while sendind request to filter: {e}")

    def remove_url_from_scope(self):
        if len(self.sf_url_list.selection()) > 0:
            selected_item = self.sf_url_list.selection()[-1]
            url_to_remove = self.sf_url_list.item(selected_item)['values'][1]
            # print(url_to_remove)
            # TODO BACKEND: Sending url removed from the list to the backend proxy to remove it from the filter.
            if selected_item:
                self.sf_url_list.delete(selected_item)

    def clear_scope(self):
        for item in self.sf_url_list.get_children():
            url_to_remove = self.sf_url_list.item(item)['values'][1]
            # print(url_to_remove)
            # TODO BACKEND: Sending url removed from the list to the backend proxy to remove it from the filter.
            self.sf_url_list.delete(item)

    def send_to_repeater(self, request_textbox, requests_list):
        request_content = request_textbox.get_text()
        request_lines = request_content.split("\n")
        selected_item = requests_list.selection()[0]
        if not any(line.startswith("Host:") for line in request_lines):
            host_string = requests_list.item(selected_item)['values'][0]
            request_lines.insert(1, f"Host: {host_string}")
            request_content = "\n".join(request_lines)

        # print(f"Debug Proxy/Send to repeater:\n{request_content}")
        url = self.htf_request_list.item(selected_item)['values'][-1]
        self.root.repeater_frame.add_request_to_repeater_tab(request_content, url=url)

        if requests_list is self.if_request_list:
            print("Sending from a intercept frame.")
            requests_list.drop_selected()
            if len(requests_list.get_children()) > 0:
                requests_list.selection_add(requests_list.get_children()[-1])
            self.check_request_lists_empty()

    def send_to_intruder(self, request_textbox, requests_list):
        pass
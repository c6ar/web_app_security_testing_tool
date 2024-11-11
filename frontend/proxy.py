from head import *
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from customtkinter import ThemeManager
import pyperclip
import socket
import subprocess
import threading
from PIL import Image
from test_functions import *


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

        self.toggle_button = ctk.CTkButton(self.top_bar, text="Intercept off", command=self.toggle, fg_color="#d1641b")
        self.toggle_button.pack(side=tk.LEFT, padx=15, pady=5)

        self.left_buttons = []

        self.forward_button = ctk.CTkButton(self.top_bar, text=f"Forward", state=tk.DISABLED)
        self.forward_button.pack(side=tk.LEFT, padx=5, pady=15)
        self.left_buttons.append(self.forward_button)
        self.drop_btn = ctk.CTkButton(self.top_bar, text=f"Drop", state=tk.DISABLED, command=self.drop_request)
        self.drop_btn.pack(side=tk.LEFT, padx=5, pady=15)
        self.left_buttons.append(self.drop_btn)
        self.send_to_repeater_btn = ctk.CTkButton(self.top_bar, text=f"Send to repeater", state=tk.DISABLED)
        self.send_to_repeater_btn.pack(side=tk.LEFT, padx=5, pady=15)
        self.left_buttons.append(self.send_to_repeater_btn)
        self.send_to_intruder_btn = ctk.CTkButton(self.top_bar, text=f"Send to intruder", state=tk.DISABLED)
        self.send_to_intruder_btn.pack(side=tk.LEFT, padx=5, pady=15)
        self.left_buttons.append(self.send_to_intruder_btn)
        self.add_random_entry = ctk.CTkButton(self.top_bar, text=f"Add random entry", command=self.add_random_request)
        self.add_random_entry.pack(side=tk.LEFT, padx=5, pady=15)

        self.browser_btn = ctk.CTkButton(self.top_bar, text="Open browser")
        self.browser_btn.pack(side=tk.RIGHT, padx=5, pady=15)
        self.settings_btn = ctk.CTkButton(self.top_bar, text="Proxy settings")
        self.settings_btn.pack(side=tk.RIGHT, padx=5, pady=15)

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

        self.update_thread = threading.Thread(target=self.receive_requests)
        self.update_thread.daemon = True
        self.update_thread.start()

    def toggle(self):
        default_fg_color = ThemeManager.theme["CTkButton"]["fg_color"]
        if self.intercepting:
            self.toggle_button.configure(text="Intercept off", fg_color="#d1641b")
            for btn in self.left_buttons:
                btn.configure(state=tk.DISABLED)
            self.intercepting = False
            print("Turning intercept off.")
        else:
            self.toggle_button.configure(text="Intercept on", fg_color=default_fg_color)
            for btn in self.left_buttons:
                btn.configure(state=tk.NORMAL, fg_color=default_fg_color)
            self.intercepting = True
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
        if self.intercepting:
            self.placeholder_label.configure(text="Intercept is on.")
            self.placeholder_image.configure(image=self.intercept_on_image)
        else:
            self.placeholder_label.configure(text="Intercept is off.")
            self.placeholder_image.configure(image=self.intercept_off_image)

        if len(self.requests_list.get_children()) == 0:
            self.placeholder_frame.lift()
        else:
            self.placeholder_frame.lower()

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

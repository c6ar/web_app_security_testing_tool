from common import *

# TODO Confirm if this is important or needed anywhere, otherwise delete it
i = 0


def change_intercept_state():
    """
        Toggles intercepting at the backend
    """
    flag = "Change state"
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, FRONT_BACK_INTERCEPTBUTTON_PORT))
            serialized_flag = flag.encode("utf-8")
            s.sendall(serialized_flag)
    except Exception as e:
        print(f"Error while sending change intercept state flag: {e}")


class GUIProxy(ctk.CTkFrame):
    """
        GUI for Proxy Tab of WASTT.
        Constist of three sub tabs: HTTP Traffic, Intercept and Scope
    """
    def __init__(self, master, root):
        super().__init__(master)
        super().__init__(master)
        self.process = None
        self.configure(fg_color=color_bg_br, bg_color="transparent", corner_radius=10)
        self.root = root
        self.intercepting = root.intercepting

        """
         > PROXY SUB NAV
        """
        self.intercept_tab = ctk.CTkFrame(self, fg_color="transparent")
        self.http_traffic_tab = ctk.CTkFrame(self, fg_color="transparent")
        self.scope_tab = ctk.CTkFrame(self, fg_color="transparent")
        self.tabs = {
            "HTTP Traffic": self.http_traffic_tab,
            "Intercept": self.intercept_tab,
            "Scope": self.scope_tab,
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
         > HTTP TRAFFIC TAB
        """
        self.htt_top_bar = ctk.CTkFrame(self.http_traffic_tab, height=50, corner_radius=10, fg_color=color_bg, bg_color="transparent")
        self.htt_top_bar.pack(side=tk.TOP, fill=tk.X, pady=(0, 5), padx=5)

        self.htt_add_to_scope_button = ActionButton(
            self.htt_top_bar, text="Add to scope", image=icon_add,
            command=self.st_add_url,
            state=tk.DISABLED)
        self.htt_send_requests_to_repeater_button = ActionButton(
            self.htt_top_bar, text="Send to repeater", image=icon_arrow_up,
            command=lambda: self.send_to_repeater(self.htt_request_textbox, self.htt_request_list),
            state=tk.DISABLED)
        self.htt_send_requests_to_intruder_button = ActionButton(
            self.htt_top_bar, text="Send to intruder", image=icon_arrow_up,
            command=lambda: self.send_to_intruder(self.htt_request_textbox, self.htt_request_list),
            state=tk.DISABLED)
        self.htt_delete_requests_button = ActionButton(
            self.htt_top_bar, text="Delete all requests", image=icon_delete,
            command=self.htt_remove_all_requests_from_list,
            state=tk.DISABLED,
            fg_color=color_acc3, hover_color=color_acc4)
        self.htt_browser_button = ActionButton(
            self.htt_top_bar, text="Open browser", image=icon_browser,
            command=self.root.start_browser_thread)
        self.htt_proxy_button = ActionButton(
            self.htt_top_bar, text="Re-run proxy", image=icon_reload,
            command=self.run_mitmdump)
        self.htt_add_random_entry = ActionButton(
            self.htt_top_bar, text=f"Random request", image=icon_random,
            command=lambda: self.generate_random_request(self.htt_request_list))

        self.htt_top_bar_buttons = [
            self.htt_add_to_scope_button,
            self.htt_send_requests_to_repeater_button,
            self.htt_send_requests_to_intruder_button,
            self.htt_delete_requests_button
        ]
        for ind, button in enumerate(self.htt_top_bar_buttons):
            if ind == 0:
                button.pack(side=tk.LEFT, padx=(10, 5), pady=15)
            else:
                button.pack(side=tk.LEFT, padx=5, pady=15)

        self.htt_add_random_entry.pack(side=tk.LEFT, padx=5, pady=15)
        self.htt_browser_button.pack(side=tk.RIGHT, padx=(5, 10), pady=15)
        self.htt_proxy_button.pack(side=tk.RIGHT, padx=5, pady=15)

        self.htt_paned_window = tk.PanedWindow(self.http_traffic_tab, orient=tk.VERTICAL, sashwidth=10,
                                               background=color_bg_br)
        self.htt_paned_window.pack(fill=tk.BOTH, expand=1, padx=5, pady=5)

        """
         > HTTP TRAFFIC TAB:
         >> Top pane
        """
        self.htt_top_pane = ctk.CTkFrame(self.htt_paned_window, corner_radius=10, fg_color=color_bg, bg_color="transparent")
        self.htt_paned_window.add(self.htt_top_pane, height=350)

        htt_columns = ("Host", "URL", "Method", "Request", "Status code", "Title", "Length", "Response", "RealURL")
        self.htt_request_list = ItemList(self.htt_top_pane, columns=htt_columns, show="headings", style="Treeview")
        self.htt_request_list.bind("<<TreeviewSelect>>", self.htt_show_request_content)
        for col in htt_columns:
            self.htt_request_list.heading(col, text=col)
            self.htt_request_list.column(col, width=100)
        self.htt_request_list.column("Request", width=0, stretch=tk.NO)
        self.htt_request_list.column("Response", width=0, stretch=tk.NO)
        self.htt_request_list.column("RealURL", width=0, stretch=tk.NO)
        self.htt_request_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.htt_request_list_empty = True

        self.htt_request_list.popup_menu.add_command(
            label="Select all",
            command=self.htt_request_list.select_all)
        self.htt_request_list.popup_menu.add_command(
            label="Delete selected",
            command=self.htt_remove_selected_request_from_list())
        self.htt_request_list.popup_menu.add_command(
            label="Delete all",
            command=self.htt_remove_all_requests_from_list)
        self.htt_request_list.popup_menu.add_separator()
        self.htt_request_list.popup_menu.add_command(
            label="Add url to the scope",
            command=lambda: self.from_request_list_to_scope(self.htt_request_list, 0, "add"))
        self.htt_request_list.popup_menu.add_command(
            label="Remove url from the scope",
            command=lambda: self.from_request_list_to_scope(self.htt_request_list, 0, "remove"))
        self.htt_request_list.popup_menu.add_separator()
        self.htt_request_list.popup_menu.add_command(
            label="Send to repeater",
            command=lambda: self.send_to_repeater(self.htt_request_textbox, self.htt_request_list))
        self.htt_request_list.popup_menu.add_command(
            label="Send to intruder",
            command=lambda: self.send_to_intruder(self.htt_request_textbox, self.htt_request_list))
        self.htt_request_list.popup_menu.add_separator()
        self.htt_request_list.popup_menu.add_command(
            label="Copy request content",
            command=lambda: self.htt_request_list.copy_value(3))
        self.htt_request_list.popup_menu.add_command(
            label="Copy response content",
            command=lambda: self.htt_request_list.copy_value(7))
        self.htt_request_list.popup_menu.add_command(
            label="Copy request url",
            command=lambda: self.htt_request_list.copy_value(-1))

        """
         > HTTP TRAFFIC TAB:
         >> Bottom pane
        """
        self.htt_bottom_pane = ctk.CTkFrame(self.htt_paned_window, corner_radius=10, fg_color=color_bg, bg_color="transparent")
        self.htt_paned_window.add(self.htt_bottom_pane)

        self.htt_bottom_pane.grid_columnconfigure(0, weight=1)
        self.htt_bottom_pane.grid_columnconfigure(1, weight=1)
        self.htt_bottom_pane.grid_rowconfigure(0, weight=1)

        self.htt_request_frame = ctk.CTkFrame(self.htt_bottom_pane, fg_color=color_bg)
        self.htt_request_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.htt_request_header = HeaderTitle(self.htt_request_frame, "Request")
        self.htt_request_header.pack(fill=tk.X)

        self.htt_request_textbox = TextBox(self.htt_request_frame, "Select request to display its contents.")
        self.htt_request_textbox.pack(pady=10, padx=10, fill="both", expand=True)

        self.htt_response_frame = ctk.CTkFrame(self.htt_bottom_pane, fg_color=color_bg, bg_color="transparent")
        self.htt_response_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.htt_response_header = HeaderTitle(self.htt_response_frame, "Response")
        self.htt_response_header.pack(fill=tk.X)

        self.htt_response_textbox = TextBox(self.htt_response_frame, "Select request to display its response contents.")
        self.htt_response_textbox.configure(state=tk.DISABLED)
        self.htt_response_textbox.pack(pady=10, padx=10, fill="both", expand=True)

        """
         > INTERCEPT TAB
        """
        # TODO OTHER: Burp's behavior, that when intercept on and filter empty, every request is intercepted?
        self.it_top_bar = ctk.CTkFrame(self.intercept_tab, height=50, corner_radius=10, fg_color=color_bg, bg_color="transparent")
        self.it_top_bar.pack(side=tk.TOP, fill=tk.X, pady=(0, 5), padx=5)

        self.it_toggle_intercept_button = ActionButton(
            self.it_top_bar, text="Intercept off", image=icon_toggle_off, command=self.it_toggle_intercept,
            fg_color=color_green, hover_color=color_green_dk, width=150)
        self.it_drop_button = ActionButton(
            self.it_top_bar, text=f"Drop", image=icon_arrow_down, command=self.it_drop_request)
        self.it_send_to_repeater_button = ActionButton(
            self.it_top_bar, text=f"Send to repeater", command=lambda: self.send_to_repeater(self.it_request_textbox, self.it_request_list),
            state=tk.DISABLED)
        self.it_send_to_intruder_button = ActionButton(
            self.it_top_bar, text=f"Send to intruder", command=lambda: self.send_to_intruder(self.it_request_textbox, self.it_request_list), state=tk.DISABLED)
        self.it_add_random_entry = ActionButton(
            self.it_top_bar, text=f"Random request", image=icon_random,
            command=lambda: self.generate_random_request(self.it_request_list))
        self.it_browser_button = ActionButton(
            self.it_top_bar, text="Open browser", image=icon_browser, command=self.root.start_browser_thread)

        self.it_paned_window = tk.PanedWindow(self.intercept_tab, orient=tk.VERTICAL, sashwidth=10, background=color_bg_br)
        self.it_paned_window.pack(fill=tk.BOTH, expand=1, padx=5, pady=5)

        """
         > INTERCEPT TAB:
         >> Top pane
        """
        self.it_top_pane = ctk.CTkFrame(self.it_paned_window, corner_radius=10, fg_color=color_bg, bg_color="transparent")
        self.it_paned_window.add(self.it_top_pane, height=350)

        it_columns = ("Host", "URL", "Method", "Content", "RealURL")
        self.it_request_list = ItemList(self.it_top_pane, columns=it_columns, show="headings", style="Treeview", selectmode="none")
        self.it_request_list.bind("<<TreeviewSelect>>", self.it_show_request_content)
        for col in it_columns:
            self.it_request_list.heading(col, text=col)
            self.it_request_list.column(col, width=100)
        self.it_request_list.column("Content", width=0, stretch=tk.NO)
        self.it_request_list.column("RealURL", width=0, stretch=tk.NO)
        self.it_request_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.it_request_list_empty = True

        self.it_request_list.popup_menu.add_command(
            label="Drop request",
            command=self.it_drop_request)
        self.it_request_list.popup_menu.add_command(
            label="Forward request",
            command=self.it_forward_request)
        self.it_request_list.popup_menu.add_separator()
        self.it_request_list.popup_menu.add_command(
            label="Add url to the scope",
            command=lambda: self.from_request_list_to_scope(self.it_request_list, 0, "add"))
        self.it_request_list.popup_menu.add_command(
            label="Remove url from the scope",
            command=lambda: self.from_request_list_to_scope(self.it_request_list, 0, "remove"))
        self.it_request_list.popup_menu.add_separator()
        self.it_request_list.popup_menu.add_command(
            label="Send to repeater",
            command=lambda: self.send_to_repeater(self.it_request_textbox, self.it_request_list))
        self.it_request_list.popup_menu.add_command(
            label="Send to intruder",
            command=lambda: self.send_to_intruder(self.it_request_textbox, self.it_request_list))
        self.it_request_list.popup_menu.add_separator()
        self.it_request_list.popup_menu.add_command(
            label="Copy request content",
            command=lambda: self.it_request_list.copy_value(3))
        self.it_request_list.popup_menu.add_command(
            label="Copy request url",
            command=lambda: self.it_request_list.copy_value(-1))

        self.it_intercept_placeholder = ctk.CTkFrame(self.it_top_pane, fg_color="transparent", bg_color="transparent")
        self.it_intercept_placeholder.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.it_placeholder_image = ctk.CTkLabel(self.it_intercept_placeholder, image=intercept_off_image, text="")
        self.it_placeholder_image.pack(pady=5)
        self.it_placeholder_label = ctk.CTkLabel(self.it_intercept_placeholder, text="Intercept is off")
        self.it_placeholder_label.pack(pady=5, expand=True)

        """
         > INTERCEPT TAB:
         >> Bottom pane
        """
        self.it_bottom_pane = ctk.CTkFrame(self.it_paned_window, corner_radius=10, fg_color=color_bg, bg_color="transparent")
        self.it_paned_window.add(self.it_bottom_pane)

        self.it_request_wrapper = ctk.CTkFrame(self.it_bottom_pane, fg_color="transparent", bg_color="transparent")
        self.it_request_wrapper.pack(fill="both", expand=True, padx=10, pady=10)
        self.it_request_wrapper.grid_columnconfigure(0, weight=1)
        self.it_request_wrapper.grid_rowconfigure(0, weight=1)

        self.it_request_wrapper_header = ctk.CTkLabel(self.it_request_wrapper, text="Request",
                                                      font=ctk.CTkFont(family="Calibri", size=24, weight="bold"),
                                                      anchor="w",
                                                      padx=10, pady=10, height=20, fg_color=color_bg)
        self.it_request_wrapper_header.pack(fill=tk.X)

        self.it_request_textbox = TextBox(self.it_request_wrapper, "Select request to display its contents.")
        self.it_request_textbox.pack(pady=10, padx=10, fill="both", expand=True)

        self.it_forward_button = ActionButton(self.it_top_bar, text="Forward", image=icon_arrow_up,
                                              command=self.it_forward_request, state=tk.DISABLED)
        self.it_top_bar_buttons = [
            self.it_drop_button,
            self.it_forward_button,
            self.it_send_to_repeater_button,
            self.it_send_to_intruder_button
        ]
        self.it_toggle_intercept_button.pack(side=tk.LEFT, padx=(10, 15), pady=15)
        for button in self.it_top_bar_buttons:
            button.pack(side=tk.LEFT, padx=5, pady=15)
        self.it_add_random_entry.pack(side=tk.LEFT, padx=5, pady=15)
        self.it_browser_button.pack(side=tk.RIGHT, padx=(5, 10), pady=15)

        """
         > SCOPE TAB:
        """
        self.st_wrapper = ctk.CTkFrame(self.scope_tab, corner_radius=10, fg_color=color_bg, bg_color="transparent")
        self.st_wrapper.pack(fill=tk.X, padx=10, pady=0)

        self.st_header = HeaderTitle(self.st_wrapper, "Scope")
        self.st_header.pack(fill=tk.X, padx=10, pady=0)

        st_columns = ("Enable", "Host prefix")
        self.st_url_list = ItemList(
            self.st_wrapper,
            columns=st_columns,
            show="headings", style="Treeview")
        self.st_url_list.heading("Enable", text="Enable?")
        self.st_url_list.column("Enable", width=25)
        self.st_url_list.heading("Host prefix", text="Host prefix")
        self.st_url_list.pack(side="left", fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.st_url_list_empty = True

        self.st_url_list.popup_menu.add_command(
            label="Select all",
            command=self.st_url_list.select_all)
        self.st_url_list.popup_menu.add_command(
            label="Delete selected",
            command=self.st_remove_url)
        self.st_url_list.popup_menu.add_command(
            label="Delete all",
            command=self.st_clear_all)
        self.st_url_list.popup_menu.add_separator()
        self.st_url_list.popup_menu.add_command(
            label="Copy URL",
            command=lambda: self.st_url_list.copy_value(1))
        
        self.st_buttons = ctk.CTkFrame(self.st_wrapper, fg_color="transparent")
        self.st_buttons.pack(side="right", fill=tk.Y, padx=(0, 10))

        self.st_add_button = ActionButton(
            self.st_buttons, text="Add URL", image=icon_add,
            command=self.st_add_url_dialog
        )
        self.st_add_button.pack(side="top", fill=tk.X, padx=5, pady=10)
        self.st_add_url_dialog = None

        self.st_remove_button = ActionButton(
            self.st_buttons, text="Remove URL", image=icon_delete,
            command=self.st_remove_url
        )
        self.st_remove_button.pack(side="top", fill=tk.X, padx=5, pady=10)

        self.st_clear_button = ActionButton(
            self.st_buttons, text="Clear URLs", image=icon_delete,
            command=self.st_clear_all
        )
        self.st_clear_button.pack(side="top", fill=tk.X, padx=5, pady=10)

        """
         > BACKEND:
         >> Initialising backend for the Proxy tab.
         >> Running mitmproxy at start
        """
        threading.Thread(target=self.it_receive_request, daemon=True).start()
        threading.Thread(target=self.htt_receive_request, daemon=True).start()
        self.deserialized_flow = None

        if not self.process:
            threading.Thread(target=self.run_mitmdump).start()
        self.intercepting = True

        self.switch_tab("HTTP Traffic")

    def run_mitmdump(self):
        """
        Proxy GUI:
            Runs mitmdump proxy script.
        """
        try:
            result = subprocess.run(['taskkill', '/F', '/IM', 'mitmdump.exe', '/T'], capture_output=True, text=True)
            if 'SUCCESS' in result.stdout:
                print("INFO: Previously run mitmdump.exe process has been terminated.")
        except Exception as e:
            print(f"Error terminating previously run mitmdump process: {e}")

        try:
            backend_dir = Path.cwd().parent / "backend"
            proxy_script = backend_dir / "proxy.py"
            command = ["mitmdump", "-s", proxy_script, "--listen-port", "8082"]
            if RUNNING_CONFIG["proxy_console"]:
                command = ["start", "cmd", "/k"] + command
                print("INFO: Starting the HTTP(S) proxy process in new shell terminal window.")
            else:
                print("INFO: Starting the HTTP(S) proxy process.")

            self.process = subprocess.Popen(
                command,
                cwd=backend_dir,
                shell=RUNNING_CONFIG["proxy_console"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            threading.Thread(target=self.read_stdout, daemon=True).start()
            threading.Thread(target=self.read_stderr, daemon=True).start()

            # TODO Confirm if this was important, cuz' the option above lets you get printouts in real time.
            # stdout, stderr = self.process.communicate()
            # if stdout:
            #     print(f"Mitmdump stdout:\n{stdout.decode('utf-8', errors='ignore')}")
            # if stderr:
            #     print(f"Mitmdump stderr:\n{stderr.decode('utf-8', errors='ignore')}")
        except Exception as e:
            print(f"Error while starting the HTTP(S) proxy process: {e}")
        finally:
            self.process = None

    def read_stdout(self):
        for line in iter(self.process.stdout.readline, ''):
            print(f"INFO (mitmdump): {line.strip()}")

    def read_stderr(self):
        for line in iter(self.process.stderr.readline, ''):
            print(f"ERROR (mitmdump): {line.strip()}")

    def switch_tab(self, selected_tab):
        """
        Proxy GUI:
            Switches sub tabs of Proxy tab
        """
        for tab_name, tab in self.tabs.items():
            if tab_name == selected_tab:
                # print(f"Debug Proxy/Tabs: Switching to {tab_name} tab")
                tab.pack(side="top", fill="both", expand=True)
                self.tab_nav_buttons[tab_name].set_selected(True)
            else:
                # print(f"Debug Proxy/Tabs: Hiding {tab_name} tab")
                tab.pack_forget()
                self.tab_nav_buttons[tab_name].set_selected(False)

    def browser_button_update(self):
        """
        Proxy GUI:
            Updates text of the browser button
        """
        if self.root.browser_opened:
            self.it_browser_button.configure(text="Go to browser")
            self.htt_browser_button.configure(text="Go to browser")
        else:
            self.it_browser_button.configure(text="Open browser")
            self.htt_browser_button.configure(text="Open browser")

    def toggle_list_actions(self, item_list, state="normal"):
        """
        Proxy GUI:
            Checks if request lists in proxy GUI are empty and updates action buttons and menu buttons accordingly.
        """
        it_request_list_actions = (
            "Drop request",
            "Forward request",
            "Add url to the scope",
            "Remove url from the scope",
            "Send to repeater",
            "Send to intruder",
            "Copy request content",
            "Copy request url",
        )
        htt_request_list_actions = (
            "Add url to the scope",
            "Remove url from the scope",
            "Send to repeater",
            "Send to intruder",
            "Copy request content",
            "Copy response content",
            "Copy request url",
        )
        st_url_list_actions = (
            "Select all",
            "Delete selected",
            "Delete all",
            "Copy URL"
        )
        if item_list == self.it_request_list:
            actions = it_request_list_actions
            buttons = self.it_top_bar_buttons
            if state == "normal":
                self.it_intercept_placeholder.lower()
            else:
                self.it_intercept_placeholder.lift()
        elif item_list == self.htt_request_list:
            actions = htt_request_list_actions
            buttons = self.htt_top_bar_buttons
        elif item_list == st_url_list_actions:
            actions = st_url_list_actions
            buttons = []
        else:
            actions = []
            buttons = []

        for button in buttons:
            if str(button.cget("state") != state):
                button.configure(state=state)
        # print(f"DEBUG/FRONTEND/PROXY: Toggling buttons to {state} state.")
        for action in actions:
            item_list.popup_menu.entryconfig(action, state=state)

    def from_request_list_to_scope(self, request_list, url_index=0, mode="add"):
        """
        Proxy GUI:
            Adds to / Removes from the scope selected url(s) from the given request list.
        """
        if len(request_list.selection()) > 0:
            for selected_item in request_list.selection():
                url = request_list.item(selected_item)['values'][url_index]
                if mode == "add":
                    # print(f"DEBUG/FRONTEND/PROXY: Adding {url} to the scope")
                    self.st_add_url(url)
                elif mode == "remove":
                    # print(f"DEBUG/FRONTEND/PROXY: Removing {url} from the scope")
                    self.st_remove_url(url)

    def htt_receive_request(self):
        """
        HTTP Traffic Tab:
            Receives tab = [flow.request, flow.response] from backend.proxy.WebRequestInterceptor.send_flow_to_http_trafic_tab
            and runs self.htt_add_request_to_list with received tab
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, BACK_FRONT_HISTORYREQUESTS_PORT))
            s.listen()
            while not self.root.stop_threads:
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
                                self.htt_add_request_to_list(request2, response)
                            else:
                                # print(f"REQUEST ONLY\n\tRequest:\n\t\t{request2}")
                                self.htt_add_request_to_list(request2)
                        except Exception as e:
                            if str(e) != "pickle data was truncated":  # Cannot pickle "cryptography.hazmat.bindings._rust.x509.Certificate"
                                print(f"Error while deserialization request to http traffic: {e}")

    def htt_add_request_to_list(self, req, resp=None):
        """
        HTTP Traffic Tab:
            Adds request to the list.
        """
        real_url = req.url
        host = req.host
        url = req.path
        method = req.method
        request_content = req.return_http_message()
        if resp is None:
            code = ""
            status = ""
            length = 0
            response_content = ""
        else:
            code = resp.status_code
            try:
                status = HTTPStatus(code).phrase
            except ValueError:
                status = ""
            response_content = resp.content.decode('utf-8')
            length = len(response_content)
        values = (host, url, method, request_content, code, status, length, response_content, real_url)

        self.htt_request_list.insert("", tk.END, values=values)

        if len(self.htt_request_list.selection()) == 0:
            self.htt_request_list.selection_add(self.htt_request_list.get_children()[0])

        if self.htt_request_list_empty:
            self.toggle_list_actions(self.htt_request_list, "normal")
            self.htt_request_list_empty = False

    def htt_show_request_content(self, event):
        """
        HTTP Traffic Tab:
            Shows selected HTTP request and its response in the textbox.
        """
        if len(self.htt_request_list.selection()) > 0:
            selected_item = self.htt_request_list.selection()[0]
            request_string = self.htt_request_list.item(selected_item)['values'][3]
            if len(self.htt_request_list.item(selected_item)['values']) == 9:
                response_string = self.htt_request_list.item(selected_item)['values'][7]
            else:
                response_string = "Request got no response."
            self.htt_request_textbox.configure(state=tk.NORMAL, font=self.htt_request_textbox.monoscape_font)
            self.htt_request_textbox.insert_text(request_string)
            self.htt_response_textbox.configure(state=tk.NORMAL, font=self.htt_request_textbox.monoscape_font)
            self.htt_response_textbox.insert_text(response_string)
            self.htt_response_textbox.configure(state=tk.DISABLED)
        else:
            self.htt_request_textbox.configure(state=tk.NORMAL)
            self.htt_request_textbox.insert_text("Select a request to display its contents.")
            self.htt_request_textbox.configure(state=tk.DISABLED, font=self.htt_request_textbox.monoscape_font_italic)
            self.htt_response_textbox.configure(state=tk.NORMAL)
            self.htt_response_textbox.insert_text("Select a request to display contents of its response.")
            self.htt_response_textbox.configure(state=tk.DISABLED, font=self.htt_request_textbox.monoscape_font_italic)

    def htt_remove_selected_request_from_list(self):
        self.htt_request_list.delete_selected()
        if len(self.htt_request_list.get_children()) == 0 and not self.htt_request_list_empty:
            self.toggle_list_actions(self.htt_request_list, "disabled")
            self.htt_request_list_empty = True

    def htt_remove_all_requests_from_list(self):
        self.htt_request_list.delete_all()
        if not self.htt_request_list_empty:
            # print("DEBUG/FRONTEND/PROXY/HTTP TRAFFIC: Deleting all of the requests from the list.")
            self.toggle_list_actions(self.htt_request_list, "disabled")
            self.htt_request_list_empty = True

    def it_toggle_intercept(self):
        """
        Intercept Tab:
            Toggles intercepting
        """
        if self.root.intercepting:
            self.it_toggle_intercept_button.configure(text="Intercept off", image=icon_toggle_off,
                                                      fg_color=color_green, hover_color=color_green_dk)
            self.root.intercepting = False
            self.it_placeholder_label.configure(text="Intercept is off.")
            self.it_placeholder_image.configure(image=intercept_off_image)
            print("Turning intercept off.")
            change_intercept_state()
        else:
            self.it_toggle_intercept_button.configure(text="Intercept on", image=icon_toggle_on,
                                                      fg_color=color_red, hover_color=color_red_dk)
            self.root.intercepting = True
            self.it_placeholder_label.configure(text="Intercept is on.")
            self.it_placeholder_image.configure(image=intercept_on_image)
            print("Turning intercept on.")
            change_intercept_state()

    def it_receive_request(self):
        """
        Intercept Tab:
            Receives request from flow.request and adds it to scope tab.
            and runs self.htt_add_request_to_list with received tab
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, BACK_FRONT_SCOPEREQUESTS_PORT))
            s.listen()

            while not self.root.stop_threads:
                conn, addr = s.accept()

                with conn:
                    serialized_reqeust = conn.recv(4096)
                    if serialized_reqeust:
                        try:
                            deserialized_request = pickle.loads(serialized_reqeust)
                            request2 = Request2.from_request(deserialized_request)
                            self.it_add_request_to_list(request2)
                        except Exception as e:
                            print(f"Error while deserialization recieved in scope: {e}")

    def it_add_request_to_list(self, req):
        """
        Intercept Tab:
            Adds request to the list.
        """
        host = req.host
        url = req.path
        method = req.method
        request_content = req.return_http_message()
        values = (host, url, method, request_content)

        self.it_request_list.insert("", 0, values=values)

        if len(self.it_request_list.selection()) == 0:
            self.it_request_list.selection_add(self.it_request_list.get_children()[0])

        if self.it_request_list_empty:
            self.toggle_list_actions(self.it_request_list, "normal")
            self.it_request_list_empty = False

    def it_show_request_content(self, event):
        """
        Intercept Tab:
            Shows HTTP message of a selected request in the textbox.
        """
        if len(self.it_request_list.selection()) > 0:
            selected_item = self.it_request_list.selection()[0]
            request_string = self.it_request_list.item(selected_item)['values'][3]
            self.it_request_textbox.configure(state=tk.NORMAL, font=self.htt_request_textbox.monoscape_font)
            self.it_request_textbox.insert_text(request_string)
        else:
            self.it_request_textbox.configure(state=tk.NORMAL)
            self.it_request_textbox.insert_text("Select a request to display its contents.")
            self.it_request_textbox.configure(state=tk.DISABLED, font=self.htt_request_textbox.monoscape_font_italic)

    def it_forward_request(self):
        """
        Intercept Tab:
            Sends a request from Intercept tab textbox, request is forwarded to web browser.
        """
        if len(self.it_request_list.selection()) > 0:
            request2 = Request2.from_http_message(self.it_request_textbox.get_text())
            request = request2.to_request()
            serialized_reqeust = pickle.dumps(request)

            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((HOST, FRONT_BACK_FORWARDBUTTON_PORT))
                    s.sendall(serialized_reqeust)
            except Exception as e:
                print(f"Error while sending after Forward button: {e}")

            self.it_request_list.delete_selected()
            if len(self.it_request_list.get_children()) > 0:
                self.it_request_list.selection_add(self.it_request_list.get_children()[-1])

        if len(self.it_request_list.get_children()) == 0:
            if not self.it_request_list_empty:
                self.toggle_list_actions(self.it_request_list, "disabled")
                self.it_request_list_empty = True

    def it_drop_request(self):
        """
        Intercept Tab:
            Removes a request from list in GUI, request is dropped, proxy sends "request dropped info".
        """
        if len(self.it_request_list.selection()) > 0:
            flag = "True"
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((HOST, FRONT_BACK_DROPREQUEST_PORT))
                    serialized_flag = flag.encode("utf-8")
                    s.sendall(serialized_flag)
            except Exception as e:
                print(f"Error while sending flag to kill process: {e}")

            self.it_request_list.delete_selected()
            try:
                if self.root.browser is not None:
                    if len(self.root.browser.window_handles) > 0:
                        self.root.browser.execute_script(
                            "alert('WASTT: Request has been dropped by user. Please close this page.');")
            except Exception as e:
                print(f"Error while letting know about dropped request: {e}")

            if len(self.it_request_list.get_children()) > 0:
                self.it_request_list.selection_add(self.it_request_list.get_children()[-1])

        if len(self.it_request_list.get_children()) == 0:
            if not self.it_request_list_empty:
                self.toggle_list_actions(self.it_request_list, "disabled")
                self.it_request_list_empty = True

    def send_to_repeater(self, request_textbox, requests_list):
        """
        Proxy GUI:
            Sends a request from given textbox and list to the Repeater.
        """
        request_content = request_textbox.get_text()
        selected_item = requests_list.selection()[0]
        hostname = self.htt_request_list.item(selected_item)['values'][-1]
        print(f"DEBUG/FRONTEND/PROXY/Sending to repeater:\n\tHostname:{hostname}\n\tRequest:\n\t\t{request_content}")
        self.root.repeater_tab.add_request_to_repeater_tab(request_content, host=hostname)

    def send_to_intruder(self, request_textbox, requests_list):
        """
        Proxy GUI:
            Sends a request from given textbox and list to the Intruder.
        """
        request_content = request_textbox.get_text()
        selected_item = requests_list.selection()[0]
        hostname = self.htt_request_list.item(selected_item)['values'][-1]
        print(f"DEBUG/FRONTEND/PROXY/Sending to intruder:\n\tHostname:{hostname}\n\tRequest:\n\t\t{request_content}")
        self.root.intruder_tab.add_request_to_intruder_tab(request_content, host=hostname)
        pass

    def generate_random_request(self, request_list):
        """
        Proxy GUI:
            Generates a random fake request and adds it to the request lists.
        """
        url = f"http://{random.choice(['example', 'test', 'check', 'domain'])}.{random.choice(['org', 'com', 'pl', 'eu'])}"
        path = f"/{random.choice(['entry', 'page', '', 'test', 'subpage'])}"
        method = random.choice(["GET", "POST", "PUT", "DELETE"])
        request_content = f'{method} {path} HTTP/1.1\nHost: {url}\nProxy-Connection: keep-alive\nrandom stuff here'
        random_request = [url, path, method, request_content, url]
        if request_list == self.htt_request_list:
            status_code = f"{random.choice(['400','401','402','403','404'])}"
            title = f""
            response_content = f'Some HTTP gibberish here.'
            length = len(response_content)
            random_request = [url, path, method, request_content, status_code, title, length, response_content, url]

        request_list.insert("", tk.END, values=random_request)
        request_list.selection_remove(request_list.get_children())
        request_list.selection_add(request_list.get_children()[-1])

        if request_list == self.it_request_list:
            if self.it_request_list_empty:
                self.toggle_list_actions(self.it_request_list, "normal")
                self.it_request_list_empty = False
        elif request_list == self.htt_request_list:
            if self.htt_request_list_empty:
                self.toggle_list_actions(self.htt_request_list, "normal")
                self.htt_request_list_empty = False

    def st_add_url_dialog(self):
        """
        Scope Tab:
            Opens an Add custom URL to Scope dialog window.
        """
        self.st_add_url_dialog = ctk.CTkToplevel(self)
        self.st_add_url_dialog.title("Add URL to Scope")
        self.st_add_url_dialog.geometry("300x150")
        self.st_add_url_dialog.attributes("-topmost", True)
        center_window(self.root, self.st_add_url_dialog, 300, 150)

        url_label = ctk.CTkLabel(self.st_add_url_dialog, text="Enter URL:", anchor="w")
        url_label.pack(pady=(10, 5), padx=10, fill="x")

        url_entry = TextEntry(self.st_add_url_dialog)
        url_entry.pack(pady=(5, 10), padx=10, fill="x")
        url_entry.bind("<Return>", lambda event: self.st_submit_url(url_entry.get()))

        submit_button = ctk.CTkButton(self.st_add_url_dialog, text="Submit", command=lambda: self.st_submit_url(url_entry.get()))
        submit_button.pack(pady=10)
        submit_button.bind("<Return>", lambda event: self.st_submit_url(url_entry.get()))

    def st_submit_url(self, url):
        """
        Scope Tab:
            Submit the provided custom URL in the dialog.
        """
        if len(url) > 0 and re.match(r"^[a-zA-Z0-9-]+\.[a-zA-Z]{1,3}$", url):
            self.st_add_url(url)
            self.st_add_url_dialog.destroy()

    def st_add_url(self, hostname=None):
        """
        Scope Tab:
            Updates filtering in backend logic, sends hostname
            Adds request to scope tab list
            If hostname is not given, it gets it from the last selected item in the HTTP Traffic.
        """
        if hostname is None:
            if len(self.htt_request_list.selection()) > 0:
                selected_item = self.htt_request_list.selection()[-1]
                hostname = self.htt_request_list.item(selected_item)['values'][0]
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                data_to_send = ("add", hostname)
                serialized_data = pickle.dumps(data_to_send)
                s.connect((HOST, FRONT_BACK_SCOPEUPDATE_PORT))
                s.sendall(serialized_data)
                self.st_url_list.insert("", tk.END, values=(True, extract_domain(hostname)))
        except Exception as e:
            print(f"Error while sendind request to filter: {e}")

        if self.st_url_list_empty:
            self.toggle_list_actions(self.st_url_list, "normal")
            self.st_url_list_empty = False

    def st_remove_url(self, hostname_to_remove=None):
        """
        Scope Tab:
            If hostname_to_remove is not provided as a parameter, it removes hostnames selected in the Scope Tab's list.
            If hostname_to_remove is provided, it looks for it in the Scope Tab's URL List to remove it.
            Either way, it updates filtering in the backend logic, sends hostname
        """
        hostnames_to_remove = set()
        if hostname_to_remove is None:
            if len(self.st_url_list.selection()) > 0:
                for selected_item in  self.st_url_list.selection():
                    hostnames_to_remove.add(self.st_url_list.item(selected_item)['values'][1])
                    self.st_url_list.delete(selected_item)
        else:
            hostnames_to_remove.add(hostname_to_remove)
            for item in self.st_url_list.get_children():
                if hostname_to_remove == self.st_url_list.item(item)['values'][1]:
                    self.st_url_list.delete(item)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                data_to_send = ("remove", *hostnames_to_remove)
                serialized_data = pickle.dumps(data_to_send)
                s.connect((HOST, FRONT_BACK_SCOPEUPDATE_PORT))
                s.sendall(serialized_data)
        except Exception as e:
            print(f"Error while sendind request to filter: {e}")

        if len(self.st_url_list.get_children()) == 0 and not self.st_url_list_empty:
            self.toggle_list_actions(self.st_url_list, "disabled")
            self.st_url_list_empty = True

    def st_clear_all(self):
        """
        Scope Tab:
            Clears all Scope Tab URLs.
            Updates backend filtering.
            With empty filter Intercept should be intercepting any request.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                data_to_send = ("clear", "")
                serialized_data = pickle.dumps(data_to_send)
                s.connect((HOST, FRONT_BACK_SCOPEUPDATE_PORT))
                s.sendall(serialized_data)
                for item in self.st_url_list.get_children():
                    self.st_url_list.delete(item)
        except Exception as e:
            print(f"Error while sendind request to filter: {e}")

        if not self.st_url_list_empty:
            self.toggle_list_actions(self.st_url_list, "disabled")
            self.st_url_list_empty = True

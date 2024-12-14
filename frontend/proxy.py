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
        self.process = None
        self.configure(fg_color="transparent")
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
            fg_color=color_acc, hover_color=color_acc2)
        self.htt_send_requests_to_repeater_button = ActionButton(
            self.htt_top_bar, text="Send to repeater", image=icon_arrow_up,
            command=lambda: self.send_to_repeater(self.htt_request_textbox, self.htt_request_list),
            fg_color=color_acc, hover_color=color_acc2)
        self.htt_send_requests_to_intruder_button = ActionButton(
            self.htt_top_bar, text="Send to intruder", image=icon_arrow_up,
            command=lambda: self.send_to_intruder(self.htt_request_textbox, self.htt_request_list),
            fg_color=color_acc, hover_color=color_acc2)
        self.htt_delete_requests_button = ActionButton(
            self.htt_top_bar, text="Delete all requests", image=icon_delete,
            command=lambda: (self.htt_request_list.delete_all(), self.check_request_lists_empty()),
            fg_color=color_acc3, hover_color=color_acc4)
        self.htt_browser_button = ActionButton(
            self.htt_top_bar, text="Open browser", image=icon_browser,
            command=self.root.start_browser_thread)
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

        self.htt_request_list.popup_menu.add_command(
            label="Select all",
            command=self.htt_request_list.select_all)
        self.htt_request_list.popup_menu.add_command(
            label="Delete selected",
            command=lambda: (self.htt_request_list.delete_selected(), self.check_request_lists_empty()))
        self.htt_request_list.popup_menu.add_command(
            label="Delete all",
            command=lambda: (self.htt_request_list.delete_all(), self.check_request_lists_empty()))
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
        # TODO FRONTEND/BACKEND: Can we have intercepting like in Burp? - When scope empty then intercepting anything, else we intercept stuff from scope.
        self.it_top_bar = ctk.CTkFrame(self.intercept_tab, height=50, corner_radius=10, fg_color=color_bg, bg_color="transparent")
        self.it_top_bar.pack(side=tk.TOP, fill=tk.X, pady=(0, 5), padx=5)

        self.it_toggle_intercept_button = ActionButton(
            self.it_top_bar, text="Intercept off", image=icon_toggle_off, command=self.it_toggle_intercept,
            fg_color=color_green, hover_color=color_green_dk)
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
        self.it_request_list = ItemList(self.it_top_pane, columns=it_columns, show="headings", style="Treeview",
                                           selectmode="none")
        self.it_request_list.bind("<<TreeviewSelect>>", self.it_show_request_content)
        for col in it_columns:
            self.it_request_list.heading(col, text=col)
            self.it_request_list.column(col, width=100)
        self.it_request_list.column("Content", width=0, stretch=tk.NO)
        self.it_request_list.column("RealURL", width=0, stretch=tk.NO)
        self.it_request_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

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

        self.it_forward_button = ActionButton(self.it_top_bar, text=f"Forward", image=icon_arrow_up, state=tk.DISABLED,
                                              compound="left", corner_radius=32, command=self.it_forward_request)
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
            show="headings", style="Treeview", selectmode="browse")
        self.st_url_list.heading("Enable", text="Enable?")
        self.st_url_list.column("Enable", width=25)
        self.st_url_list.heading("Host prefix", text="Host prefix")
        self.st_url_list.pack(side="left", fill=tk.BOTH, expand=True, padx=5, pady=5)

        # TODO FRONTEND: Update the commands for these pop menu once BACKEND logic implemented.
        self.st_url_list.popup_menu.add_command(
            label="Select all",
            command=self.st_url_list.select_all)
        self.st_url_list.popup_menu.add_command(
            label="Delete selected",
            command=lambda: (self.st_url_list.delete_selected(), self.check_request_lists_empty()))
        self.st_url_list.popup_menu.add_command(
            label="Delete all",
            command=lambda: (self.st_url_list.delete_all(), self.check_request_lists_empty()))
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
        self.update_thread_scope = threading.Thread(target=self.it_receive_request)
        self.update_thread_scope.daemon = True
        self.update_thread_scope.start()
        self.update_thread_traffic = threading.Thread(target=self.htt_receive_request)
        self.update_thread_traffic.daemon = True
        self.update_thread_traffic.start()
        self.deserialized_flow = None

        if not self.process:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.join(current_dir, "..", "backend")
            proxy_script = os.path.join(backend_dir, "proxy.py")
            command = ["mitmdump", "-s", proxy_script, "--listen-port", "8082"]

            threading.Thread(target=self.run_mitmdump, args=(command, backend_dir)).start()
        self.intercepting = True

        self.switch_tab("HTTP Traffic")
        self.check_request_lists_empty()

    def run_mitmdump(self, command, cwd):
        """
        Proxy GUI:
            Runs mitmdump proxy script.
        """
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

    def check_request_lists_empty(self):
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
        if len(self.it_request_list.get_children()) == 0:
            self.it_intercept_placeholder.lift()
            for button in self.it_top_bar_buttons:
                button.configure(state=tk.DISABLED)
            for action in it_request_list_actions:
                self.it_request_list.popup_menu.entryconfig(action, state=tk.DISABLED)
        else:
            self.it_intercept_placeholder.lower()
            for button in self.it_top_bar_buttons:
                button.configure(state=tk.NORMAL)
            for action in it_request_list_actions:
                self.it_request_list.popup_menu.entryconfig(action, state=tk.NORMAL)

        htt_request_list_actions = (
            "Add url to the scope",
            "Remove url from the scope",
            "Send to repeater",
            "Send to intruder",
            "Copy request content",
            "Copy response content",
            "Copy request url",
        )
        if len(self.htt_request_list.get_children()) == 0:
            for button in self.htt_top_bar_buttons:
                button.configure(state=tk.DISABLED)
            for action in htt_request_list_actions:
                self.htt_request_list.popup_menu.entryconfig(action, state=tk.DISABLED)
        else:
            for button in self.htt_top_bar_buttons:
                button.configure(state=tk.NORMAL)
            for action in htt_request_list_actions:
                self.htt_request_list.popup_menu.entryconfig(action, state=tk.NORMAL)

        st_url_list_actions = (
            "Select all",
            "Delete selected",
            "Delete all",
            "Copy URL"
        )
        if len(self.st_url_list.get_children()) == 0:
            for action in st_url_list_actions:
                self.st_url_list.popup_menu.entryconfig(action, state=tk.DISABLED)
        else:
            for action in st_url_list_actions:
                self.st_url_list.popup_menu.entryconfig(action, state=tk.NORMAL)

    def from_request_list_to_scope(self, request_list, url_index=0, mode="add"):
        """
        Proxy GUI:
            Adds to / Removes from the scope selected url(s) from the given request list.
        """
        if len(request_list.selection()) > 0:
            for selected_item in request_list.selection():
                url = request_list.item(selected_item)['values'][url_index]
                if mode == "add":
                    print(f"DEBUG/FRONTEND/PROXY: Adding {url} to the scope")
                    self.st_add_url(url)
                elif mode =="remove":
                    print(f"DEBUG/FRONTEND/PROXY: Removing {url} from the scope")
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
                                self.htt_add_request_to_list(request2, response)
                            else:
                                # print(f"REQUEST ONLY\n\tRequest:\n\t\t{request2}")
                                self.htt_add_request_to_list(request2)
                            self.check_request_lists_empty()
                        except Exception as e:
                            if str(e) != "pickle data was truncated":  #cannot pickle "cryptography.hazmat.bindings._rust.x509.Certificate"
                                print(f"Error while deserialization request to http traffic: {e}")

    def htt_add_request_to_list(self, req, resp=None):
        """
        HTTP Traffic Tab:
            Adds request to the list.
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

        self.htt_request_list.insert("", tk.END, values=values)

        if len(self.htt_request_list.selection()) == 0:
            self.htt_request_list.selection_add(self.htt_request_list.get_children()[0])

    def htt_show_request_content(self, event):
        """
        HTTP Traffic Tab:
            Shows selected HTTP request and its response in the textbox.
        """
        if len(self.htt_request_list.selection()) > 0:
            selected_item = self.htt_request_list.selection()[0]
            request_string = self.htt_request_list.item(selected_item)['values'][3]
            if len(self.htt_request_list.item(selected_item)['values']) == 8:
                response_string = self.htt_request_list.item(selected_item)['values'][7]
            elif len(self.htt_request_list.item(selected_item)['values']) == 5:
                response_string = self.htt_request_list.item(selected_item)['values'][5]
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
        self.check_request_lists_empty()

    def it_receive_request(self):
        """
        Intercept Tab:
            Receives request from flow.request and adds it to scope tab.
            and runs self.htt_add_request_to_list with received tab
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
                            self.it_add_request_to_list(request2)
                        except Exception as e:
                            print(f"Error while deserialization recieved in scope: {e}")

                        self.check_request_lists_empty()

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
        self.check_request_lists_empty()

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

        self.check_request_lists_empty()

    def send_to_repeater(self, request_textbox, requests_list):
        """
        Proxy GUI:
            Sends a request from given textbox and list to the Repeater.
        """
        request_content = request_textbox.get_text()
        request_lines = request_content.split("\n")
        selected_item = requests_list.selection()[0]
        if not any(line.startswith("Host:") for line in request_lines):
            host_string = requests_list.item(selected_item)['values'][0]
            request_lines.insert(1, f"Host: {host_string}")
            request_content = "\n".join(request_lines)

        # print(f"Debug Proxy/Send to repeater:\n{request_content}")
        url = self.htt_request_list.item(selected_item)['values'][-1]
        self.root.repeater_tab.add_request_to_repeater_tab(request_content, url=url)

        if requests_list is self.it_request_list:
            # print("DEBUG/FRONTEND/Proxy: Sending from an intercept frame.")
            requests_list.delete_selected()
            if len(requests_list.get_children()) > 0:
                requests_list.selection_add(requests_list.get_children()[-1])
            self.check_request_lists_empty()

    def send_to_intruder(self, request_textbox, requests_list):
        """
        Proxy GUI:
            Sends a request from given textbox and list to the Intruder.
        """
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

        self.check_request_lists_empty()

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

    def st_add_url(self, url=None):
        """
        Scope Tab:
            Updates filtering in backend logic, sends hostname
            Adds request to scope tab list
        """
        if url is not None: # Temporal if solution to be implementing old backend logic
            self.st_url_list.insert("", "end", values=(True, url))
        else:
            # TODO BACKEND: Change backend logic behind it to be only receiving hostname for the filter.
            request2 = Request2.from_http_message(self.htt_request_textbox.get_text())
            request = request2.to_request()
            serialized_reqeust = pickle.dumps(request)

            self.st_url_list.insert("", tk.END, values=(True, request.host))
            self.check_request_lists_empty()

            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((HOST, FRONT_BACK_SCOPEUPDATE_PORT))
                    s.sendall(serialized_reqeust)
            except Exception as e:
                print(f"Error while sendind request to filter: {e}")

        self.check_request_lists_empty()

    def st_remove_url(self, url_to_remove=None):
        """
        Scope Tab:
            If url_to_remove is not provided as a parameter, it removes urls selected in the Scope Tab's URL list.
            If url_to_remove is provided, it looks for it in the Scope Tab's URL List to remove it.
            Either way, it updates filtering in the backend logic, sends hostname
        """
        if url_to_remove is None:
            if len(self.st_url_list.selection()) > 0:
                for selected_item in self.st_url_list.selection():
                    url_to_remove = self.st_url_list.item(selected_item)['values'][1]
                    if selected_item:
                        self.st_url_list.delete(selected_item)
        else:
            for item in self.st_url_list.get_children():
                if url_to_remove == self.st_url_list.item(item)['values'][1]:
                    self.st_url_list.delete(item)

        self.check_request_lists_empty()

        # print(url_to_remove)
        # TODO BACKEND: Sending url_to_remove to the backend proxy to remove it from the filter.

    def st_clear_all(self):
        """
        Scope Tab:
            Clears all Scope Tab URLs.
            Updates backend filtering.
            With empty filter Intercept should be intercepting any request.
        """
        for item in self.st_url_list.get_children():
            url_to_remove = self.st_url_list.item(item)['values'][1]
            # print(url_to_remove)
            # TODO BACKEND: Sending url_to_remove to the backend proxy to remove it from the filter.
            self.st_url_list.delete(item)

        self.check_request_lists_empty()

from frontend.common import *


# noinspection PyShadowingNames
def log_flow(request: Request2, response: Response = None) -> None:
    """
    HTTP Traffic Tab:
        Logs the HTTP flow to a specific log file for tracking and analysis.

    Parameters:
        request: Request2 - request
        response: Response - response, optional
    """
    logs_location = RUNNING_CONFIG.get("logs_location", "")
    if not logs_location:
        app_dir = Path(__file__).resolve().parent.parent
        logs_location = app_dir / "logs"
    else:
        logs_location = Path(logs_location)
    logs_path = Path(logs_location / "http_traffic")
    logs_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    log_file = logs_path / f"traffic_flow-{today}.log"

    host = request.host
    port = request.port
    scheme = request.scheme
    request_content = request.return_http_message()

    with log_file.open("a", encoding="utf-8", errors="replace") as file:
        file.write(f"[{timestamp}] Intercepted request to {scheme}://{host}:{port}\n{request_content}")

    if response is not None:
        code = response.status_code
        try:
            from http import HTTPStatus
            status = HTTPStatus(code).phrase
        except ValueError:
            status = ""

        try:
            response_content = response.content.decode("utf-8", errors="replace")
        except (AttributeError, UnicodeDecodeError):
            response_content = str(response.content)

        with log_file.open("a", encoding="utf-8", errors="replace") as file:
            file.write(f"[{timestamp}] Response from {scheme}://{host}:{port} : {code} - {status}\n"
                       f"{response_content}")


class HTTPTrafficTab(ctk.CTkFrame):
    """
    WASTT/Proxy/HTTPTraffic:
        Represents a custom GUI tab to display and manage HTTP traffic details.

        This class serves as a GUI module for hosting a user interface designed to monitor, display, and interact
        with HTTP requests and responses. It acts as an intermediary between the backend HTTP proxy and the user,
        offering functionalities like filtering, sorting, and reviewing captured HTTP traffic. The class displays
        captured requests and responses in a table and provides various controls for managing captured data,
        invoking specific functions, or viewing detailed information.
    """
    def __init__(self, master, root):
        super().__init__(master)
        self.configure(
            fg_color="transparent",
            bg_color="transparent",
            corner_radius=10
        )
        self.wastt = root
        self.proxy = master

        # ================================================
        # Top Bar
        # ================================================
        top_bar = DarkBox(self, height=50)
        top_bar.pack(side=tk.TOP, fill=tk.X, pady=(0, 5), padx=10)

        add_to_scope_button = ActionButton(
            top_bar,
            text="Add to scope",
            # image=icon_add,
            command=lambda: self.update_scope(),
            state=tk.DISABLED
        )
        send_requests_to_intruder_button = ActionButton(
            top_bar,
            text="Send to intruder",
            # image=icon_arrow_up,
            command=lambda: self.send_request("intruder"),
            state=tk.DISABLED
        )
        send_requests_to_repeater_button = ActionButton(
            top_bar, text="Send to repeater",
            # image=icon_arrow_up,
            command=lambda: self.send_request("repeater"),
            state=tk.DISABLED
        )
        self.filter_list_button = ActionButton(
            top_bar, text=f"Filter with scope",
            # image=icon_list,
            command=self.filter_list_with_scope,
            state=tk.DISABLED
        )
        delete_requests_button = ActionButton(
            top_bar, text="Delete all requests",
            # image=icon_delete,
            command=self.remove_all_requests_from_list,
            state=tk.DISABLED,
            fg_color=color_acc3,
            hover_color=color_acc4
        )
        add_random_entry = ActionButton(
            top_bar,
            text=f"Random request",
            image=icon_random,
            command=self.generate_random_request
        )
        browser_button = ActionButton(
            top_bar,
            text="Open browser",
            image=icon_browser,
            command=self.wastt.start_browser_thread
        )
        proxy_button = ActionButton(
            top_bar,
            text="Re-run proxy",
            image=icon_reload,
            command=self.proxy.run_mitmdump
        )
        info_button = InfoButton(
            top_bar,
            self,
            "http://localhost:8080/proxy.html#http_traffic"
        )
        info_button.pack(side=tk.RIGHT, padx=5, pady=0)

        self.request_list_filtered = False

        self.top_bar_buttons = [
            add_to_scope_button,
            send_requests_to_intruder_button,
            send_requests_to_repeater_button,
            self.filter_list_button,
            delete_requests_button
        ]
        for i, button in enumerate(self.top_bar_buttons):
            button.pack(side=tk.LEFT, padx=(15 if i == 0 else 5, 5), pady=15)

        browser_button.pack(side=tk.RIGHT, padx=(5, 10), pady=15)

        if RUNNING_CONFIG["debug_mode"]:
            add_random_entry.pack(side=tk.LEFT, padx=5, pady=15)
            proxy_button.pack(side=tk.RIGHT, padx=5, pady=15)

        self.paned_window = tk.PanedWindow(
            self,
            orient=tk.VERTICAL,
            sashwidth=10,
            background=color_bg_br
        )
        self.paned_window.pack(fill=tk.BOTH, expand=1, padx=10, pady=(5, 10))

        # ================================================
        # Request List
        # ================================================
        top_pane = DarkBox(self.paned_window)
        self.paned_window.add(top_pane, height=350)

        columns = ("Host", "URL", "Method", "Request", "Status code", "Title", "Length", "Response", "RealURL")
        self.request_list = ItemList(
            top_pane,
            columns=columns,
            show="headings",
            style="Treeview"
        )
        self.request_list_backup = ItemList(top_pane, columns=columns)
        self.request_list.bind("<<TreeviewSelect>>", self.show_request_content)
        self.request_list.bind("<Button-1>", self.on_click_outside_item)
        for col in columns:
            self.request_list.heading(col, text=col, command=lambda c=col: self.sort_by_column(c, False))
            self.request_list.column(col, width=100)
        self.request_list.column("Request", width=0, stretch=tk.NO)
        self.request_list.column("Response", width=0, stretch=tk.NO)
        self.request_list.column("RealURL", width=0, stretch=tk.NO)
        self.request_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.request_list_empty = True

        self.request_list.popup_menu.add_command(
            label="Select all",
            command=self.request_list.select_all
        )
        self.request_list.popup_menu.add_command(
            label="Delete selected",
            command=self.remove_selected_request_from_list
        )
        self.request_list.popup_menu.add_command(
            label="Delete all",
            command=self.remove_all_requests_from_list
        )
        self.request_list.popup_menu.add_separator()
        self.request_list.popup_menu.add_command(
            label="Add url to the scope",
            command=lambda: self.update_scope("add"),
            state=tk.DISABLED
        )
        self.request_list.popup_menu.add_command(
            label="Remove url from the scope",
            command=lambda: self.update_scope("remove"),
            state=tk.DISABLED
        )
        self.request_list.popup_menu.add_separator()
        self.request_list.popup_menu.add_command(
            label="Send to intruder",
            command=lambda: self.send_request("intruder"),
            state=tk.DISABLED
        )
        self.request_list.popup_menu.add_command(
            label="Send to repeater",
            command=lambda: self.send_request("repeater"),
            state=tk.DISABLED
        )
        self.request_list.popup_menu.add_separator()
        self.request_list.popup_menu.add_command(
            label="Copy request content",
            command=lambda: self.request_list.copy_value(3),
            state=tk.DISABLED
        )
        self.request_list.popup_menu.add_command(
            label="Copy response content",
            command=lambda: self.request_list.copy_value(7),
            state=tk.DISABLED
        )
        self.request_list.popup_menu.add_command(
            label="Copy request url",
            command=lambda: self.request_list.copy_value(-1),
            state=tk.DISABLED
        )

        # ================================================
        # Request and response bottom pane
        # ================================================
        self.bottom_pane = DarkBox(self.paned_window)

        self.bottom_pane.grid_columnconfigure(0, weight=1)
        self.bottom_pane.grid_columnconfigure(1, weight=1)
        self.bottom_pane.grid_rowconfigure(0, weight=1)

        request_frame = ctk.CTkFrame(self.bottom_pane, fg_color=color_bg)
        request_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        request_header = HeaderTitle(request_frame, "Request")
        request_header.pack(fill=tk.X)

        self.request_textbox = TextBox(request_frame, "Select request to display its contents.")
        self.request_textbox.pack(pady=10, padx=10, fill="both", expand=True)

        response_frame = ctk.CTkFrame(self.bottom_pane, fg_color=color_bg, bg_color="transparent")
        response_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        response_header = HeaderTitle(response_frame, "Response")
        response_header.pack(fill=tk.X)

        self.response_textbox = TextBox(response_frame, "Select request to display its response contents.")
        self.response_textbox.configure(state=tk.DISABLED)
        self.response_textbox.pack(pady=10, padx=10, fill="both", expand=True)

        self.response_hostname = ""
        response_render_button = ActionButton(
            response_frame,
            text="Show response render",
            command=lambda: show_response_view(self.wastt, self.response_hostname, self.response_textbox.get_text())
        )
        response_render_button.place(relx=1, rely=0, anchor=tk.NE, x=-10, y=10)

    def receive_request(self) -> None:
        """
        WASTT/Proxy/HTTPTraffic:
            Receives tab = [flow.request, flow.response] from backend.proxy.WebRequestInterceptor.send_flow_to_http_trafic_tab
            and runs self.htt_add_request_to_list with received tab
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((RUNNING_CONFIG["proxy_host_address"],
                    RUNNING_CONFIG["back_front_request_to_traffic_port"]))
            s.listen()
            while not self.wastt.stop_threads:
                conn, addr = s.accept()
                with conn:
                    serialized_flow = conn.recv(4096)
                    if serialized_flow:
                        try:
                            flow_tab = pickle.loads(serialized_flow)
                            if isinstance(flow_tab, list):
                                request2 = Request2.from_request(flow_tab[0])
                                response = flow_tab[1] if len(flow_tab) == 2 else None

                            elif isinstance(flow_tab, Request):
                                request2 = Request2.from_request(flow_tab)
                                response = None

                            self.add_request_to_list(request2, response)
                            if RUNNING_CONFIG["log_http_traffic_flow"]:
                                log_flow(request2, response)

                        except Exception as e:
                            # Cannot pickle "cryptography.hazmat.bindings._rust.x509.Certificate"
                            if str(e) != "pickle data was truncated":
                                print(f"[ERROR] Failure while deserialization request to http traffic: {e}")

    def add_request_to_list(self, req: Request2, resp: Response = None) -> None:
        """
        WASTT/Proxy/HTTPTraffic:
            Adds request to the list.

        Parameters:
            req: Request2 - request
            resp: Response - response, optional
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
                from http import HTTPStatus
                status = HTTPStatus(code).phrase
            except ValueError:
                status = ""

            try:
                response_content = resp.content.decode("utf-8", errors="replace")
            except AttributeError:
                response_content = str(resp.content)

            length = len(response_content)
        values = (host, url, method, request_content, code, status, length, response_content, real_url)

        self.request_list.insert("", tk.END, values=values)
        self.request_list_backup.insert("", tk.END, values=values)

        if len(self.request_list.selection()) == 0:
            self.request_list.selection_add(self.request_list.get_children()[0])

        if self.request_list_empty:
            self.toggle_list_actions("normal")
            self.request_list_empty = False

    def on_click_outside_item(self, _event) -> None:
        """
        WASTT/Proxy/HTTPTraffic:
            Checks if clicked outside the requests list item to unselect all.
        """
        region = self.request_list.identify_region(_event.x, _event.y)
        if region != "cell":
            self.request_list.selection_remove(self.request_list.selection())
            self.show_request_content(_event)

    def show_request_content(self, _event) -> None:
        """
        WASTT/Proxy/HTTPTraffic:
            Shows selected HTTP request and its response in the textbox.
        """
        if len(self.request_list.selection()) > 0:
            self.paned_window.add(self.bottom_pane)
            selected_item = self.request_list.selection()[0]
            request_string = self.request_list.item(selected_item)['values'][3]
            response_string = self.request_list.item(selected_item)['values'][-2]
            self.response_hostname = self.request_list.item(selected_item)['values'][0]
            self.request_textbox.configure(state=tk.NORMAL, font=self.request_textbox.monoscape_font)
            self.request_textbox.insert_text(request_string)
            self.response_textbox.configure(state=tk.NORMAL, font=self.request_textbox.monoscape_font)
            self.response_textbox.insert_text(response_string)
            self.response_textbox.configure(state=tk.DISABLED)
        else:
            self.paned_window.remove(self.bottom_pane)
            self.request_textbox.configure(state=tk.NORMAL)
            self.request_textbox.insert_text("Select a request to display its contents.")
            self.request_textbox.configure(state=tk.DISABLED, font=self.request_textbox.monoscape_font_italic)
            self.response_textbox.configure(state=tk.NORMAL)
            self.response_textbox.insert_text("Select a request to display contents of its response.")
            self.response_textbox.configure(state=tk.DISABLED, font=self.request_textbox.monoscape_font_italic)

    def update_scope(self, mode: str = "add") -> None:
        """
        WASTT/Proxy/HTTPTraffic:
            Adds to / Removes from the scope selected url(s) from the given request list.

        Parameters:
            mode: str - 'add' or 'remove', default 'add'
        """
        if len(self.request_list.selection()) > 0:
            hostnames = set()

            for item in self.request_list.selection():
                hostnames.add(self.request_list.item(item)['values'][0])

            if len(hostnames) > 0:
                self.proxy.update_scope(mode, hostnames)
                dprint(f"[DEBUG] /FRONTEND/PROXY: {mode.capitalize().replace('e', '')}ing {hostnames} to the scope")

    def send_request(self, dest: str) -> None:
        """
        WASTT/Proxy/HTTPTraffic:
            It directly sends the first selected request to the respective app module: Intruder/Repeater.

        Parameters:
            dest: str - module name
        """
        request_content = self.request_textbox.get_text()
        hostname_url = ""
        if len(self.request_list.selection()[0]) > 0:
            selected_item = self.request_list.selection()[0]
            hostname_url = self.request_list.item(selected_item)['values'][-1]
        if dest == "intruder":
            self.wastt.intruder.add_request_to_intruder_tab(content=request_content, host=hostname_url)
        elif dest == "repeater":
            self.wastt.repeater.add_request_to_repeater_tab(content=request_content, host=hostname_url)

    def remove_selected_request_from_list(self) -> None:
        """
        WASTT/Proxy/HTTPTraffic:
            Removes selected request from the list.
        """
        for item in self.request_list.selection():
            self.request_list_backup.delete(item)
            dprint(f"[DEBUG] FRONTEND/PROXY/HTTP TRAFFIC: Deleted {item} from backup list")
        self.request_list.delete_selected()
        if len(self.request_list.get_children()) == 0 and not self.request_list_empty:
            self.toggle_list_actions(tk.DISABLED)
            self.request_list_empty = True

    def remove_all_requests_from_list(self) -> None:
        """
        WASTT/Proxy/HTTPTraffic:
            Removes all requests from the list.
        """
        self.request_list.delete_all()
        self.request_list_backup.delete_all()
        if not self.request_list_empty:
            dprint("[DEBUG] FRONTEND/PROXY/HTTP TRAFFIC: Deleting all the requests from the list.")
            self.toggle_list_actions(tk.DISABLED)
            self.request_list_empty = True

    def sort_by_column(self, col: str, reverse: bool) -> None:
        """
        WASTT/Proxy/HTTPTraffic:
            Sorts the list by column which header was clicked.

        Parametetrs:
            col: str - column header name
            reverse: bool - reverse order
        """
        index_list = [(self.request_list.set(k, col), k) for k in self.request_list.get_children('')]
        index_list.sort(reverse=reverse)

        for index, (val, k) in enumerate(index_list):
            self.request_list.move(k, '', index)

        self.request_list.heading(col, command=lambda: self.sort_by_column(col, not reverse))

    def filter_list_with_scope(self) -> None:
        """
        WASTT/Proxy/HTTPTraffic:
            Toggles filtering of the list using Web Request Interceptor's scope.
        """
        if self.request_list_filtered:
            self.request_list.delete_all()

            for item in self.request_list_backup.get_children():
                values = list(self.request_list_backup.item(item)['values'])
                self.request_list.insert("", tk.END, values=values)

            self.request_list_filtered = False
        elif len(self.proxy.current_scope) > 0:
            for item in self.request_list.get_children():
                if self.request_list.set(item, "Host") not in self.proxy.current_scope:
                    self.request_list.detach(item)
                else:
                    self.request_list.reattach(item, '', tk.END)

            self.request_list_filtered = True

    def toggle_list_actions(self, state: str = tk.NORMAL) -> None:
        """
        WASTT/Proxy/HTTPTraffic:
            Toggle and updates action buttons and context menu actions accordingly to given state.
        """
        actions = (
            "Add url to the scope",
            "Remove url from the scope",
            "Send to repeater",
            "Send to intruder",
            "Copy request content",
            "Copy response content",
            "Copy request url",
        )
        for action in actions:
            self.request_list.popup_menu.entryconfig(action, state=state)

        for button in self.top_bar_buttons:
            if str(button.cget("state") != state):
                button.configure(state=state)
            if button == self.filter_list_button and len(self.proxy.current_scope) == 0:
                button.configure(state=tk.DISABLED)
            if button == self.filter_list_button and self.request_list_filtered:
                button.configure(state=tk.NORMAL)

        dprint(f"[DEBUG] FRONTEND/PROXY: Toggling buttons to {state} state.")

    def generate_random_request(self) -> None:
        """
        WASTT/Proxy/HTTPTraffic:
            Generates a random artificial request and adds it to the request list.
        """
        host = f"{random.choice(['example', 'test', 'check', 'domain'])}.{random.choice(['org', 'com', 'pl', 'eu'])}"
        path = f"/{random.choice(['entry', 'page', '', 'test', 'subpage'])}"
        method = random.choice(["GET", "POST", "PUT", "DELETE"])
        request_content = f'{method} {path} HTTP/1.1\nHost: {host}\nProxy-Connection: keep-alive\nrandom stuff here'
        status_code = f"{random.choice(['400', '401', '402', '403', '404'])}"
        title = f""
        response_content = (f"<!DOCTYPE html>\n"
                            f"<html lang=\"en\">\n"
                            f" <head>\n"
                            f"  <link rel=\"stylesheet\" href=\"/style.css\">\n"
                            f"  <link rel=\"icon\" href=\"/wastt.ico\" type=\"image/x-icon\">\n"
                            f"  <meta charset=\"UTF-8\">\n"
                            f"  <title>WASTT | Random content</title>\n"
                            f" </head>\n"
                            f" <body>\n"
                            f"  <h1>Header</h1>\n"
                            f"  <p>Paragraph</p>\n"
                            f" </body>\n"
                            f"</html>")
        length = len(response_content)
        random_request = [host, path, method, request_content,
                          status_code, title, length, response_content,
                          "https://" + host]

        self.request_list.insert("", tk.END, values=random_request)
        self.request_list_backup.insert("", tk.END, values=random_request)
        self.request_list.selection_remove(self.request_list.get_children())
        self.request_list.selection_add(self.request_list.get_children()[-1])

        if self.request_list_empty:
            self.toggle_list_actions(tk.NORMAL)
            self.request_list_empty = False


class InterceptTab(ctk.CTkFrame):
    """
    WASTT/Proxy/Interceptor:
        InterceptTab is a GUI component designed for managing
        and interacting with web request interceptions and related configurations.

        The class renders a frame containing several widgets to handle functionalities like
        toggling request interception, managing domain scopes, displaying intercepted request
        details, and providing quick actions like dropping or forwarding requests. It integrates
        tightly with certain external resources such as icons, styles, and master contexts to ensure
        seamless functionality.
    """
    def __init__(self, master, root):
        super().__init__(master)
        self.configure(
            fg_color=color_bg_br,
            bg_color="transparent",
            corner_radius=10
        )
        self.wastt = root
        self.proxy = master
        self.intercepting = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=2)

        # ================================================
        # Interceptor widget
        # ================================================
        interceptor_widget = DarkBox(self)
        interceptor_widget.grid(row=0, column=0, padx=(10, 5), pady=(0, 10), sticky=tk.NSEW)

        self.interceptor_header = HeaderTitle(interceptor_widget, "Web Request Interceptor")
        self.interceptor_header.pack(fill=tk.X, padx=10, pady=10)

        info_button = InfoButton(
            interceptor_widget,
            self,
            "http://localhost:8080/proxy.html#web_request_interceptor"
        )
        info_button.place(relx=1, rely=0, anchor=tk.NE, x=-5, y=15)

        interceptor_icon = Label(interceptor_widget, text="", image=icon_intercept)
        interceptor_icon.pack(expand=True, padx=10, pady=(5, 0))

        self.interceptor_status = Label(interceptor_widget, text="")
        self.interceptor_status.pack(expand=True, padx=10, pady=(0, 0))

        self.toggle_intercept_button = ActionButton(
            interceptor_widget,
            text="",
            image=icon_toggle_off,
            command=self.toggle_intercept,
            fg_color=color_green,
            hover_color=color_green_dk,
            width=200
        )
        self.toggle_intercept_button.pack(expand=True, padx=(10, 15), pady=(10, 0))

        browser_button = ActionButton(
            interceptor_widget,
            text="Open browser",
            image=icon_browser,
            command=self.wastt.start_browser_thread,
            width=200
        )
        browser_button.pack(expand=True, padx=(5, 10), pady=(5, 10))

        self.intercepted_request = None

        # ================================================
        # Scope widget
        # ================================================
        scope_widget = DarkBox(self)
        scope_widget.grid(row=0, column=1, padx=(5, 10), pady=(0, 10), sticky=tk.NSEW)

        scope_header = HeaderTitle(scope_widget, "Scope")
        scope_header.pack(fill=tk.X, padx=10, pady=10)

        scope_buttons = Box(scope_widget)
        scope_buttons.pack(side=tk.LEFT, fill=tk.Y, padx=(20, 5), pady=(0, 20))

        add_button = ActionButton(
            scope_buttons,
            text="Add domain",
            image=icon_add,
            command=self.proxy.submit_new_scope_hostname_dialog
        )
        add_button.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(0, 10))
        remove_button = ActionButton(
            scope_buttons,
            text="Remove domain",
            image=icon_delete,
            command=lambda: self.update_scope("remove")
        )
        remove_button.pack(side=tk.TOP, fill=tk.X, padx=5, pady=10)
        clear_button = ActionButton(
            scope_buttons,
            text="Clear domains",
            image=icon_delete,
            command=lambda: self.update_scope("clear")
        )
        clear_button.pack(side=tk.TOP, fill=tk.X, padx=5, pady=10)
        add_random_button = ActionButton(
            scope_buttons,
            text="Add random",
            image=icon_random,
            command=lambda: self.proxy.update_scope("add_random")
        )
        if RUNNING_CONFIG["debug_mode"]:
            add_random_button.pack(side=tk.TOP, fill=tk.X, padx=5, pady=10)
        load_from_file_button = ActionButton(
            scope_buttons,
            text="Load domains",
            image=icon_load_file,
            command=self.proxy.load_hostnames_to_scope
        )
        load_from_file_button.pack(side=tk.TOP, fill=tk.X, padx=5, pady=10)

        scope_url_list_wrapper = BrightBox(scope_widget)
        scope_url_list_wrapper.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 20), pady=(0, 20))

        self.scope_url_list = ItemList(scope_url_list_wrapper, columns="Host", style="Treeview2.Treeview")
        self.scope_url_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.scope_url_list.heading("Host", text="Domain names in the scope")
        self.scope_url_list.column("#0", width=0, stretch=tk.NO)
        self.scope_url_list_empty = True

        self.scope_url_list.popup_menu.add_command(
            label="Select all",
            command=self.scope_url_list.select_all
        )
        self.scope_url_list.popup_menu.add_command(
            label="Delete selected",
            command=lambda: self.update_scope("remove")
        )
        self.scope_url_list.popup_menu.add_command(
            label="Delete all",
            command=lambda: self.update_scope("clear")
        )
        self.scope_url_list.popup_menu.add_separator()
        self.scope_url_list.popup_menu.add_command(
            label="Copy URL",
            command=lambda: self.scope_url_list.copy_value(0)
        )

        # ================================================
        # Web Request Interceptor placeholder
        # ================================================
        self.placeholder_widget = DarkBox(self)
        self.placeholder_widget.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky=tk.NSEW)

        center_box = Box(self.placeholder_widget)
        center_box.pack(expand=True, anchor=tk.CENTER)

        self.interceptor_image = Label(center_box, image=intercept_off_image, text="")
        self.interceptor_image.pack(fill=tk.X, padx=10, pady=10)

        self.interceptor_state_label = Label(center_box, text="")
        self.interceptor_state_label.pack(fill=tk.X, padx=10, pady=10)

        self.interceptor_scope_label = Label(center_box, text="")
        self.interceptor_scope_label.pack(fill=tk.X, padx=10, pady=10)

        self.interceptor_status_update()

        # ================================================
        # Request widget
        # ================================================
        self.request_widget = DarkBox(self)

        request_buttons = Box(self.request_widget)
        request_buttons.pack(fill=tk.X, padx=10, pady=(10, 5))

        self.request_header = HeaderTitle(request_buttons, "Intercepted request")
        self.request_header.pack(side=tk.LEFT, padx=0, pady=0)

        drop_button = ActionButton(
            request_buttons,
            text=f"Drop",
            image=icon_arrow_down,
            command=self.drop_request
        )
        forward_button = ActionButton(
            request_buttons,
            text="Forward",
            image=icon_arrow_up,
            command=self.forward_request
        )
        send_to_intruder_button = ActionButton(
            request_buttons,
            text=f"Send to intruder",
            command=lambda: self.send_request("intruder")
        )
        send_to_repeater_button = ActionButton(
            request_buttons,
            text=f"Send to repeater",
            command=lambda: self.send_request("repeater")
        )
        self.top_bar_buttons = [
            drop_button,
            forward_button,
            send_to_intruder_button,
            send_to_repeater_button
        ]

        for button in self.top_bar_buttons:
            button.pack(side=tk.LEFT, padx=5, pady=10)

        request_fields = Box(self.request_widget)
        request_fields.pack(fill=tk.X, padx=10, pady=(0, 10))

        request_host_label = Label(request_fields, text="Host")
        request_host_label.pack(side=tk.LEFT, padx=(10, 0), pady=0)
        self.request_host_entry = TextEntry(request_fields, width=200)
        self.request_host_entry.pack(side=tk.LEFT, padx=(0, 10), pady=0)

        request_port_label = Label(request_fields, text="Port")
        request_port_label.pack(side=tk.LEFT, padx=(10, 0), pady=0)
        self.request_port_entry = TextEntry(request_fields, width=200)
        self.request_port_entry.pack(side=tk.LEFT, padx=(0, 10), pady=0)

        request_scheme_label = Label(request_fields, text="Scheme")
        request_scheme_label.pack(side=tk.LEFT, padx=(10, 0), pady=0)
        self.request_scheme_entry = TextEntry(request_fields, width=200)
        self.request_scheme_entry.pack(side=tk.LEFT, padx=(0, 10), pady=0)

        self.request_authority = None

        self.request_textbox = TextBox(self.request_widget, "")
        self.request_textbox.pack(pady=(0, 20), padx=20, fill=tk.BOTH, expand=True)

    def toggle_intercept(self) -> None:
        """
        WASTT/Proxy/Interceptor:
            Toggles intercepting on the frontend and sends flag to the backend.
        """
        def toggle():
            self.intercepting = not self.intercepting
            dprint(f"[DEBUG] FRONTEND/PROXY: Intercept state {self.intercepting}.")
            self.interceptor_status_update()

            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    serialized_flag = str(self.intercepting).encode("utf-8")
                    s.connect((RUNNING_CONFIG["proxy_host_address"], RUNNING_CONFIG["front_back_intercept_toggle_port"]))
                    s.sendall(serialized_flag)
            except Exception as e:
                print(f"[ERROR] FRONTEND/PROXY: Error while sending change intercept state flag: {e}")

        if self.intercepted_request is not None:
            confirm = ConfirmDialog(
                self,
                self.wastt,
                "Request currently intercepted",
                "There is request currently held by Web Interceptor. How do you want to proceed?",
                "Forward original request",
                lambda: (self.forward_request(), toggle(), confirm.destroy()),
                "Forward modified request",
                lambda: (self.forward_request(original=True), toggle(), confirm.destroy()),
                "Cancel",
                lambda: (confirm.destroy()),
                width=550
            )
        else:
            toggle()

    def interceptor_status_update(self) -> None:
        """
        WASTT/Proxy/Interceptor:
            Updates the status and UI components of a web interceptor based on its current state.

            The method modifies various UI elements, including buttons, labels, and images, to reflect whether
            the interceptor is active or inactive. Additionally, it provides detailed information
            about the scope of the interceptor when it is enabled,
            indicating whether specific domains are being monitored or if all requests are intercepted.
        """
        if self.intercepting:
            self.toggle_intercept_button.configure(text="Toggle Intercept off", image=icon_toggle_on,
                                                   fg_color=color_red, hover_color=color_red_dk)
            self.interceptor_status.configure(text="Web Interceptor is on.")
            self.interceptor_image.configure(image=intercept_on_image)
            self.interceptor_state_label.configure(text="Web Interceptor is currently on.\n"
                                                        "Web flow will be intercepted.")
            if len(self.proxy.current_scope) > 0:
                scope_string = ", ".join(self.proxy.current_scope)
                self.interceptor_scope_label.configure(text=f"There are domains in Web Interceptor scope.\n\n"
                                                            f"Requests to the following domains will be intercepted:\n"
                                                            f"{scope_string}")
            else:
                self.interceptor_scope_label.configure(text="Scope of Web Interceptor is empty.\n\n"
                                                            "All web requests will be intercepted.\n")

        else:
            self.toggle_intercept_button.configure(text="Toggle Intercept on", image=icon_toggle_off,
                                                   fg_color=color_green, hover_color=color_green_dk)
            self.interceptor_status.configure(text="Web Interceptor is off.")
            self.interceptor_image.configure(image=intercept_off_image)
            self.interceptor_state_label.configure(text="Web Interceptor is currently off.\n"
                                                        "Web flow won't be intercepted.")
            self.interceptor_scope_label.configure(text="\n\n\n")

    def receive_request(self) -> None:
        """
        WASTT/Proxy/Interceptor:
            Receives request from flow.request and adds it to intercept tab.
            and runs self.htt_add_request_to_list with received tab
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((RUNNING_CONFIG["proxy_host_address"], RUNNING_CONFIG["back_front_request_to_intercept_port"]))
            s.listen()

            while not self.wastt.stop_threads:
                conn, addr = s.accept()

                with conn:
                    serialized_reqeust = conn.recv(4096)
                    if serialized_reqeust:
                        try:
                            deserialized_request = pickle.loads(serialized_reqeust)
                            request2 = Request2.from_request(deserialized_request)

                            self.intercepted_request = request2
                            if RUNNING_CONFIG["log_intercepted_requests"]:
                                self.log_request()
                            self.show_request()

                        except Exception as e:
                            print(f"[ERROR] FRONTEND/PROXY: Error while deserializing received in scope: {e}")
                            data = ["resume", ]
                            serialized_data = pickle.dumps(data)
                            try:
                                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
                                    s2.connect((RUNNING_CONFIG["proxy_host_address"], RUNNING_CONFIG["front_back_data_port"]))
                                    s2.sendall(serialized_data)
                                self.intercepted_request = None
                                self.remove_request()
                            except Exception as e:
                                print(f"[ERROR] FRONTEND/PROXY: Forwarding intercepted request failed: {e}")

    def show_request(self) -> None:
        """
        WASTT/Proxy/Interceptor:
            Shows info and HTTP message of an intercepted request.
        """
        # version = self.intercepted_request.http_version
        host = self.intercepted_request.host
        port = self.intercepted_request.port
        scheme = self.intercepted_request.scheme
        authority = self.intercepted_request.authority
        request_content = self.intercepted_request.return_http_message()

        self.request_host_entry.insert("0", host)
        self.request_port_entry.insert("0", port)
        self.request_scheme_entry.insert("0", scheme)
        self.request_authority = authority
        self.request_textbox.insert_text(request_content)
        self.placeholder_widget.grid_forget()
        self.request_widget.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="nsew")

        for button in self.top_bar_buttons:
            if str(button.cget("state") != "normal"):
                button.configure(state="normal")

    def remove_request(self) -> None:
        """
        WASTT/Proxy/Interceptor:
            Hides request info and HTTP message after dropping, forwarding it.
        """
        self.intercepted_request = None

        self.request_host_entry.delete("0", tk.END)
        self.request_port_entry.delete("0", tk.END)
        self.request_scheme_entry.delete("0", tk.END)
        # self.request_authority_entry.delete("0", tk.END)
        self.request_textbox.insert_text("")
        self.request_widget.grid_forget()
        self.placeholder_widget.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="nsew")

        for button in self.top_bar_buttons:
            if str(button.cget("state") != "disabled"):
                button.configure(state="disabled")

    def log_request(self) -> None:
        """
        WASTT/Proxy/Interceptor:
            Logs the intercepted HTTP request to a specific log file for tracking and analysis.
        """
        logs_location = RUNNING_CONFIG.get("logs_location", "")
        if not logs_location:
            app_dir = Path(__file__).resolve().parent.parent
            logs_location = app_dir / "logs"
        logs_path = Path(logs_location / "web_interceptor")
        logs_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        log_file = logs_path / f"interceptor_requests-{today}.log"

        host = self.intercepted_request.host
        port = self.intercepted_request.port
        scheme = self.intercepted_request.scheme
        request_content = self.intercepted_request.return_http_message()

        with log_file.open("a") as file:
            file.write(f"[{timestamp}] Intercepted request to {scheme}://{host}:{port}\n{request_content}")

    def forward_request(self, original: bool = False) -> None:
        """
        WASTT/Proxy/Interceptor:
            Sends a request from Intercept tab textbox, request is forwarded to web browser.
        """
        data = None
        if original:
            data = ["forward", self.intercepted_request]
        else:
            request_host = self.request_host_entry.get()
            request_content = self.request_textbox.get_text().replace("\r", "")
            if len(request_content) > 0 and len(request_host) > 0:
                request2 = Request2.from_http_message(request_content)
                request2.host = request_host
                try:
                    request2.port = int(self.request_port_entry.get())
                except ValueError as e:
                    ErrorDialog(self, self.wastt, e)
                    return
                request2.scheme = self.request_scheme_entry.get()
                request2.authority = self.request_authority

                data = ["forward", request2.to_request()]

        if data is not None:
            serialized_data = pickle.dumps(data)
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((RUNNING_CONFIG["proxy_host_address"], RUNNING_CONFIG["front_back_data_port"]))
                    s.sendall(serialized_data)
                    self.remove_request()
            except Exception as e:
                print(f"[ERROR] FRONTEND/PROXY: Forwarding intercepted request failed: {e}")

    def drop_request(self) -> None:
        """
        WASTT/Proxy/Interceptor:
            Removes a request from list in GUI, request is dropped, proxy sends "request dropped info".
        """
        data = ["drop"]

        serialized_data = pickle.dumps(data)

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((RUNNING_CONFIG["proxy_host_address"], RUNNING_CONFIG["front_back_data_port"]))
                s.sendall(serialized_data)
                self.remove_request()
                self.intercepted_request = None
                self.intercepting = False
                self.interceptor_status_update()
        except Exception as e:
            print(f"[ERROR] FRONTEND/PROXY: Forwarding intercepted request failed: {e}")

    def send_request(self, dest: str) -> None:
        """
        WASTT/Proxy/Interceptor:
            It directly sends the first selected request to the respective app module: Intruder/Repeater.

        Parameters:
            dest: str - module name
        """
        request_content = self.request_textbox.get_text()
        try:
            hostname_url = self.intercepted_request.host
            if dest == "intruder":
                self.wastt.intruder.add_request_to_intruder_tab(content=request_content, host=hostname_url)
            elif dest == "repeater":
                self.wastt.repeater.add_request_to_repeater_tab(content=request_content, host=hostname_url)
        except Exception as e:
            print(f"[ERROR] Error while sending request from Intercept: {e}")

    def update_scope(self, mode: str = "remove") -> None:
        """
        WASTT/Proxy/Interceptor:
            Removes selected url(s) from the interceptor's scope.
            If mode set to 'clear' it removes all urls from the scope.

        Parameters:
            mode: str - 'remove' or 'clear', default 'remove'
        """
        if mode == "remove":
            hostnames = set()

            if len(self.scope_url_list.selection()) > 0:
                for selected_item in self.scope_url_list.selection():
                    hostnames.add(self.scope_url_list.item(selected_item)['values'][0])

            if len(hostnames) > 0:
                self.proxy.update_scope(mode, hostnames)

        elif mode == "clear":
            self.proxy.update_scope(mode)


class Proxy(ctk.CTkFrame):
    """
    WASTT/Proxy:
        Represents the Proxy GUI component within the application.

        The Proxy class is responsible for managing and displaying the Proxy GUI
        elements, including HTTP traffic tabs, scope management for intercepted HTTP
        traffic, and interacting with the HTTP(S) proxy backend process (`mitmdump`).
        It provides functionality for navigating between tabs, initiating and managing
        the proxy backend subprocess, and updating the scope of intercepted domain
        hostnames.
    """

    def __init__(self, master, root):
        super().__init__(master)
        self.configure(fg_color=color_bg_br, bg_color="transparent", corner_radius=10)
        self.wastt = root
        self.process = None

        # ================================================
        # Web Request Interceptor scope
        # ================================================
        self.add_to_scope_dialog = None
        self.add_to_scope_dialog_notice = None
        self.current_scope = set()

        # ================================================
        # Proxy sub-tabs
        # ================================================
        self.http_traffic_tab = HTTPTrafficTab(self, self.wastt)
        self.intercept_tab = InterceptTab(self, self.wastt)
        self.tabs = {
            "HTTP Traffic": self.http_traffic_tab,
            "Intercept": self.intercept_tab
        }
        tab_nav = Box(self)
        tab_nav.pack(side=tk.TOP, fill="x", padx=25, pady=(10, 0))

        self.tab_nav_buttons = {}
        for tab in self.tabs.keys():
            self.tab_nav_buttons[tab] = NavButton(tab_nav, text=tab, command=lambda t=tab: self.switch_tab(t),
                                                  font=ctk.CTkFont(family="Calibri", size=14, weight="normal"),
                                                  background=color_bg_br, background_selected=color_bg)
            self.tab_nav_buttons[tab].pack(side="left")

        self.switch_tab("HTTP Traffic")

        # ================================================
        # Initialising backend for the Proxy tab.
        # Running mitmproxy at start
        # ================================================
        threading.Thread(target=self.intercept_tab.receive_request, daemon=True).start()
        threading.Thread(target=self.http_traffic_tab.receive_request, daemon=True).start()

        if not self.process:
            threading.Thread(target=self.run_mitmdump).start()

    def run_mitmdump(self, init_scope=None):
        """
        WASTT/Proxy:
            Runs mitmdump process after first killing all the mitdmdump.exe processes.
        """
        try:
            result = subprocess.run(['taskkill', '/F', '/IM', 'mitmdump.exe', '/T'], capture_output=True, text=True)
            if 'SUCCESS' in result.stdout:
                print("[INFO] Previously run mitmdump.exe process has been terminated.")
        except Exception as e:
            print(f"[ERROR] Terminating previously run mitmdump process failed: {e}")

        try:
            from config import RUNNING_CONFIG

            backend_dir = Path(__file__).parent.parent / "backend"
            proxy_script = backend_dir / "proxy.py"
            proxy_port = str(RUNNING_CONFIG["proxy_port"])
            command = ["mitmdump", "-s", proxy_script, "--listen-port", proxy_port]

            if RUNNING_CONFIG["proxy_console"]:
                command = ["start", "cmd", "/k"] + command
                print("[INFO] Starting the HTTP(S) proxy process in new shell terminal window.")
            else:
                print("[INFO] Starting the HTTP(S) proxy process.")

            if RUNNING_CONFIG["proxy_logging"]:
                logs_location = RUNNING_CONFIG.get("logs_location", "")
                if not logs_location:
                    app_dir = Path(__file__).resolve().parent.parent
                    logs_location = app_dir / "logs"
                else:
                    logs_location(logs_location)
                log_file = str(Path(logs_location / "proxy" / f"mitmdump-{today}.log"))
                print(f"[INFO] Logging mitmdump process to the file: {log_file}.")
                command = command + ["-w", log_file]

            self.process = subprocess.Popen(
                command,
                cwd=backend_dir,
                shell=RUNNING_CONFIG["proxy_console"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            def read_stdout():
                """
                WASTT/Proxy:
                    Reads Standard Out lines from running mitmdump process.
                """
                for line in iter(self.process.stdout.readline, ''):
                    print(f"[MITMDUMP] {line.strip()}")

            def read_stderr():
                """
                WASTT/Proxy:
                    Reads Standard Error lines from running mitmdump process.
                """
                for line in iter(self.process.stderr.readline, ''):
                    print(f"[MITMDUMP ERROR] {line.strip()}")

            threading.Thread(target=read_stdout, daemon=True).start()
            threading.Thread(target=read_stderr, daemon=True).start()

            if init_scope is not None and len(init_scope) > 0:
                try:
                    self.update_scope(
                        mode="add",
                        hostnames_to_update=init_scope
                    )
                    self.current_scope = init_scope

                except Exception as e:
                    print(f"[ERROR] {e}")
            else:
                self.current_scope.clear()
                self.intercept_tab.scope_url_list.delete_all()

        except Exception as e:
            print(f"[ERROR] While starting the HTTP(S) proxy process: {e}")
        finally:
            self.process = None

    def switch_tab(self, selected_tab):
        """
        WASTT/Proxy:
            Switches sub tabs of Proxy tab
        """
        for tab_name, tab in self.tabs.items():
            if tab_name == selected_tab:
                dprint(f"[DEBUG] Proxy/Tabs: Switching to {tab_name} tab")
                tab.pack(side=tk.TOP, fill="both", expand=True)
                self.tab_nav_buttons[tab_name].select(True)
            else:
                dprint(f"[DEBUG] Proxy/Tabs: Hiding {tab_name} tab")
                tab.pack_forget()
                self.tab_nav_buttons[tab_name].select(False)

    def submit_new_scope_hostname_dialog(self):
        """
        WASTT/Proxy:
            Opens a dialog to add a custom hostname to Scope.
        """
        self.add_to_scope_dialog = ctk.CTkToplevel(self)
        self.add_to_scope_dialog.title("Add hostname to the Scope")
        self.add_to_scope_dialog.geometry("300x150")
        self.add_to_scope_dialog.attributes("-topmost", True)
        center_window(self.wastt, self.add_to_scope_dialog, 300, 150)

        url_label = ctk.CTkLabel(self.add_to_scope_dialog, text="Enter domain URL", anchor="w")
        url_label.pack(pady=(10, 5), padx=10, fill="x")

        url_entry = TextEntry(self.add_to_scope_dialog)
        url_entry.pack(pady=5, padx=10, fill="x")
        url_entry.bind("<Return>", lambda event: self.submit_new_scope_hostname(url_entry.get()))

        self.add_to_scope_dialog_notice = ctk.CTkLabel(self.add_to_scope_dialog, text="",
                                                       text_color=color_text_warn,
                                                       wraplength=250)
        self.add_to_scope_dialog_notice.pack(pady=0, padx=10, fill=tk.X)

        submit_button = ctk.CTkButton(self.add_to_scope_dialog, text="Submit",
                                      command=lambda: self.submit_new_scope_hostname(url_entry.get()))
        submit_button.pack(pady=(5, 10))
        submit_button.bind("<Return>", lambda event: self.submit_new_scope_hostname(url_entry.get()))

    def submit_new_scope_hostname(self, url):
        """
        WASTT/Proxy:
            Submits the custom scope hostname provided in the dialog.
        """
        pattern = r"^(?:[a-zA-Z0-9-]+\.)*[a-zA-Z0-9-]+\.[a-zA-Z]{1,3}$"
        if len(url) > 0:
            if re.match(pattern, url):
                if url not in self.current_scope:
                    hostnames = set()
                    hostnames.add(url)
                    self.update_scope("add", hostnames)
                    self.add_to_scope_dialog.destroy()
                else:
                    self.add_to_scope_dialog_notice.configure(text=f"Oy! Domain {url} is already added to the scope!")
            else:
                self.add_to_scope_dialog_notice.configure(text="Oy! Your domain url does not match valid pattern!")
        else:
            self.add_to_scope_dialog_notice.configure(text="Oy! Cannot pass empty URL!")

    def load_hostnames_to_scope(self):
        """
        WASTT/Proxy:
            Load scope hostnames from text file.
        """
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])

        if file_path:
            try:
                with open(file_path, "r") as file:
                    hostnames = set()
                    for line in file:
                        hostnames.add(line.strip())
                    self.update_scope("add", hostnames)

            except FileNotFoundError:
                print(f"[ERROR] FRONTEND/PROXY: File {file_path} could not be open. Default settings have been loaded.")

    def update_scope(self, mode="add", hostnames_to_update=None):
        """
        WASTT/Proxy:
            Updates (adds, removes, clears) the current scope for Web Interceptor.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if mode == "add":
                    hostnames_to_update -= self.current_scope
                if mode == "clear":
                    hostnames_to_update = set()
                if mode == "add_random":
                    mode = "add"
                    source_hostnames = {"example.com", "test.com", "name.com",
                                        "wikipedia.org", "overthewire.org",
                                        "bing.com", "facebook.com", "youtube.com", "google.com",
                                        "nazwa.pl", "kurnik.pl", "wp.pl"
                                        }
                    hostnames_to_update = set()
                    n = random.randint(1, len(source_hostnames))
                    hostnames_to_update.update(random.sample(source_hostnames, n))
                    hostnames_to_update -= self.current_scope

                data_to_send = (mode, *hostnames_to_update)
                serialized_data = pickle.dumps(data_to_send)
                s.connect((RUNNING_CONFIG["proxy_host_address"], RUNNING_CONFIG["front_back_scope_update_port"]))
                s.sendall(serialized_data)

                if mode == "add":
                    self.current_scope |= hostnames_to_update
                    for hostname in hostnames_to_update:
                        self.intercept_tab.scope_url_list.insert("", tk.END, values=hostname)

                elif mode == "remove":
                    self.current_scope -= hostnames_to_update
                    for item in self.intercept_tab.scope_url_list.get_children():
                        if self.intercept_tab.scope_url_list.item(item)['values'][0] in hostnames_to_update:
                            self.intercept_tab.scope_url_list.delete(item)

                elif mode == "clear":
                    self.current_scope.clear()
                    self.intercept_tab.scope_url_list.delete_all()

            if len(self.current_scope) == 0:
                self.http_traffic_tab.filter_list_button.toggle_state(tk.DISABLED)
            elif not self.http_traffic_tab.request_list_empty:
                self.http_traffic_tab.filter_list_button.toggle_state(tk.NORMAL)

        except Exception as e:
            print(f"ERROR FRONTEND PROXY: Error while updating ({mode}) WebInterceptor scope: {e}")

        self.intercept_tab.interceptor_status_update()

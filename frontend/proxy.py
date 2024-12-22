from common import *


class HTTPTrafficTab(ctk.CTkFrame):
    def __init__(self, master, root):
        super().__init__(master)
        self.configure(fg_color="transparent", bg_color="transparent", corner_radius=10)
        self.proxy_gui = master
        self.gui = root
        self.intercepting = root.intercepting

        """
         > Top Bar
        """
        self.top_bar = ctk.CTkFrame(self, height=50, corner_radius=10, fg_color=color_bg,
                                    bg_color="transparent")
        self.top_bar.pack(side=tk.TOP, fill=tk.X, pady=(0, 5), padx=5)

        self.add_to_scope_button = ActionButton(
            self.top_bar, text="Add to scope",  # image=icon_add,
            command=lambda: self.update_scope(),
            state=tk.DISABLED)
        self.send_requests_to_intruder_button = ActionButton(
            self.top_bar, text="Send to intruder",  # image=icon_arrow_up,
            command=lambda: self.send_request("intruder"),
            state=tk.DISABLED)
        self.send_requests_to_repeater_button = ActionButton(
            self.top_bar, text="Send to repeater",  # image=icon_arrow_up,
            command=lambda: self.send_request("repeater"),
            state=tk.DISABLED)
        self.filter_list_button = ActionButton(
            self.top_bar, text=f"Filter the list with scope",  # image=icon_random,
            command=self.filter_list_with_scope)
        self.delete_requests_button = ActionButton(
            self.top_bar, text="Delete all requests",  # image=icon_delete,
            command=self.remove_all_requests_from_list,
            state=tk.DISABLED,
            fg_color=color_acc3, hover_color=color_acc4)
        self.add_random_entry = ActionButton(
            self.top_bar, text=f"Random request", image=icon_random,
            command=self.generate_random_request)
        self.browser_button = ActionButton(
            self.top_bar, text="Open browser", image=icon_browser,
            command=self.gui.start_browser_thread)
        self.proxy_button = ActionButton(
            self.top_bar, text="Re-run proxy", image=icon_reload,
            command=self.proxy_gui.run_mitmdump)

        self.request_list_filtered = False

        self.top_bar_buttons = [
            self.add_to_scope_button,
            self.send_requests_to_intruder_button,
            self.send_requests_to_repeater_button,
            self.filter_list_button,
            self.delete_requests_button
        ]
        for ind, button in enumerate(self.top_bar_buttons):
            if ind == 0:
                button.pack(side=tk.LEFT, padx=(10, 5), pady=15)
            else:
                button.pack(side=tk.LEFT, padx=5, pady=15)

        self.add_random_entry.pack(side=tk.LEFT, padx=5, pady=15)
        self.browser_button.pack(side=tk.RIGHT, padx=(5, 10), pady=15)
        self.proxy_button.pack(side=tk.RIGHT, padx=5, pady=15)

        self.paned_window = tk.PanedWindow(self, orient=tk.VERTICAL, sashwidth=10,
                                           background=color_bg_br)
        self.paned_window.pack(fill=tk.BOTH, expand=1, padx=5, pady=5)

        """
         > Top pane
        """
        self.top_pane = ctk.CTkFrame(self.paned_window, corner_radius=10, fg_color=color_bg,
                                     bg_color="transparent")
        self.paned_window.add(self.top_pane, height=350)

        columns = ("Host", "URL", "Method", "Request", "Status code", "Title", "Length", "Response", "RealURL")
        self.request_list = ItemList(self.top_pane, columns=columns, show="headings", style="Treeview")
        self.request_list_backup = ItemList(self.top_pane, columns=columns)
        self.request_list.bind("<<TreeviewSelect>>", self.show_request_content)
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
            command=self.request_list.select_all)
        self.request_list.popup_menu.add_command(
            label="Delete selected",
            command=self.remove_selected_request_from_list)
        self.request_list.popup_menu.add_command(
            label="Delete all",
            command=self.remove_all_requests_from_list)
        self.request_list.popup_menu.add_separator()
        self.request_list.popup_menu.add_command(
            label="Add url to the scope",
            command=lambda: self.update_scope("add"))
        self.request_list.popup_menu.add_command(
            label="Remove url from the scope",
            command=lambda: self.update_scope("remove"))
        self.request_list.popup_menu.add_separator()
        self.request_list.popup_menu.add_command(
            label="Send to intruder",
            command=lambda: self.send_request("intruder"))
        self.request_list.popup_menu.add_command(
            label="Send to repeater",
            command=lambda: self.send_request("repeater"))
        self.request_list.popup_menu.add_separator()
        self.request_list.popup_menu.add_command(
            label="Copy request content",
            command=lambda: self.request_list.copy_value(3))
        self.request_list.popup_menu.add_command(
            label="Copy response content",
            command=lambda: self.request_list.copy_value(7))
        self.request_list.popup_menu.add_command(
            label="Copy request url",
            command=lambda: self.request_list.copy_value(-1))

        """
         > Bottom pane
        """
        self.bottom_pane = ctk.CTkFrame(self.paned_window, corner_radius=10, fg_color=color_bg,
                                        bg_color="transparent")
        self.paned_window.add(self.bottom_pane)

        self.bottom_pane.grid_columnconfigure(0, weight=1)
        self.bottom_pane.grid_columnconfigure(1, weight=1)
        self.bottom_pane.grid_rowconfigure(0, weight=1)

        self.request_frame = ctk.CTkFrame(self.bottom_pane, fg_color=color_bg)
        self.request_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.request_header = HeaderTitle(self.request_frame, "Request")
        self.request_header.pack(fill=tk.X)

        self.request_textbox = TextBox(self.request_frame, "Select request to display its contents.")
        self.request_textbox.pack(pady=10, padx=10, fill="both", expand=True)

        self.response_frame = ctk.CTkFrame(self.bottom_pane, fg_color=color_bg, bg_color="transparent")
        self.response_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.response_header = HeaderTitle(self.response_frame, "Response")
        self.response_header.pack(fill=tk.X)

        self.response_render_button = ActionButton(
            self.response_frame,
            text="Show response render",
            command=self.show_response_view
        )
        self.response_render_button.place(relx=1, rely=0, anchor=tk.NE, x=-10, y=10)

        self.response_textbox = TextBox(self.response_frame, "Select request to display its response contents.")
        self.response_textbox.configure(state=tk.DISABLED)
        self.response_textbox.pack(pady=10, padx=10, fill="both", expand=True)
        self.response_view = None

    def update_scope(self, mode="add"):
        """
        Proxy GUI:
            Adds to / Removes from the scope selected url(s) from the given request list.
        """
        if len(self.request_list.selection()) > 0:
            hostnames = set()

            for item in self.request_list.selection():
                hostnames.add(self.request_list.item(item)['values'][0])

            if len(hostnames) > 0:
                self.proxy_gui.update_scope(mode, hostnames)
                # print(f"DEBUG/FRONTEND/PROXY: {mode.capitalize().replace('e', '')}ing {hostnames_to_update} to the scope")

    def receive_request(self):
        """
        HTTP Traffic Tab:
            Receives tab = [flow.request, flow.response] from backend.proxy.WebRequestInterceptor.send_flow_to_http_trafic_tab
            and runs self.htt_add_request_to_list with received tab
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, BACK_FRONT_HISTORYREQUESTS_PORT))
            s.listen()
            while not self.gui.stop_threads:
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
                                self.add_request_to_list(request2, response)
                            else:
                                # print(f"REQUEST ONLY\n\tRequest:\n\t\t{request2}")
                                self.add_request_to_list(request2)
                        except Exception as e:
                            if str(e) != "pickle data was truncated":  # Cannot pickle "cryptography.hazmat.bindings._rust.x509.Certificate"
                                print(f"Error while deserialization request to http traffic: {e}")

    def add_request_to_list(self, req, resp=None):
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

        self.request_list.insert("", tk.END, values=values)
        self.request_list_backup.insert("", tk.END, values=values)

        if len(self.request_list.selection()) == 0:
            self.request_list.selection_add(self.request_list.get_children()[0])

        if self.request_list_empty:
            self.toggle_list_actions("normal")
            self.request_list_empty = False

    def show_request_content(self, event):
        """
        HTTP Traffic Tab:
            Shows selected HTTP request and its response in the textbox.
        """
        if len(self.request_list.selection()) > 0:
            selected_item = self.request_list.selection()[0]
            request_string = self.request_list.item(selected_item)['values'][3]
            if len(self.request_list.item(selected_item)['values']) == 9:
                response_string = self.request_list.item(selected_item)['values'][7]
            else:
                response_string = "Request got no response."
            self.request_textbox.configure(state=tk.NORMAL, font=self.request_textbox.monoscape_font)
            self.request_textbox.insert_text(request_string)
            self.response_textbox.configure(state=tk.NORMAL, font=self.request_textbox.monoscape_font)
            self.response_textbox.insert_text(response_string)
            self.response_textbox.configure(state=tk.DISABLED)
        else:
            self.request_textbox.configure(state=tk.NORMAL)
            self.request_textbox.insert_text("Select a request to display its contents.")
            self.request_textbox.configure(state=tk.DISABLED, font=self.request_textbox.monoscape_font_italic)
            self.response_textbox.configure(state=tk.NORMAL)
            self.response_textbox.insert_text("Select a request to display contents of its response.")
            self.response_textbox.configure(state=tk.DISABLED, font=self.request_textbox.monoscape_font_italic)

    def show_response_view(self):
        response_content = self.response_textbox.get_text()

        if len(response_content) > 0:
            self.response_view = ctk.CTk()
            width = int(self.gui.root.winfo_width() * 0.9)
            height = int(self.gui.root.winfo_height() * 0.9)
            self.response_view.geometry(f"{width}x{height}")
            # self.response_view.attributes("-topmost", True)
            center_window(self.gui, self.response_view, width, height)

            host_url = ""
            if len(self.request_list.selection()) > 0:
                selected_item = self.request_list.selection()[0]
                host_url = self.request_list.item(selected_item)['values'][-1]
                response_content = self.response_textbox.get_text()
                response_content = response_content.replace("src=\"/", f"src=\"{host_url}/")
                response_content = response_content.replace("href=\"/", f"href=\"{host_url}/")

            response_webview = tkinterweb.HtmlFrame(self.response_view, messages_enabled=False)
            response_webview.load_html(response_content)
            response_webview.current_url = host_url
            response_webview.pack(pady=0, padx=0, fill="both", expand=True)
            self.response_view.mainloop()

    def send_request(self, dest):
        request_content = self.request_textbox.get_text()
        hostname_url = ""
        if len(self.request_list.selection()[0]) > 0:
            selected_item = self.request_list.selection()[0]
            hostname_url = self.request_list.item(selected_item)['values'][-1]
        if dest == "intruder":
            self.gui.intruder_tab.add_request_to_intruder_tab(request_content, host=hostname_url)
        elif dest == "repeater":
            self.gui.repeater_tab.add_request_to_repeater_tab(request_content, host=hostname_url)

    def remove_selected_request_from_list(self):
        # print(self.request_list.selection())
        for item in self.request_list.selection():
            self.request_list_backup.delete(item)
            print(f"deleted {item} from backup list")
        self.request_list.delete_selected()
        if len(self.request_list.get_children()) == 0 and not self.request_list_empty:
            self.toggle_list_actions("disabled")
            self.request_list_empty = True

    def remove_all_requests_from_list(self):
        self.request_list.delete_all()
        self.request_list_backup.delete_all()
        if not self.request_list_empty:
            # print("DEBUG/FRONTEND/PROXY/HTTP TRAFFIC: Deleting all the requests from the list.")
            self.toggle_list_actions("disabled")
            self.request_list_empty = True

    def sort_by_column(self, col, reverse):
        index_list = [(self.request_list.set(k, col), k) for k in self.request_list.get_children('')]
        index_list.sort(reverse=reverse)

        for index, (val, k) in enumerate(index_list):
            self.request_list.move(k, '', index)

        self.request_list.heading(col, command=lambda: self.sort_by_column(col, not reverse))

    def filter_list_with_scope(self):
        if self.request_list_filtered:
            self.filter_list_button.configure(text="Filter the list with scope")

            self.request_list.delete_all()

            for item in self.request_list_backup.get_children():
                values = list(self.request_list_backup.item(item)['values'])
                self.request_list.insert("", tk.END, values=values)

            self.request_list_filtered = False
        elif len(self.proxy_gui.current_scope) > 0:
            self.filter_list_button.configure(text="Remove filtering")

            for item in self.request_list.get_children():
                if self.request_list.set(item, "Host") not in self.proxy_gui.current_scope:
                    self.request_list.detach(item)
                else:
                    self.request_list.reattach(item, '', tk.END)

            self.request_list_filtered = True

    def generate_random_request(self):
        """
        Proxy GUI:
            Generates a random fake request and adds it to the request lists.
        """
        url = f"{random.choice(['example', 'test', 'check', 'domain'])}.{random.choice(['org', 'com', 'pl', 'eu'])}"
        path = f"/{random.choice(['entry', 'page', '', 'test', 'subpage'])}"
        method = random.choice(["GET", "POST", "PUT", "DELETE"])
        request_content = f'{method} {path} HTTP/1.1\nHost: {url}\nProxy-Connection: keep-alive\nrandom stuff here'
        status_code = f"{random.choice(['400', '401', '402', '403', '404'])}"
        title = f""
        response_content = f'Some HTTP gibberish here.'
        length = len(response_content)
        random_request = [url, path, method, request_content, status_code, title, length, response_content, url]

        self.request_list.insert("", tk.END, values=random_request)
        self.request_list_backup.insert("", tk.END, values=random_request)
        self.request_list.selection_remove(self.request_list.get_children())
        self.request_list.selection_add(self.request_list.get_children()[-1])

        if self.request_list_empty:
            self.toggle_list_actions("normal")
            self.request_list_empty = False

    def toggle_list_actions(self, state="normal"):
        """
        Proxy GUI:
            Checks if request lists in proxy GUI are empty and updates action buttons and menu buttons accordingly.
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
        # print(f"DEBUG/FRONTEND/PROXY: Toggling buttons to {state} state.")


class InterceptTab(ctk.CTkFrame):
    def __init__(self, master, root):
        super().__init__(master)
        self.configure(fg_color=color_bg_br, bg_color="transparent", corner_radius=10)
        self.proxy_gui = master
        self.gui = root
        self.intercepting = root.intercepting

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=2)
        """
         > Web Interceptor Widget
        """
        self.interceptor_widget = ctk.CTkFrame(self, fg_color=color_bg, bg_color="transparent",
                                               corner_radius=10)
        self.interceptor_widget.grid(row=0, column=0, padx=5, pady=(0, 10), sticky="nsew")

        self.interceptor_header = HeaderTitle(self.interceptor_widget, "Web Interceptor")
        self.interceptor_header.pack(fill=tk.X, padx=10, pady=10)
        # self.interceptor_wrapper.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(0, 10))

        self.interceptor_icon = ctk.CTkLabel(self.interceptor_widget, text="", image=icon_intercept)
        self.interceptor_icon.pack(expand=True, padx=10, pady=(5, 0))

        self.interceptor_status = ctk.CTkLabel(self.interceptor_widget, text="")
        self.interceptor_status.pack(expand=True, padx=10, pady=(0, 0))

        self.toggle_intercept_button = ActionButton(self.interceptor_widget,
                                                    text="",
                                                    image=icon_toggle_off,
                                                    command=self.toggle_intercept,
                                                    fg_color=color_green,
                                                    hover_color=color_green_dk,
                                                    width=200)
        self.toggle_intercept_button.pack(expand=True, padx=(10, 15), pady=(10, 0))

        self.browser_button = ActionButton(self.interceptor_widget,
                                           text="Open browser",
                                           image=icon_browser,
                                           command=self.gui.start_browser_thread,
                                           width=200)
        self.browser_button.pack(expand=True, padx=(5, 10), pady=(5, 10))

        self.intercepted_request = None

        """
         > Scope Widget
        """
        self.scope_widget = ctk.CTkFrame(self, corner_radius=10, fg_color=color_bg, bg_color="transparent")
        self.scope_widget.grid(row=0, column=1, padx=5, pady=(0, 10), sticky="nsew")

        self.scope_header = HeaderTitle(self.scope_widget, "Scope")
        self.scope_header.pack(fill=tk.X, padx=10, pady=10)

        self.scope_buttons = ctk.CTkFrame(self.scope_widget, fg_color="transparent", corner_radius=10)
        self.scope_buttons.pack(side=tk.LEFT, fill=tk.Y, padx=(20, 5), pady=(0, 20))

        self.add_button = ActionButton(
            self.scope_buttons, text="Add domain", image=icon_add,
            command=self.proxy_gui.submit_new_scope_hostname_dialog
        )
        self.add_button.pack(side="top", fill=tk.X, padx=5, pady=(0, 10))
        self.remove_button = ActionButton(
            self.scope_buttons, text="Remove domain", image=icon_delete,
            command=lambda: self.update_scope("remove")
        )
        self.remove_button.pack(side="top", fill=tk.X, padx=5, pady=10)
        self.clear_button = ActionButton(
            self.scope_buttons, text="Clear domains", image=icon_delete,
            command=lambda: self.update_scope("clear")
        )
        self.clear_button.pack(side="top", fill=tk.X, padx=5, pady=10)
        self.clear_button = ActionButton(
            self.scope_buttons, text="Load domains", image=icon_load_file,
            command=self.proxy_gui.load_hostnames_to_scope
        )
        self.clear_button.pack(side="top", fill=tk.X, padx=5, pady=10)

        self.scope_url_list_wrapper = ctk.CTkFrame(self.scope_widget,
                                                   corner_radius=10, fg_color=color_bg_br, bg_color="transparent")
        self.scope_url_list_wrapper.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 20), pady=(0, 20))
        self.scope_url_list = ItemList(self.scope_url_list_wrapper, columns="Host", style="Treeview2.Treeview")
        self.scope_url_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.scope_url_list.heading("Host", text="Domain names in the scope")
        self.scope_url_list.column("#0", width=0, stretch=tk.NO)
        self.scope_url_list_empty = True

        self.scope_url_list.popup_menu.add_command(
            label="Select all",
            command=self.scope_url_list.select_all)
        self.scope_url_list.popup_menu.add_command(
            label="Delete selected",
            command=lambda: self.update_scope("remove"))
        self.scope_url_list.popup_menu.add_command(
            label="Delete all",
            command=lambda: self.update_scope("clear"))
        self.scope_url_list.popup_menu.add_separator()
        self.scope_url_list.popup_menu.add_command(
            label="Copy URL",
            command=lambda: self.scope_url_list.copy_value(0))

        """
         > Interceptor Placeholder
        """
        self.placeholder_widget = ctk.CTkFrame(self, fg_color=color_bg, bg_color="transparent",
                                               corner_radius=10)
        self.placeholder_widget.grid(row=1, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="nsew")

        self.center_frame = ctk.CTkFrame(self.placeholder_widget, fg_color="transparent", bg_color="transparent")
        self.center_frame.pack(expand=True, anchor="center")

        self.interceptor_image = ctk.CTkLabel(self.center_frame, image=intercept_off_image, text="")
        self.interceptor_image.pack(fill=tk.X, padx=10, pady=10)

        self.interceptor_state_label = ctk.CTkLabel(self.center_frame, text="")
        self.interceptor_state_label.pack(fill=tk.X, padx=10, pady=10)

        self.interceptor_scope_label = ctk.CTkLabel(self.center_frame, text="")
        self.interceptor_scope_label.pack(fill=tk.X, padx=10, pady=10)

        self.interceptor_status_update()

        """
         > Request Widget
        """
        self.request_widget = ctk.CTkFrame(self, fg_color=color_bg, bg_color="transparent",
                                           corner_radius=10)
        # self.request_widget.grid(row=1, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="nsew")

        self.request_buttons = ctk.CTkFrame(self.request_widget, fg_color="transparent", bg_color="transparent",
                                            corner_radius=10)
        self.request_buttons.pack(fill=tk.X, padx=10, pady=(10, 5))

        self.request_header = HeaderTitle(self.request_buttons, "Intercepted request")
        self.request_header.pack(side=tk.LEFT, padx=0, pady=0)

        self.drop_button = ActionButton(
            self.request_buttons, text=f"Drop", image=icon_arrow_down,
            command=self.drop_request)
        self.forward_button = ActionButton(
            self.request_buttons, text="Forward", image=icon_arrow_up,
            command=self.forward_request)
        self.send_to_intruder_button = ActionButton(
            self.request_buttons, text=f"Send to intruder", command=lambda: self.send_request("intruder"))
        self.send_to_repeater_button = ActionButton(
            self.request_buttons, text=f"Send to repeater", command=lambda: self.send_request("repeater"))
        self.top_bar_buttons = [
            self.drop_button,
            self.forward_button,
            self.send_to_intruder_button,
            self.send_to_repeater_button
        ]
        for button in self.top_bar_buttons:
            button.pack(side=tk.LEFT, padx=5, pady=10)

        self.request_fields = ctk.CTkFrame(self.request_widget, fg_color="transparent", bg_color="transparent",
                                           corner_radius=10)
        self.request_fields.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.request_host_label = Label(self.request_fields, text="Host")
        self.request_host_label.pack(side=tk.LEFT, padx=(10, 0), pady=0)
        self.request_host_entry = TextEntry(self.request_fields, width=200)
        self.request_host_entry.pack(side=tk.LEFT, padx=(0, 10), pady=0)

        self.request_port_label = Label(self.request_fields, text="Port")
        self.request_port_label.pack(side=tk.LEFT, padx=(10, 0), pady=0)
        self.request_port_entry = TextEntry(self.request_fields, width=200)
        self.request_port_entry.pack(side=tk.LEFT, padx=(0, 10), pady=0)

        self.request_scheme_label = Label(self.request_fields, text="Scheme")
        self.request_scheme_label.pack(side=tk.LEFT, padx=(10, 0), pady=0)
        self.request_scheme_entry = TextEntry(self.request_fields, width=200)
        self.request_scheme_entry.pack(side=tk.LEFT, padx=(0, 10), pady=0)

        self.request_authority_label = Label(self.request_fields, text="Authority")
        self.request_authority_label.pack(side=tk.LEFT, padx=(10, 0), pady=0)
        self.request_authority_entry = TextEntry(self.request_fields, width=200)
        self.request_authority_entry.pack(side=tk.LEFT, padx=(0, 10), pady=0)

        self.request_textbox = TextBox(self.request_widget, "")
        self.request_textbox.pack(pady=(0, 20), padx=20, fill="both", expand=True)

    def toggle_intercept(self):
        """
        Intercept Tab:
            Toggles intercepting on the frontend and sends flag to the backend.
        """
        self.gui.intercepting = not self.gui.intercepting
        # print(f"DEBUG/FRONTEND/PROXY: Intercept state {self.gui.intercepting}.")
        self.interceptor_status_update()

        # TODO BACKEND: Can we have an actual bool state of self.gui.intercepting sent to backend instead of toggle flag?
        flag = "Change state"
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, FRONT_BACK_INTERCEPTBUTTON_PORT))
                serialized_flag = flag.encode("utf-8")
                s.sendall(serialized_flag)
        except Exception as e:
            print(f"Error while sending change intercept state flag: {e}")

    def interceptor_status_update(self):
        if self.gui.intercepting:
            self.toggle_intercept_button.configure(text="Toggle Intercept off", image=icon_toggle_on,
                                                   fg_color=color_red, hover_color=color_red_dk)
            self.interceptor_status.configure(text="Web Interceptor is on.")
            self.interceptor_image.configure(image=intercept_on_image)
            self.interceptor_state_label.configure(text="Web Interceptor is currently on.\n"
                                                        "Web flow will be intercepted.")
            if len(self.proxy_gui.current_scope) > 0:
                scope_string = ", ".join(self.proxy_gui.current_scope)
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

    def receive_request(self):
        """
        Intercept Tab:
            Receives request from flow.request and adds it to intercept tab.
            and runs self.htt_add_request_to_list with received tab
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, BACK_FRONT_SCOPEREQUESTS_PORT))
            s.listen()

            while not self.gui.stop_threads:
                conn, addr = s.accept()

                with conn:
                    serialized_reqeust = conn.recv(4096)
                    if serialized_reqeust:
                        try:
                            deserialized_request = pickle.loads(serialized_reqeust)
                            request2 = Request2.from_request(deserialized_request)

                            self.intercepted_request = request2
                            self.show_request()

                        except Exception as e:
                            print(f"Error while deserialization recieved in scope: {e}")

    def show_request(self):
        """
        Intercept Tab:
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
        self.request_authority_entry.insert("0", authority)
        self.request_textbox.insert_text(request_content)
        self.placeholder_widget.grid_forget()
        self.request_widget.grid(row=1, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="nsew")

        for button in self.top_bar_buttons:
            if str(button.cget("state") != "normal"):
                button.configure(state="normal")

    def remove_request(self):
        """
        Intercept Tab:
            Hides request info and HTTP message after dropping, forwarding it.
        """
        self.intercepted_request = None

        self.request_host_entry.delete("0", tk.END)
        self.request_port_entry.delete("0", tk.END)
        self.request_scheme_entry.delete("0", tk.END)
        self.request_authority_entry.delete("0", tk.END)
        self.request_textbox.insert_text("")
        self.request_widget.grid_forget()
        self.placeholder_widget.grid(row=1, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="nsew")

        for button in self.top_bar_buttons:
            if str(button.cget("state") != "disabled"):
                button.configure(state="disabled")

    def forward_request(self):
        """
        Intercept Tab:
            Sends a request from Intercept tab textbox, request is forwarded to web browser.
        """
        request_content = self.request_textbox.get_text().replace("\r", "")

        if len(request_content) > 0:
            request2 = Request2.from_http_message(request_content)
            request2.host = self.intercepted_request.host
            request2.port = self.intercepted_request.port
            request2.scheme = self.intercepted_request.scheme
            request2.authority = self.intercepted_request.authority

            request = request2.to_request()
            serialized_reqeust = pickle.dumps(request)

            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((HOST, FRONT_BACK_FORWARDBUTTON_PORT))
                    s.sendall(serialized_reqeust)
                    self.remove_request()
            except Exception as e:
                print(f"ERROR/FRONTEND/PROXY: Forwarding intercepted request failed: {e}")

    def drop_request(self):
        """
        Intercept Tab:
            Removes a request from list in GUI, request is dropped, proxy sends "request dropped info".
        """
        request_content = self.request_textbox.get_text()

        if len(request_content) > 0:
            flag = "True"
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((HOST, FRONT_BACK_DROPREQUEST_PORT))
                    serialized_flag = flag.encode("utf-8")
                    s.sendall(serialized_flag)
                    self.remove_request()
            except Exception as e:
                print(f"ERROR/FRONTEND/PROXY: Droping intercepted request failed: {e}")

            try:
                if self.gui.browser is not None:
                    # self.gui.browser.quit()
                    if len(self.gui.browser.window_handles) > 0:
                        self.gui.browser.execute_script(
                            "alert('WASTT: Request has been dropped by user. Please close this page.');")
            except Exception as e:
                print(f"Error while letting know about dropped request: {e}")

    def send_request(self, dest):
        request_content = self.request_textbox.get_text()
        try:
            hostname_url = self.intercepted_request.host
            if dest == "intruder":
                self.gui.intruder_tab.add_request_to_intruder_tab(request_content, host=hostname_url)
            elif dest == "repeater":
                self.gui.repeater_tab.add_request_to_repeater_tab(request_content, host=hostname_url)
        except Exception as e:
            print(f"Error while sending request from Intercept: {e}")

    def update_scope(self, mode="remove"):
        if mode == "remove":
            hostnames = set()

            if len(self.scope_url_list.selection()) > 0:
                for selected_item in self.scope_url_list.selection():
                    hostnames.add(self.scope_url_list.item(selected_item)['values'][0])

            if len(hostnames) > 0:
                self.proxy_gui.update_scope(mode, hostnames)

        elif mode == "clear":
            self.proxy_gui.update_scope(mode)


class GUIProxy(ctk.CTkFrame):
    """
        GUI for Proxy Tab of WASTT.
        Constist of three sub tabs: HTTP Traffic, Intercept and Scope
    """

    def __init__(self, master, root):
        super().__init__(master)
        self.process = None
        self.configure(fg_color=color_bg_br, bg_color="transparent", corner_radius=10)
        self.root = root
        self.intercepting = root.intercepting

        # Proxy tabs nav
        self.http_traffic_tab = HTTPTrafficTab(self, self.root)
        self.intercept_tab = InterceptTab(self, self.root)
        self.tabs = {
            "HTTP Traffic": self.http_traffic_tab,
            "Intercept": self.intercept_tab
        }
        self.tab_nav = ctk.CTkFrame(self, fg_color="transparent")
        self.tab_nav.pack(side="top", fill="x", padx=15, pady=(10, 0))
        self.tab_nav_buttons = {}
        for tab in self.tabs.keys():
            self.tab_nav_buttons[tab] = NavButton(self.tab_nav, text=tab, command=lambda t=tab: self.switch_tab(t),
                                                  font=ctk.CTkFont(family="Calibri", size=14, weight="normal"),
                                                  background=color_bg_br, background_selected=color_bg)
            self.tab_nav_buttons[tab].pack(side="left")

        # Initialising WebInterceptor scope items
        self.add_to_scope_dialog = None
        self.add_to_scope_dialog_notice = None
        self.current_scope = set()

        # Initialising backend for the Proxy tab. - Running mitmproxy at start
        threading.Thread(target=self.intercept_tab.receive_request, daemon=True).start()
        threading.Thread(target=self.http_traffic_tab.receive_request, daemon=True).start()
        self.deserialized_flow = None

        if not self.process:
            threading.Thread(target=self.run_mitmdump).start()
        self.intercepting = True

        self.switch_tab("HTTP Traffic")

    def run_mitmdump(self):
        """
        Proxy GUI:
            Runs mitmdump process after first killing all the mitdmdump.exe processes.
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
        except Exception as e:
            print(f"Error while starting the HTTP(S) proxy process: {e}")
        finally:
            self.process = None

    def read_stdout(self):
        """
        Proxy GUI:
            Reads Standard Out lines from running mitmdump process.
        """
        for line in iter(self.process.stdout.readline, ''):
            print(f"INFO (mitmdump): {line.strip()}")

    def read_stderr(self):
        """
        Proxy GUI:
            Reads Standard Error lines from running mitmdump process.
        """
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

    def update_browser_buttons(self):
        """
        Proxy GUI:
            Updates text of the Open browser button
        """
        if self.root.browser_opened:
            self.intercept_tab.browser_button.configure(text="Go to browser")
            self.http_traffic_tab.browser_button.configure(text="Go to browser")
        else:
            self.intercept_tab.browser_button.configure(text="Open browser")
            self.http_traffic_tab.browser_button.configure(text="Open browser")

    def submit_new_scope_hostname_dialog(self):
        """
        Proxy GUI:
            Opens a dialog to add a custom hostname to Scope.
        """
        self.add_to_scope_dialog = ctk.CTkToplevel(self)
        self.add_to_scope_dialog.title("Add hostname to the Scope")
        self.add_to_scope_dialog.geometry("300x150")
        self.add_to_scope_dialog.attributes("-topmost", True)
        center_window(self.root, self.add_to_scope_dialog, 300, 150)

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
        Proxy GUI:
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
        Proxy GUI:
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
                print(f"PROXY SCOPE ERROR: File {file_path} could not be open. Default settings have been loaded.")

    def update_scope(self, mode="add", hostnames_to_update=None):
        """
        Proxy GUI:
            Updates (adds, removes, clears) the current scope for Web Interceptor.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if mode == "add":
                    hostnames_to_update -= self.current_scope
                if mode == "clear":
                    hostnames_to_update = set()

                data_to_send = (mode, *hostnames_to_update)
                serialized_data = pickle.dumps(data_to_send)
                s.connect((HOST, FRONT_BACK_SCOPEUPDATE_PORT))
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

        except Exception as e:
            print(f"ERROR FRONTEND PROXY: Error while updating ({mode}) WebInterceptor scope: {e}")

        self.intercept_tab.interceptor_status_update()

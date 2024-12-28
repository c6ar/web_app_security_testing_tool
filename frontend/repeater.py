from common import *


class RepeaterTab(ctk.CTkFrame):
    def __init__(self, master, id_number=0, content=None, hosturl=None):
        super().__init__(master)
        self.hosturl = hosturl
        self.configure(
            fg_color=color_bg,
            corner_radius=10,
            background_corner_colors=(color_bg_br, color_bg_br, color_bg_br, color_bg_br)
        )
        self.gui = master
        self.id = id_number
        self.is_empty = True

        logs_path = Path(RUNNING_CONFIG["logs_location"]) / "repeater"
        logs_path.mkdir(parents=True, exist_ok=True)
        self.log_file = logs_path / f"repeater-{today}.log"

        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.hosturl_label = ctk.CTkLabel(self.top_bar, text="Host URL")
        self.hosturl_label.pack(padx=10, pady=10, side="left")

        self.hosturl_entry = TextEntry(self.top_bar, width=350)
        if self.hosturl is not None:
            self.hosturl_entry.insert(0, self.hosturl)
        self.hosturl_entry.pack(padx=(0, 10), pady=10, side="left")
        self.hosturl_entry.bind("<KeyRelease>", self.on_request_textbox_change)

        self.send_button = ActionButton(
            self.top_bar,
            text="Send",
            image=icon_arrow_up,
            command=self.send_request_from_repeater,
            state=tk.DISABLED
        )
        self.send_button.pack(padx=10, pady=10, side="left")

        self.tab_iterations = {}
        self.tab_iteration_keys = []

        self.iteration_var = tk.StringVar(self.top_bar)
        self.iteration_var.set("Select Iteration")

        self.iteration_dropdown = ctk.CTkOptionMenu(
            self.top_bar,
            variable=self.iteration_var,
            values=[],
            command=self.select_iteration,
            state=tk.DISABLED,
            width=200
        )
        self.iteration_dropdown.pack(side="left", padx=5, pady=10)

        info_button = InfoButton(
            self.top_bar,
            self,
            "http://localhost:8080/en/repeater.html"
        )
        info_button.pack(side=tk.RIGHT, padx=5, pady=0)

        self.gen_button = ActionButton(
            self.top_bar,
            text="Generate a request",
            image=icon_random,
            command=self.generate_request,
        )
        if RUNNING_CONFIG["debug_mode"]:
            self.gen_button.pack(padx=10, pady=10, side=tk.RIGHT)

        if self.id != 0:
            self.delete_tab_button = ActionButton(
                self.top_bar,
                text="Delete the card",
                image=icon_delete,
                command=lambda: self.gui.delete_tab(self.id),
            )
            self.delete_tab_button.pack(padx=10, pady=10, side="right")

        self.request_header = HeaderTitle(self, text="Request")
        self.request_header.grid(row=1, column=0, padx=10, pady=(5, 0), sticky="w")

        self.request_textbox = TextBox(self, text="Enter request here.")
        self.request_textbox.configure(font=self.request_textbox.monoscape_font_italic)
        self.request_textbox.grid(row=2, column=0, padx=(20, 10), pady=(0, 20), sticky="nsew")
        if content is not None:
            self.request_textbox.insert_text(content)
            self.is_empty = False
        self.request_textbox.bind("<<Modified>>", self.on_request_textbox_change)

        self.response_header = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent", bg_color="transparent")
        self.response_header.grid(row=1, column=1, padx=(10, 20), pady=(5, 0), sticky="we")

        self.response_header_title = HeaderTitle(self.response_header, text="Response")
        self.response_header_title.pack(side=tk.LEFT, padx=0, pady=0)

        self.response_textbox = TextBox(self, text="Response will appear here.")
        self.response_textbox.configure(state="disabled", font=self.response_textbox.monoscape_font_italic)
        self.response_textbox.grid(row=2, column=1, padx=(10, 20), pady=(0, 20), sticky="nsew")

        self.response_render_button = ActionButton(
            self.response_header,
            text="Show response render",
            command=lambda: show_response_view(self.gui, self.hosturl_entry.get(), self.response_textbox.get_text()),
            state=tk.DISABLED
        )
        self.response_render_button.pack(side=tk.RIGHT, padx=0, pady=0)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

    def update_number(self, id_number):
        self.id = id_number
        if self.id != 0:
            self.delete_tab_button.configure(
                command=lambda: self.gui.delete_tab(self.id)
            )

    def on_request_textbox_change(self, _event):
        self._reset_request_modified_flag()
        if len(self.request_textbox.get_text()) > 0 and self.request_textbox.get_text() != "Enter request here.":
            self.is_empty = False
            self.request_textbox.configure(font=self.request_textbox.monoscape_font)
            if len(self.hosturl_entry.get()) > 0:
                self.send_button.configure(state=tk.NORMAL)
            else:
                self.send_button.configure(state=tk.DISABLED)
        else:
            self.is_empty = True
            self.request_textbox.configure(font=self.request_textbox.monoscape_font_italic)
            self.send_button.configure(state=tk.DISABLED)

    def _reset_request_modified_flag(self):
        self.request_textbox.edit_modified(False)

    def send_request_from_repeater(self):
        request_text = self.request_textbox.get_text()
        request_host = self.hosturl_entry.get()
        if len(request_text) > 0 and len(request_host) > 0:
            try:
                response = send_http_message(request_text, real_url=request_host)
                response_text = process_response(response)
                self.add_response_to_repeater_tab(response_text)

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                with open(self.log_file, "a", encoding="utf-8", errors="replace") as file:
                    file.write(f"\n[{timestamp}] Request to {request_host}:\n{request_text}")
                    file.write(f"\n[{timestamp}] Response from {request_host}:\n{response_text}")

                self.tab_iterations[timestamp] = [request_text, response_text]
                self.tab_iteration_keys.insert(0, timestamp)
                self.update_dropdown_menu()
            except Exception as e:
                ErrorDialog(self, self.gui, e)

    def add_response_to_repeater_tab(self, response):
        self.response_textbox.configure(state=tk.NORMAL)
        self.response_textbox.insert_text(response)
        self.response_textbox.configure(state=tk.DISABLED)
        self.response_render_button.configure(state=tk.NORMAL)

    def update_dropdown_menu(self):
        self.iteration_dropdown.configure(values=self.tab_iteration_keys, state=tk.NORMAL)
        if self.tab_iteration_keys:
            recent_iteration = self.tab_iteration_keys[0]
            self.iteration_var.set(recent_iteration)

    def select_iteration(self, iteration_name):
        if iteration_name in self.tab_iteration_keys:
            self.load_iteration(iteration_name)

    def load_iteration(self, iteration_name):
        request_text, response_text = self.tab_iterations[iteration_name]
        self.request_textbox.configure(state=tk.NORMAL)
        self.response_textbox.configure(state=tk.NORMAL)
        self.request_textbox.delete("1.0", tk.END)
        self.request_textbox.insert_text(request_text)
        self.response_textbox.delete("1.0", tk.END)
        self.response_textbox.insert_text(response_text)
        self.response_textbox.configure(state=tk.DISABLED)
        self.response_render_button.configure(state=tk.NORMAL)

    def generate_request(self):
        url = "https://www.example.com"
        http_request = "GET / HTTP/2.0"

        self.request_textbox.insert_text(http_request)
        self.hosturl_entry.delete(0, tk.END)
        self.hosturl_entry.insert(0, url)


class Repeater(ctk.CTkFrame):
    def __init__(self, master, root):
        super().__init__(master)
        self.configure(fg_color=color_bg_br, bg_color="transparent", corner_radius=10)
        self.root = root

        self.tabs = []
        self.tab_nav = ctk.CTkFrame(self, fg_color="transparent")
        self.tab_nav.pack(side="top", fill="x", padx=25, pady=(10, 0))
        self.current_tab = 0
        self.tab_nav_buttons = []
        first_tab_button = NavButton(self.tab_nav, text="1",
                                     command=lambda: self.show_tab(0),
                                     background=color_bg_br,
                                     background_selected=color_bg)
        self.tab_nav_buttons.append(first_tab_button)
        first_tab_button.pack(side="left")
        self.tab_add_button = NavButton(self.tab_nav, text="",
                                        icon=icon_add,
                                        command=self.add_tab,
                                        background=color_bg_br,
                                        background_selected=color_bg)
        self.tab_add_button.pack(side="right")
        self.tabs.append(RepeaterTab(self, 0))
        self.show_tab(self.current_tab)

    def add_tab(self, new_tab=None):
        new_tab_id = len(self.tab_nav_buttons)
        new_tab_nav_button = NavButton(self.tab_nav, text=str(new_tab_id + 1),
                                       command=lambda: self.show_tab(new_tab_id),
                                       background=color_bg_br,
                                       background_selected=color_bg
                                       )
        self.tab_nav_buttons.append(new_tab_nav_button)
        new_tab_nav_button.pack(side="left", padx=(10, 0))

        if new_tab is None:
            new_tab = RepeaterTab(self, new_tab_id)
        self.tabs.append(new_tab)
        self.show_tab(new_tab_id)

    def show_tab(self, tab_id):
        self.current_tab = tab_id
        for i, tab in enumerate(self.tabs):
            if i == tab_id:
                self.tab_nav_buttons[i].select(True)
                tab.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 10))
            else:
                self.tab_nav_buttons[i].select(False)
                tab.pack_forget()

    def delete_tab(self, tab_id):
        if self.current_tab == tab_id:
            self.show_tab(tab_id - 1)

        self.tabs.pop(tab_id)
        self.tab_nav_buttons[tab_id].pack_forget()
        self.tab_nav_buttons.pop(tab_id)

        self.update_tab_numbering()

    def update_tab_numbering(self):
        for i, button in enumerate(self.tab_nav_buttons):
            button.main_button.configure(text=str(i + 1), command=lambda t=i: self.show_tab(t))
            self.tabs[i].update_number(i)

    def add_request_to_repeater_tab(self, content, host=None):
        for tab in self.tabs:
            if tab.is_empty:
                tab.hosturl = host
                tab.hosturl_entry.insert(0, host)
                tab.request_textbox.insert_text(content)
                tab.is_empty = False
                return
        else:
            new_tab = RepeaterTab(self, len(self.tab_nav_buttons), content, host)
            self.add_tab(new_tab)

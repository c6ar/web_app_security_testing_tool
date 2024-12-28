from backend.intruder import *
from common import *


class IntruderResult(ctk.CTkToplevel):
    def __init__(self, master, gui, hostname, positions, payloads, timestamp, q, control_flags, **kwargs):
        super().__init__(master, **kwargs)
        self.queue = q
        self.title(f"Intruder Attack on {hostname}")
        self.intruder_tab = master
        self.root = gui.gui_root
        self.focus_set()
        self.transient(gui.gui_root)
        self.configure(fg_color=color_bg, bg_color=color_bg)
        self.root.after(100, self.check_queue)
        self.after(250, self.iconbitmap, f"{ASSET_DIR}\\wastt.ico", "")
        width = int(int(self.root.winfo_width()) * 0.9)
        height = int(int(self.root.winfo_height()) * 0.9)
        center_window(self.root, self, width, height)

        self.hostname = hostname
        self.timestamp = timestamp

        logs_path = Path(RUNNING_CONFIG["logs_location"]) / "intruder"
        logs_path.mkdir(parents=True, exist_ok=True)
        self.log_file = logs_path / f"intruder-{today}.log"

        with open(self.log_file, "a", encoding="utf-8", errors="replace") as file:
            file.write(f"\n[{self.timestamp}] Started attack on {self.hostname}.")

        self.control_flags = control_flags
        self.attack_paused = False
        self.attack_ceased = False

        self.top_bar = Box(self)
        self.top_bar.pack(side=tk.TOP, fill=tk.X, padx=15, pady=(5, 0))
        self.attack_start_label = Label(self.top_bar, text=f"Attack on: {self.hostname} started at {self.timestamp}.")
        self.attack_start_label.pack(side=tk.LEFT, padx=(20, 0))
        self.pause_button = ActionButton(
            self.top_bar,
            text="Pause",
            image=icon_pause,
            command=self.pause_attack,
            fg_color=color_bg,
            hover_color=color_bg_br
        )
        self.pause_button.pack(side=tk.LEFT, padx=(10, 0))
        self.abort_button = ActionButton(
            self.top_bar,
            text="Abort",
            image=icon_abort,
            command=self.abort_attack,
            fg_color=color_bg,
            hover_color=color_bg_br
        )
        self.abort_button.pack(side=tk.LEFT, padx=(10, 0))
        self.attack_status_label = Label(self.top_bar, text=f"Attack is ongoing.")
        self.attack_status_label.pack(side=tk.LEFT, padx=(10, 0))

        self.tab_nav_bar = Box(self)
        self.tab_nav_bar.pack(side=tk.TOP, fill=tk.X, padx=15, pady=(5, 0))

        self.results_tab = BrightBox(self)
        self.positions_tab = BrightBox(self)

        self.tabs = {
            "Results": self.results_tab,
            "Positions": self.positions_tab
        }
        self.tab_nav_buttons = {}
        for name in self.tabs.keys():
            self.tab_nav_buttons[name] = NavButton(self.tab_nav_bar, text=name.upper(),
                                                   command=lambda t=name: self.show_tab(t))
            self.tab_nav_buttons[name].pack(side=tk.LEFT)

        self.add_random_button = NavButton(self.tab_nav_bar, text="Add random request", icon=icon_random,
                                           command=self.generate_random_request)
        if RUNNING_CONFIG["debug_mode"]:
            self.add_random_button.pack(side=tk.RIGHT)

        """
         > RESULTS TAB
        """
        self.results_paned_window = tk.PanedWindow(self.results_tab, orient=tk.VERTICAL, sashwidth=10,
                                                   background=color_bg_br)
        self.results_paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.top_frame = ctk.CTkFrame(self.results_paned_window, corner_radius=10, fg_color=color_bg,
                                      bg_color="transparent")
        self.results_paned_window.add(self.top_frame, height=350)

        request_columns = ("Request No.", "Position", "Payload", "Status code", "Error", "Timeout", "Length",
                           "Request Content", "Response Content")
        self.attack_request_list = ItemList(self.top_frame, columns=request_columns, show="headings", style="Treeview")
        self.attack_request_list.bind("<<TreeviewSelect>>", self.show_request_content)
        self.attack_request_list.bind("<Button-1>", self.on_click_outside_item)
        for col in request_columns:
            if col in ("Request Content", "Response Content"):
                self.attack_request_list.heading(col, text=col)
                self.attack_request_list.column(col, width=0, stretch=tk.NO)
            else:
                self.attack_request_list.heading(col, text=col)
                self.attack_request_list.column(col, width=100)
        self.attack_request_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.bottom_frame = ctk.CTkFrame(self.results_paned_window, corner_radius=10, fg_color=color_bg,
                                         bg_color="transparent")

        self.bottom_frame.grid_columnconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(1, weight=1)
        self.bottom_frame.grid_rowconfigure(0, weight=1)

        self.request_frame = ctk.CTkFrame(self.bottom_frame, fg_color=color_bg)
        self.request_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.request_header = HeaderTitle(self.request_frame, "Request")
        self.request_header.pack(fill=tk.X)

        self.request_textbox = TextBox(self.request_frame, "Select request to display its contents.")
        self.request_textbox.configure(state=tk.DISABLED)
        self.request_textbox.pack(pady=10, padx=10, fill="both", expand=True)

        self.response_frame = ctk.CTkFrame(self.bottom_frame, fg_color=color_bg, bg_color="transparent")
        self.response_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.response_header = ctk.CTkFrame(self.response_frame, fg_color="transparent", bg_color="transparent")
        self.response_header.pack(fill=tk.X)

        self.response_header_title = HeaderTitle(self.response_header, "Response")
        self.response_header_title.pack(side=tk.LEFT)

        self.response_textbox = TextBox(self.response_frame, "Select request to display its response contents.")
        self.response_textbox.configure(state=tk.DISABLED)
        self.response_textbox.pack(pady=10, padx=10, fill="both", expand=True)

        self.response_render_button = ActionButton(
            self.response_header,
            text="Show response render",
            command=lambda: show_response_view(self.root, self.hostname, self.response_textbox.get_text())
        )
        self.response_render_button.pack(side=tk.RIGHT, padx=(0, 10))

        """
         > POSITIONS TAB
        """
        self.wrapper = ctk.CTkFrame(self.positions_tab, fg_color=color_bg, bg_color="transparent", corner_radius=10)
        self.wrapper.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.request_header = HeaderTitle(self.wrapper, text="Positions")
        self.request_header.grid(row=1, column=0, padx=10, pady=(5, 0), sticky="w")

        self.positions_textbox = TextBox(self.wrapper, text="Enter request here.")
        self.positions_textbox.insert_text(positions.get_text())

        tags = positions.tag_names()
        for tag in tags:
            tag_ranges = positions.tag_ranges(tag)
            for start, end in zip(tag_ranges[0::2], tag_ranges[1::2]):
                self.positions_textbox.tag_add(tag, start, end)
                self.positions_textbox.tag_config(tag, background=color_highlight_bg, foreground=color_highlight)
        self.positions_textbox.configure(state=tk.DISABLED)
        self.positions_textbox.grid(row=2, column=0, padx=(20, 10), pady=(0, 20), sticky="nsew")

        self.payloads_header = HeaderTitle(self.wrapper, text="Sent payloads")
        self.payloads_header.grid(row=1, column=1, padx=10, pady=(5, 0), sticky="w")

        if self.intruder_tab.attack_type == 2:
            self.payloads_frame = ctk.CTkScrollableFrame(self.wrapper, fg_color="transparent", bg_color="transparent")
            for var, payloads in payloads.items():
                payloads_label = ctk.CTkLabel(self.payloads_frame, text=f"Payloads for positions of \"{var}\"",
                                              anchor=tk.W, justify=tk.LEFT)
                payloads_label.pack(fill=tk.X, padx=10, pady=(10, 0))
                payloads_textbox = TextBox(self.payloads_frame, text=payloads.get_text(), height=150)
                payloads_textbox.pack(fill=tk.X, padx=10, pady=(10, 0))
        else:
            self.payloads_textbox = TextBox(self.wrapper, text=payloads.get(0).get_text())
            self.payloads_textbox.grid(row=2, column=1, padx=(10, 20), pady=(0, 20), sticky="nsew")

        self.wrapper.grid_columnconfigure(0, weight=1)
        self.wrapper.grid_columnconfigure(1, weight=1)
        self.wrapper.grid_rowconfigure(2, weight=1)

        self.show_tab("Results")
        self.flow = None

        self.close_dialog = None
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        if not self.attack_ceased:
            confirm = ConfirmDialog(
                self,
                self.root,
                "There is currently attack pending. Do you want to close the window?",
                "Warning",
                "Cancel",
                lambda: confirm.destroy(),
                "Keep attack in the background",
                lambda: (self.withdraw(), self.root.focus_set(), confirm.destroy(), self.root.deiconify()),
                "Abort the attack",
                lambda: (self.abort_attack(), self.withdraw(), confirm.destroy(), self.root.deiconify()),
                width=550,
                height=100
            )
        else:
            self.withdraw()

    def show_tab(self, tab_name):
        for name, tab in self.tabs.items():
            if name == tab_name:
                tab.pack(side="top", fill="both", expand=True)
                self.tab_nav_buttons[name].select(True)
            else:
                tab.pack_forget()
                self.tab_nav_buttons[name].select(False)

    def show_request_content(self, _event):
        if len(self.attack_request_list.selection()) > 0:
            selected_item = self.attack_request_list.selection()[0]
            request_string = self.attack_request_list.item(selected_item)['values'][-2]
            response_string = self.attack_request_list.item(selected_item)['values'][-1]
            self.request_textbox.configure(state=tk.NORMAL, font=self.request_textbox.monoscape_font)
            self.request_textbox.insert_text(request_string)
            self.request_textbox.configure(state=tk.DISABLED)
            self.response_textbox.configure(state=tk.NORMAL, font=self.response_textbox.monoscape_font)
            self.response_textbox.insert_text(response_string)
            self.response_textbox.configure(state=tk.DISABLED)
            self.results_paned_window.add(self.bottom_frame)
        else:
            self.results_paned_window.remove(self.bottom_frame)
            self.request_textbox.configure(state=tk.NORMAL)
            self.request_textbox.insert_text("Select a request to display its contents.")
            self.request_textbox.configure(state=tk.DISABLED, font=self.request_textbox.monoscape_font_italic)
            self.response_textbox.configure(state=tk.NORMAL)
            self.response_textbox.insert_text("Select a request to display contents of its response.")
            self.response_textbox.configure(state=tk.DISABLED, font=self.response_textbox.monoscape_font_italic)

    def on_click_outside_item(self, event):
        region = self.attack_request_list.identify_region(event.x, event.y)
        if region != "cell":
            self.attack_request_list.selection_remove(self.attack_request_list.selection())

    def generate_random_request(self):
        rn = len(self.attack_request_list.get_children()) + 1
        pos = random.randint(1, len(self.positions_textbox.tag_names()))
        payload = random.choice(["Test", "LOL", "XD", "ABC", "123", "LoremIpsum", "Etc"])
        status_code = f"{random.choice(['400', '401', '402', '403', '404'])}"
        error = False
        timeout = False
        req_con = f"HTTP/1.1\nHost: {self.hostname}\nValue = {payload}\nProxy-Connection: keep-alive\n{random.choice(['random stuff here', 'Header Lorem Ipsum', 'ETC...'])}\n"
        res_con = f"{status_code} \n{random.choice(['Response Lorem Ipsum.', 'Some HTTP gibberish here.'])}\nEnd of Response."
        length = len(res_con)
        random_request = [rn, pos, payload, status_code, error, timeout, length, req_con, res_con]

        self.attack_request_list.insert("", tk.END, values=random_request)
        if len(self.attack_request_list.selection()) == 0:
            self.attack_request_list.selection_add(self.attack_request_list.get_children()[0])

    def add_attack_flow(self, data):
        if 'status' not in data.keys():
            try:
                children = self.attack_request_list.get_children()
            except tk.TclError:
                dprint("Warn: attack_request_list widget does not exist. Skipping add_attack_flow.")
                return

            rn = len(children) + 1
            pos = data['position']
            payload = data['payload']
            status_code = data['status_code']
            error = data['error']
            timeout = data['timeout']
            request_content = data['req_con']
            response_content = data['res_con']
            length = len(response_content)
            values = [rn, pos, payload, status_code, error, timeout, length, request_content, response_content]

            if self.attack_request_list:
                self.attack_request_list.insert("", tk.END, values=values)

            with open(self.log_file, "a", encoding="utf-8", errors="replace") as file:
                timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
                file.write(f"\n[{timestamp}] Payload [{payload}] at position #{pos}:\n{request_content}")
                file.write(f"\n[{timestamp}] Response {status_code}:\n{response_content}")

        else:
            finish_timestamp = datetime.now().strftime("%H:%M:%S %d-%m-%Y")
            self.attack_ceased = True
            self.abort_button.pack_forget()
            self.pause_button.pack_forget()
            if data['status'] == 'completed':
                self.attack_status_label.configure(text=f"Attack completed at {finish_timestamp}.")
                op = "completed"

            elif data['status'] == 'aborted':
                self.attack_status_label.configure(text=f"Attack aborted at {finish_timestamp}.")
                op = "aborted"

            else:
                op = "error"

            with open(self.log_file, "a", encoding="utf-8", errors="replace") as file:
                file.write(f"\n[{finish_timestamp}] Attack {op}.")

    def check_queue(self):
        while not self.queue.empty():
            try:
                data = self.queue.get()
                self.add_attack_flow(data)
            except Exception as e:
                dprint(f"Error INTR001: {e}")
        self.root.after(100, self.check_queue)

    def pause_attack(self):
        if self.attack_paused:
            self.control_flags["pause"].clear()
            self.pause_button.configure(text="Pause", image=icon_pause)
            self.attack_status_label.configure(text="Attack is ongoing.")
        else:
            self.control_flags["pause"].set()
            self.pause_button.configure(text="Resume", image=icon_start)
            self.attack_status_label.configure(text="Attack is paused.")
        self.attack_paused = not self.attack_paused

    def abort_attack(self):
        self.control_flags["abort"].set()


class IntruderTab(ctk.CTkFrame):
    def __init__(self, master, unique_id, visual_id, content=None, hostname=None):
        super().__init__(master)
        self.configure(
            fg_color=color_bg,
            corner_radius=10,
            background_corner_colors=(color_bg_br, color_bg_br, color_bg_br, color_bg_br)
        )
        self.gui = master
        self.unique_id = unique_id
        self.id = visual_id
        self.hostname = hostname
        self.is_empty = True if content is None else False

        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 0), sticky="ew")

        self.attack_type_label = ctk.CTkLabel(self.top_bar, text="Attack type")
        self.attack_type_label.pack(padx=(20, 5), pady=10, side="left")

        self.attack_type_options = [
            "Sniper attack",
            "Battering ram attack",
            "Pitchfork attack"
        ]
        selected_option = tk.StringVar(value=self.attack_type_options[0])
        self.attack_type_dropdown = ctk.CTkOptionMenu(
            self.top_bar,
            width=200,
            corner_radius=10,
            variable=selected_option,
            values=self.attack_type_options,
            command=self.on_attack_option_select
        )
        self.attack_type_dropdown.pack(padx=(0, 10), pady=10, side=tk.LEFT)
        self.attack_type = 0

        self.attack_button = ActionButton(
            self.top_bar,
            text="Start attack",
            image=icon_attack,
            command=self.on_attack_button_click,
            state=tk.DISABLED
        )
        self.attack_button.pack(padx=10, pady=10, side=tk.LEFT)
        self.reload_dialog = None
        self.results_button = ActionButton(
            self.top_bar,
            text="Show attack results",
            image=icon_logs,
            command=self.show_attack,
            state=tk.DISABLED
        )
        self.results_button.pack(padx=10, pady=10, side=tk.LEFT)
        self.attack_info = Label(
            self.top_bar,
            text="No attack started.",
            anchor="w"
        )
        self.attack_info.pack(padx=10, pady=10, side=tk.LEFT)

        self.attack_timestamp = None
        self.control_flags = {
            "pause": Event(),
            "abort": Event()
        }

        if self.id != 0:
            self.delete_frame_button = ActionButton(
                self.top_bar,
                text="Delete the card",
                width=30,
                image=icon_delete,
                command=lambda: self.gui.delete_tab(self.id),
                compound="left",
                corner_radius=32
            )
            self.delete_frame_button.pack(padx=10, pady=10, side=tk.RIGHT)

        info_button = InfoButton(
            self.top_bar,
            self,
            "http://localhost:8080/en/intruder.html"
        )
        info_button.pack(side=tk.RIGHT, padx=5, pady=0)

        self.gen_button = ActionButton(
            self.top_bar,
            text="Generate an attack",
            image=icon_random,
            command=self.generate_seed_intrusion
        )
        if RUNNING_CONFIG["debug_mode"]:
            self.gen_button.pack(padx=10, pady=10, side=tk.RIGHT)

        self.left_column = ctk.CTkFrame(self, fg_color="transparent", bg_color="transparent")
        self.left_column.grid(row=1, column=0, padx=(10, 5), pady=(0, 10), sticky="nsew")

        self.positions_header = ctk.CTkFrame(self.left_column, fg_color="transparent", bg_color="transparent")
        self.positions_header.pack(side=tk.TOP, fill=tk.X, padx=10, pady=0)

        self.positions_header_title = HeaderTitle(self.positions_header, "Positions")
        self.positions_header_title.pack(side=tk.LEFT, padx=(0, 10), pady=0)

        self.add_button = ActionButton(
            self.positions_header,
            text="Add position",
            image=icon_add,
            command=self.add_position
        )
        self.add_button.pack(side=tk.LEFT, padx=5, pady=0)

        self.clear_button = ActionButton(
            self.positions_header,
            text="Clear position(s)",
            image=icon_delete,
            command=self.clear_position,
            fg_color=color_acc3,
            hover_color=color_acc4
        )
        self.clear_button.pack(side=tk.LEFT, padx=5, pady=0)

        self.positions_textbox = TextBox(self.left_column, text="")
        self.positions_textbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        if content is not None:
            self.positions_textbox.insert_text(content)
        self.positions_textbox.bind("<<Modified>>", self.on_positions_textbox_change)

        self.positions_var_gen_id = 0

        self.right_column = ctk.CTkFrame(self, fg_color="transparent", bg_color="transparent")
        self.right_column.grid(row=1, column=1, padx=(5, 10), pady=(0, 10), sticky="nsew")

        self.target_bar = ctk.CTkFrame(self.right_column, fg_color="transparent", bg_color="transparent")
        self.target_bar.pack(side=tk.TOP, fill=tk.X, padx=(0, 10), pady=0)

        self.target_bar_title = HeaderTitle(self.target_bar, "Target")
        self.target_bar_title.pack(side=tk.LEFT, padx=(0, 10), pady=0)

        self.hostname_entry = TextEntry(self.target_bar, width=350)
        if self.hostname is not None:
            self.hostname_entry.insert(0, self.hostname)
        self.hostname_entry.pack(side=tk.LEFT, padx=(0, 10), pady=0)
        self.hostname_entry.bind("<KeyRelease>", self.on_positions_textbox_change)

        self.payloads_header = ctk.CTkFrame(self.right_column, fg_color="transparent", bg_color="transparent")
        self.payloads_header.pack(side=tk.TOP, fill=tk.X, padx=(0, 10), pady=0)

        self.payloads_header_title = HeaderTitle(self.payloads_header, "Payloads")
        self.payloads_header_title.pack(side=tk.LEFT, padx=(0, 10), pady=0)

        self.payloads_textbox_var = tk.StringVar(self.payloads_header)
        self.payloads_textbox_var.set("All")
        self.payloads_textbox_dropdown = ctk.CTkOptionMenu(
            self.payloads_header,
            width=200,
            corner_radius=10,
            variable=self.payloads_textbox_var,
            values=[],
            command=self.switch_payloads_textbox,
            state=tk.DISABLED,
        )
        self.payloads_textbox_dropdown.pack(side=tk.LEFT, padx=(0, 10), pady=0)
        self.payloads_load_button = ActionButton(
            self.payloads_header,
            text="Load from file",
            image=icon_load_file,
            command=self.load_payloads
        )
        self.payloads_load_button.pack(side=tk.LEFT, padx=(0, 10), pady=0)
        self.payloads_clear_button = ActionButton(
            self.payloads_header,
            text="Clear payloads",
            image=icon_delete,
            command=self.clear_payloads,
            fg_color=color_acc3,
            hover_color=color_acc4
        )
        self.payloads_clear_button.pack(side=tk.LEFT, padx=(0, 10), pady=0)

        self.payloads_textboxes: Dict[Union[int, str], TextBox] = {0: TextBox(self.right_column)}
        self.current_payloads_textbox = self.payloads_textboxes[0]
        self.current_payloads_textbox.pack(fill=tk.BOTH, expand=True, padx=(0, 10), pady=(5, 10))

        self.payload_placeholder = ctk.CTkLabel(
            self.right_column,
            text="Add payload position to get payload frame.",
            justify="left",
            anchor="w"
        )

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.on_attack_option_select("Sniper attack")

    def update_number(self, id_number):
        self.id = id_number
        if self.id != 0:
            self.delete_frame_button.configure(
                command=lambda: self.gui.delete_tab(self.id),
            )

    def on_positions_textbox_change(self, _event):
        self._reset_positions_modified_flag()
        if len(self.positions_textbox.get_text()) > 0:
            self.is_empty = False
            if len(self.hostname_entry.get()) > 0:
                self.attack_button.configure(state=tk.NORMAL)
            else:
                self.attack_button.configure(state=tk.DISABLED)
        else:
            self.is_empty = True
            self.attack_button.configure(state=tk.DISABLED)

    def on_attack_option_select(self, choice):
        self.attack_type = self.attack_type_options.index(choice)
        self.update_payloads_textbox_dropdown()
        self.switch_payloads_textbox()

    def _reset_positions_modified_flag(self):
        self.positions_textbox.edit_modified(False)

    def on_attack_button_click(self):
        queue_id = self.unique_id
        if queue_id in self.gui.attack_queues:
            confirm = ConfirmDialog(
                master=self,
                root=self.gui.gui_root,
                title="Watch out!",
                prompt=f"The last attack was started at {self.attack_timestamp}. Do you wish to show its result or reload an attack with new parameters (previous results will be lost)?",
                action1="Reload attack",
                command1=lambda: (self.start_attack(), confirm.destroy()),
                action2="Show last attack",
                command2=lambda: (self.show_attack(), confirm.destroy()),
                height=150
            )
        else:
            self.start_attack()

    def start_attack(self):
        self.attack_timestamp = datetime.now().strftime("%H:%M:%S %d-%m-%Y")
        uuid = self.unique_id
        hostname = self.hostname_entry.get()
        request_text = self.positions_textbox.get_text()
        dprint(f"================================================\n"
               f"[DEBUG] Starting #{self.unique_id} attack on {hostname} at {self.attack_timestamp}")

        payloads = {}
        if self.attack_type != 2:
            payloads = self.payloads_textboxes[0].get_text()
        else:
            for var, textbox in self.payloads_textboxes.items():
                if var == 0:
                    continue
                payloads[var] = textbox.get_text()
        if len(payloads) == 0:
            raise ValueError("No payloads")
        dprint(f"with payloads:\n{payloads}")

        if self.attack_type != 1:
            positions = {}
            for tag in self.positions_textbox.tag_names():
                if tag == "sel":
                    continue
                ranges = self.positions_textbox.tag_ranges(tag)
                for start, end in zip(ranges[0::2], ranges[1::2]):
                    if self.attack_type == 0:
                        positions[str(start)] = str(end)
                    elif self.attack_type == 2:
                        positions[tag] = (str(start), str(end))

            if len(positions) == 0:
                raise ValueError("No positions")
            dprint(f"On positions:\n{positions}"
                   f"================================================\n")

        self.control_flags['pause'].clear()
        self.control_flags['abort'].clear()

        if uuid in self.gui.attack_queues:
            del self.gui.attack_queues[uuid]
            dprint(f"[DEBUG] Found attack queue with ID: {uuid}. Deleting it.")

        self.gui.attack_queues[uuid] = queue.Queue()
        attack_queue = self.gui.attack_queues[uuid]

        if uuid in self.gui.results_windows:
            self.gui.results_windows[uuid].destroy()
            del self.gui.results_windows[uuid]
            dprint(f"[DEBUG] Found results window ID: {uuid}. Deleting it.")

        results_window = IntruderResult(
            master=self,
            gui=self.gui,
            hostname=hostname,
            positions=self.positions_textbox,
            payloads=self.payloads_textboxes,
            timestamp=self.attack_timestamp,
            q=attack_queue,
            control_flags=self.control_flags
        )
        self.gui.results_windows[uuid] = results_window

        def producer(q, attack_type):
            if attack_type == 0:
                sniper_attack(
                    q=q,
                    request=request_text,
                    hostname=hostname,
                    wordlist=payloads,
                    positions=positions,
                    control_flags=self.control_flags
                )
            elif attack_type == 1:
                ram_attack(
                    q=q,
                    request=request_text,
                    hostname=hostname,
                    wordlist=payloads,
                    control_flags=self.control_flags
                )
            elif attack_type == 2:
                pitchfork_attack(
                    q=q,
                    request=request_text,
                    hostname=hostname,
                    wordlists=payloads,
                    positions=positions,
                    control_flags=self.control_flags
                )

        if uuid in self.gui.producer_threads:
            self.gui.producer_threads[uuid].join(timeout=1)
            del self.gui.producer_threads[uuid]
            dprint(f"[DEBUG] Found producer thread with ID: {uuid}. Deleting it.")

        producer_thread = Thread(target=producer, args=(
            attack_queue,
            self.attack_type
        ))
        producer_thread.start()
        self.gui.producer_threads[uuid] = producer_thread

        def consumer():
            while True:
                try:
                    data = attack_queue.get(timeout=1)
                    results_window.add_attack_flow(data)
                except queue.Empty:
                    continue

        if uuid in self.gui.consumer_threads:
            del self.gui.consumer_threads[uuid]
            dprint(f"[DEBUG] Found consumer thread with ID: {uuid}. Deleting it.")

        consumer_thread = Thread(target=consumer, daemon=True)
        consumer_thread.start()
        self.gui.consumer_threads[uuid] = consumer_thread

        self.attack_info.configure(text=f"Attack started at {self.attack_timestamp}.")
        self.results_button.configure(state=tk.NORMAL)

        results_window.deiconify()
        results_window.lift()
        results_window.focus_force()

    def show_attack(self):
        if self.unique_id in self.gui.results_windows:
            results_window = self.gui.results_windows[self.unique_id]
            results_window.deiconify()
            results_window.lift()
        else:
            ErrorDialog(self, self.gui.gui_root, "No attack with ID: {self.unique_id} found.")

    def generate_seed_intrusion(self):
        self.clear_all_positions()
        for name, textbox in self.payloads_textboxes.items():
            if name == 0:
                continue
            textbox.pack_forget()
            del textbox

        self.hostname_entry.delete(0, tk.END)
        self.hostname_entry.insert(0, "https://www.example.com")
        self.positions_textbox.insert_text("GET / HTTP/2.0\n"
                                           "sec-ch-ua: \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"\n"
                                           "sec-ch-ua-mobile: ?0\n"
                                           "sec-ch-ua-platform: Windows\n"
                                           "accept-language: en-GB,en;q=0.9\n"
                                           "upgrade-insecure-requests: 1\n"
                                           "user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36\n"
                                           "accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7\n"
                                           "sec-fetch-site: none\n"
                                           "sec-fetch-mode: navigate\n"
                                           "sec-fetch-user: ?1\n"
                                           "sec-fetch-dest: document\n"
                                           "accept-encoding: gzip, deflate, br, zstd\n"
                                           "priority: u=0, i\n"
                                           )
        if self.attack_type != 2:
            tags = {
                "tag1": {"start": "4.20", "end": "4.28"},
                "tag2": {"start": "12.16", "end": "12.25"},
            }
            for tag, data in tags.items():
                self.positions_textbox.insert(data["start"], "§")
                self.positions_textbox.insert(data["end"], "§")
                self.positions_textbox.tag_add(tag, data["start"], data["end"]+"+1c")
                self.positions_textbox.tag_config(tag, background=color_highlight_bg, foreground=color_highlight)
            self.payloads_textboxes[0].insert_text("Test1\nTest2\nTest3\nTest4\nTest5\n")
        elif self.attack_type == 2:
            tags = {
                "windows": {"start": "4.20", "end": "4.28", "text": "Test1\nTest2\nTest3\nTest4\nTest5\nTest6\n"},
                "navigate": {"start": "10.16", "end": "10.25", "text": "TestA\nTestB\nTestC\nTestD\n"},
                "document": {"start": "12.16", "end": "12.25", "text": "X\nY\nZ\nX\nY\n"},
            }
            for tag, data in tags.items():
                self.positions_textbox.insert(data["start"], "§")
                self.positions_textbox.insert(data["end"], "§")
                self.positions_textbox.tag_add(tag, data["start"], data["end"]+"+1c")
                self.add_payload(tag)
                self.positions_textbox.tag_config(tag, background=color_highlight_bg, foreground=color_highlight)
                self.payloads_textboxes[tag].insert_text(data["text"])

    def get_cursor_position(self):
        return self.positions_textbox.index(tk.INSERT)

    def get_selection(self):
        try:
            return self.positions_textbox.selection_get()
        except tk.TclError:
            return None

    def get_selection_indices(self):
        try:
            start_index = self.positions_textbox.index(tk.SEL_FIRST)
            end_index = self.positions_textbox.index(tk.SEL_LAST)
            return start_index, end_index
        except tk.TclError:
            return None, None

    def is_overlapping(self, start, end):
        for tag in self.positions_textbox.tag_names():
            if tag == "sel":
                continue
            tag_ranges = self.positions_textbox.tag_ranges(tag)
            dprint(f"Debug: Checking tag range: {tag_ranges}")
            for i in range(0, len(tag_ranges), 2):
                tag_start = self.positions_textbox.index(tag_ranges[i])
                tag_end = self.positions_textbox.index(tag_ranges[i + 1])
                if (self.positions_textbox.compare(start, ">=", tag_start) and self.positions_textbox.compare(start,
                                                                                                              "<",
                                                                                                              tag_end)):
                    # Case when a new tag's start is within the already existing tag
                    dprint(
                        f"Debug Intruder/Variable: You are trying to create a variable tag ({start, end}) with its beginning inside the already exisiting one ({tag_start, tag_end})!")
                    return True
                elif (self.positions_textbox.compare(end, ">", tag_start) and self.positions_textbox.compare(end, "<=",
                                                                                                             tag_end)):
                    # Case when a new tag's end is within the already existing tag
                    dprint(
                        f"Debug Intruder/Variable: You are trying to create a variable tag ({start, end}) with its ending inside the already exisiting one ({tag_start, tag_end})!")
                    return True
                elif (self.positions_textbox.compare(start, "<", tag_start) and self.positions_textbox.compare(end, ">",
                                                                                                               tag_end)):
                    # Case when the already existing tag is confined within a new tag's range
                    dprint(
                        f"Debug Intruder/Variable: You are trying to create a variable tag ({start, end}) that would contain the already exisiting one ({tag_start, tag_end})!")
                    return True
        return False

    def add_position(self):
        cursor = self.get_cursor_position()
        selection = self.get_selection()
        selection_indices = self.get_selection_indices()
        dprint(f"Debug:\n cursor pos: {cursor}\n selection: {selection}\n selection indices: {selection_indices}")

        if selection is None:
            var_name = f"var{self.positions_var_gen_id}"
            var_string = f"§{var_name}§"
            self.positions_var_gen_id += 1

            if not self.is_overlapping(cursor, cursor + "+1c"):
                self.positions_textbox.tag_config(var_name, background=color_highlight_bg, foreground=color_highlight)
                self.positions_textbox.insert(cursor, var_string)

                next_cursor = self.get_cursor_position()
                self.positions_textbox.tag_add(var_name, cursor, next_cursor)

                if self.attack_type == 2:
                    self.add_payload(var_name)
            else:
                ErrorDialog(self, self.gui.gui_root, "Cursor is overlapping with an existing tag.")
        else:
            var_name = re.sub(r'\s+', '_', selection)
            var_name = re.sub(r'[^a-zA-Z0-9_]', '', var_name)
            var_string = f"§{var_name}§"
            x, y = selection_indices

            if var_name in self.positions_textbox.tag_names():
                ErrorDialog(self, self.gui.gui_root,
                            f"Variable with the name {var_name} currently exists. Chose different name.")
                return

            if x.split('.')[0] == y.split('.')[0]:
                if not self.is_overlapping(x, y):
                    self.positions_textbox.delete(x, y)
                    self.positions_textbox.insert(x, var_string)
                    y = self.get_cursor_position()
                    self.positions_textbox.tag_config(var_name, background=color_highlight_bg, foreground=color_highlight)
                    self.positions_textbox.tag_add(var_name, x, y)
                    if self.attack_type == 2:
                        self.add_payload(var_name)
                else:
                    ErrorDialog(self, self.gui.gui_root, "Selection is overlapping with an existing tag.")
            else:
                ErrorDialog(self, self.gui.gui_root, "Selection cannot span over multiple lines!")

    def clear_position(self):
        cursor = self.get_cursor_position()
        selection = self.get_selection()
        selection_indices = self.get_selection_indices()
        dprint(f"Debug:\n cursor pos: {cursor}\n selection: {selection}\n selection indices: {selection_indices}")

        if selection is None:
            # Case 1: Cursor is within the existing tag.
            tag_found = False
            for tag in self.positions_textbox.tag_names():
                if tag == "sel":
                    continue
                if tag_found:
                    break
                tag_ranges = self.positions_textbox.tag_ranges(tag)
                for i in range(0, len(tag_ranges), 2):
                    tag_start = self.positions_textbox.index(tag_ranges[i])
                    tag_end = self.positions_textbox.index(tag_ranges[i + 1])
                    if self.positions_textbox.compare(cursor, ">=", tag_start) and self.positions_textbox.compare(
                            cursor, "<",
                            tag_end):
                        # Cursor is inside an existing tag, remove the tag
                        self.positions_textbox.tag_remove(tag, tag_start, tag_end)
                        self.positions_textbox.tag_delete(tag)
                        self.positions_textbox.delete(tag_start, tag_end)
                        self.positions_textbox.insert(tag_start, tag)
                        if tag in self.payloads_textboxes:
                            if self.payloads_textboxes[tag] == self.current_payloads_textbox:
                                self.switch_payloads_textbox()
                            del self.payloads_textboxes[tag]
                        tag_found = True
                        break
            # Case 2: Cursor is outside any tag, remove all the tags.
            if not tag_found:
                confirm = ConfirmDialog(
                    self,
                    self.gui.gui_root,
                    "Are you sure you want to clear all the positions?",
                    "Watch out!",
                    "Yes",
                    lambda: (self.clear_all_positions(), confirm.destroy()),
                    "No",
                    lambda: confirm.destroy()
                )
        else:
            # Remove all tags that are overlapping or within the selection
            x, y = selection_indices
            for tag in self.positions_textbox.tag_names():
                if tag == "sel":
                    continue
                tag_ranges = self.positions_textbox.tag_ranges(tag)
                for i in range(0, len(tag_ranges), 2):
                    tag_start = self.positions_textbox.index(tag_ranges[i])
                    tag_end = self.positions_textbox.index(tag_ranges[i + 1])
                    if (self.positions_textbox.compare(x, "<=", tag_start) and self.positions_textbox.compare(y, ">=",
                                                                                                              tag_end)) or \
                            (self.positions_textbox.compare(x, ">=", tag_start) and self.positions_textbox.compare(x,
                                                                                                                   "<",
                                                                                                                   tag_end)) or \
                            (self.positions_textbox.compare(y, ">", tag_start) and self.positions_textbox.compare(y,
                                                                                                                  "<=",
                                                                                                                  tag_end)):
                        # Tag is overlapping or within the selection, remove the tag
                        self.positions_textbox.tag_remove(tag, tag_start, tag_end)
                        self.positions_textbox.tag_delete(tag)
                        self.positions_textbox.delete(tag_start, tag_end)
                        self.positions_textbox.insert(tag_start, tag)
                        if tag in self.payloads_textboxes:
                            if self.payloads_textboxes[tag] == self.current_payloads_textbox:
                                self.switch_payloads_textbox()
                            del self.payloads_textboxes[tag]
        self.update_payloads_textbox_dropdown()

    def clear_all_positions(self):
        for tag in self.positions_textbox.tag_names():

            if tag == "sel":
                continue

            tag_ranges = self.positions_textbox.tag_ranges(tag)

            for i in range(0, len(tag_ranges), 2):
                tag_start = self.positions_textbox.index(tag_ranges[i])
                tag_end = self.positions_textbox.index(tag_ranges[i + 1])

                self.positions_textbox.tag_remove(tag, tag_start, tag_end)
                self.positions_textbox.tag_delete(tag)
                self.positions_textbox.delete(tag_start, tag_end)
                self.positions_textbox.insert(tag_start, tag)

                if tag in self.payloads_textboxes:
                    self.payloads_textboxes[tag].pack_forget()
                    del self.payloads_textboxes[tag]

        self.switch_payloads_textbox()
        self.update_payloads_textbox_dropdown()

    def add_payload(self, name):
        self.payload_placeholder.pack_forget()
        self.payloads_textboxes[name] = TextBox(self.right_column)
        self.update_payloads_textbox_dropdown()

    def update_payloads_textbox_dropdown(self):
        if self.attack_type != 2:
            self.payloads_textbox_var.set("All positions")
            self.payloads_textbox_dropdown.configure(values=[], state=tk.DISABLED)

            for tag, textbox in self.payloads_textboxes.items():
                if tag != 0:
                    textbox.pack_forget()

        elif self.attack_type == 2:
            keys_to_select = [k for k in self.payloads_textboxes.keys() if k != 0]
            self.payloads_textbox_dropdown.configure(values=keys_to_select, state=tk.NORMAL)

            if keys_to_select:
                first_key = keys_to_select[0]
                self.payloads_textbox_var.set(first_key)
                self.switch_payloads_textbox(first_key)

            else:
                self.payloads_textbox_var.set("No positions added")
                self.switch_payloads_textbox()

    def switch_payloads_textbox(self, choice=None):
        for tag, textbox in self.payloads_textboxes.items():
            textbox.pack_forget()

        if self.attack_type != 2:
            self.current_payloads_textbox = self.payloads_textboxes[0]
            self.current_payloads_textbox.pack(fill=tk.BOTH, expand=True, padx=(0, 10), pady=(5, 10))

        elif choice is None:
            keys_to_select = [k for k in self.payloads_textboxes.keys() if k != 0]

            if keys_to_select:
                first_key = keys_to_select[0]
                self.switch_payloads_textbox(first_key)

            else:
                self.current_payloads_textbox = None
                self.payload_placeholder.pack(fill=tk.BOTH, padx=10, pady=0)

        elif choice in self.payloads_textboxes.keys():
            self.current_payloads_textbox = self.payloads_textboxes[choice]
            self.current_payloads_textbox.pack(fill=tk.BOTH, expand=True, padx=(0, 10), pady=(5, 10))

        else:
            self.current_payloads_textbox = None
            self.payload_placeholder.pack(fill=tk.BOTH, padx=10, pady=0)

    def load_payloads(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])

        if file_path and self.current_payloads_textbox is not None:
            try:
                with open(file_path, 'r') as file:
                    file_content = file.read()
                self.current_payloads_textbox.delete("1.0", tk.END)
                self.current_payloads_textbox.insert("1.0", file_content)
            except Exception as e:
                print(f"[ERROR] Error reading the file: {e}")
        else:
            print(f"[ERROR] Cannot add payloads from file: {file_path}")

    def clear_payloads(self):
        if self.current_payloads_textbox is not None:
            self.current_payloads_textbox.delete("1.0", tk.END)


class Intruder(ctk.CTkFrame):
    def __init__(self, master, root):
        super().__init__(master)
        self.configure(fg_color=color_bg_br, bg_color="transparent", corner_radius=10)
        self.gui_root = root

        # tabs, tab_nav_buttons and current_tab use visual_ids
        self.tabs = []
        self.tab_nav_buttons = []
        self.current_tab = 0
        # results_windows, attack_queues, producer_threads and consumer_threads use immutable unique_ids
        self.results_windows = {}
        self.attack_queues = {}
        self.producer_threads = {}
        self.consumer_threads = {}
        self.unique_id_counter = 1  # 0 is used for the first, unremovable tab

        self.tab_nav = ctk.CTkFrame(self, fg_color="transparent")
        self.tab_nav.pack(side="top", fill="x", padx=25, pady=(10, 0))
        first_tab_button = NavButton(
            self.tab_nav, text="1",
            command=lambda: self.show_tab(0),
            background=color_bg_br,
            background_selected=color_bg
        )
        self.tab_nav_buttons.append(first_tab_button)
        first_tab_button.pack(side="left")
        self.tab_add_button = NavButton(
            self.tab_nav,
            text="",
            icon=icon_add,
            command=self.add_tab,
            background=color_bg_br,
            background_selected=color_bg
        )
        self.tab_add_button.pack(side="right")
        self.tabs.append(IntruderTab(self, 0, 0))

        self.show_tab(self.current_tab)

    def add_tab(self, new_tab=None):
        visual_id = len(self.tabs)
        new_tab_nav_button = NavButton(self.tab_nav, text=str(visual_id + 1),
                                       command=lambda: self.show_tab(visual_id),
                                       background=color_bg_br,
                                       background_selected=color_bg
                                       )
        self.tab_nav_buttons.append(new_tab_nav_button)
        new_tab_nav_button.pack(side="left", padx=(10, 0))

        if new_tab is None:
            new_tab = IntruderTab(self, self.unique_id_counter, visual_id)
            self.unique_id_counter += 1
        self.tabs.append(new_tab)
        self.show_tab(visual_id)

    def show_tab(self, tab_id):
        self.current_tab = tab_id
        for i, tab in enumerate(self.tabs):
            if i == tab_id:
                self.tab_nav_buttons[i].select(True)
                tab.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 10))
            else:
                self.tab_nav_buttons[i].select(False)
                tab.pack_forget()

    def delete_tab(self, visual_id):
        unique_id = self.tabs[visual_id].unique_id

        if unique_id in self.producer_threads:
            self.producer_threads[unique_id].join(timeout=1)
            del self.producer_threads[unique_id]

        if unique_id in self.consumer_threads:
            # Consumer thread is daemon; it will stop with the program
            del self.consumer_threads[unique_id]

        if unique_id in self.attack_queues:
            del self.attack_queues[unique_id]

        if unique_id in self.results_windows:
            self.results_windows[unique_id].destroy()
            del self.results_windows[unique_id]

        if self.current_tab == visual_id:
            self.show_tab(visual_id - 1)
        self.tabs.pop(visual_id)

        self.tab_nav_buttons[visual_id].pack_forget()
        self.tab_nav_buttons.pop(visual_id)

        self.update_tab_numbering()

    def update_tab_numbering(self):
        for i, button in enumerate(self.tab_nav_buttons):
            button.main_button.configure(text=str(i + 1), command=lambda t=i: self.show_tab(t))
            self.tabs[i].update_number(i)

    def add_request_to_intruder_tab(self, content, host=None):
        for tab in self.tabs:
            if tab.is_empty:
                tab.hostname = host
                tab.hostname_entry.insert(0, host)
                tab.positions_textbox.insert_text(content)
                tab.is_empty = False
                return
        else:
            new_tab = IntruderTab(self, self.unique_id_counter, len(self.tab_nav_buttons), content, host)
            self.unique_id_counter += 1
            self.add_tab(new_tab)

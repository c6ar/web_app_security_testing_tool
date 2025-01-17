from backend.intruder import *
from frontend.common import *


class IntruderResult(ctk.CTkToplevel):
    """
    WASTT/Intruder/Results:
        Represents a GUI window for managing and displaying the results of an 'intruder attack'.

        This class serves as a specialized tkinter Toplevel window designed to handle the display and interaction
        with the ongoing 'intruder attack' process, including tabs for results, positions, and control functionality
        to pause or abort the attack. The class also facilitates displaying request and response content, positions,
        and the payloads being sent during the attack. Additional features include logging attack events and rendering
        detailed responses.
    """
    def __init__(self, master, gui, hostname, positions, payloads, timestamp, q, control_flags, **kwargs):
        super().__init__(master, **kwargs)
        self.queue = q
        self.title(f"Intruder Attack on {hostname}")
        self.intruder_tab = master
        self.wastt = gui
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.transient(self.wastt)
        self.configure(fg_color=color_bg, bg_color=color_bg)
        self.wastt.after(100, self.check_queue)
        self.after(250, self.iconbitmap, f"{ASSET_DIR}\\wastt.ico", "")
        width = int(int(self.wastt.winfo_width()) * 0.9)
        height = int(int(self.wastt.winfo_height()) * 0.9)
        center_window(self.wastt, self, width, height)
        self.focus_set()

        self.hostname = hostname
        self.timestamp = timestamp

        logs_location = RUNNING_CONFIG.get("logs_location", "")
        if not logs_location:
            app_dir = Path(__file__).resolve().parent.parent
            logs_location = app_dir / "logs"
        else:
            logs_location = Path(logs_location)
        logs_path = Path(logs_location / "intruder")

        logs_path.mkdir(parents=True, exist_ok=True)
        self.log_file = logs_path / f"intruder-{today}.log"

        with open(self.log_file, "a", encoding="utf-8", errors="replace") as file:
            file.write(f"\n[{self.timestamp}] Started attack on {self.hostname}.")

        self.control_flags = control_flags
        self.attack_paused = False
        self.attack_ceased = False

        # ================================================
        # Top bar
        # ================================================
        top_bar = Box(self)
        top_bar.pack(side=tk.TOP, fill=tk.X, padx=15, pady=(5, 0))

        attack_start_label = Label(top_bar, text=f"Attack on: {self.hostname} started at {self.timestamp}.")
        attack_start_label.pack(side=tk.LEFT, padx=(20, 0))

        self.pause_button = ActionButton(
            top_bar,
            text="Pause",
            image=icon_pause,
            command=self.pause_attack,
            fg_color=color_bg,
            hover_color=color_bg_br
        )
        self.pause_button.pack(side=tk.LEFT, padx=(10, 0))
        self.abort_button = ActionButton(
            top_bar,
            text="Abort",
            image=icon_abort,
            command=self.abort_attack,
            fg_color=color_bg,
            hover_color=color_bg_br
        )
        self.abort_button.pack(side=tk.LEFT, padx=(10, 0))
        self.attack_status_label = Label(top_bar, text=f"Attack is ongoing.")
        self.attack_status_label.pack(side=tk.LEFT, padx=(10, 0))

        tab_nav_bar = Box(self)
        tab_nav_bar.pack(side=tk.TOP, fill=tk.X, padx=15, pady=(5, 0))

        results_tab = BrightBox(self)
        positions_tab = BrightBox(self)

        self.tabs = {
            "Results": results_tab,
            "Positions": positions_tab
        }
        self.tab_nav_buttons = {}
        for name in self.tabs.keys():
            self.tab_nav_buttons[name] = NavButton(tab_nav_bar, text=name.upper(),
                                                   command=lambda t=name: self.show_tab(t))
            self.tab_nav_buttons[name].pack(side=tk.LEFT)

        self.add_random_button = NavButton(tab_nav_bar, text="Add random request", icon=icon_random,
                                           command=self.generate_random_request)
        if RUNNING_CONFIG["debug_mode"]:
            self.add_random_button.pack(side=tk.RIGHT)

        # ================================================
        # Results tab
        # ================================================
        self.results_paned_window = tk.PanedWindow(results_tab, orient=tk.VERTICAL, sashwidth=10,
                                                   background=color_bg_br)
        self.results_paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.top_frame = DarkBox(self.results_paned_window)
        self.results_paned_window.add(self.top_frame, height=350)

        request_columns = ("Request No.", "Position", "Payload", "Status code",
                           "Error", "Timeout", "Length",
                           "Request Content", "Response Content")
        self.attack_request_list = ItemList(self.top_frame, columns=request_columns,
                                            show="headings", style="Treeview")
        self.attack_request_list.bind("<<TreeviewSelect>>", self.show_request_content)
        self.attack_request_list.bind("<Button-1>", self.on_click_outside_item)
        for col in request_columns:
            if col in ("Request Content", "Response Content"):
                self.attack_request_list.heading(col, text=col)
                self.attack_request_list.column(col, width=0, stretch=tk.NO)
            else:
                self.attack_request_list.heading(col, text=col, command=lambda c=col: self.sort_by_column(c, False))
                self.attack_request_list.column(col, width=100)
        self.attack_request_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.bottom_frame = DarkBox(self.results_paned_window)

        self.bottom_frame.grid_columnconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(1, weight=1)
        self.bottom_frame.grid_rowconfigure(0, weight=1)

        request_frame = Box(self.bottom_frame)
        request_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=10, pady=10)

        request_header = HeaderTitle(request_frame, "Request")
        request_header.pack(fill=tk.X)

        self.request_textbox = TextBox(request_frame, "Select request to display its contents.")
        self.request_textbox.configure(state=tk.DISABLED)
        self.request_textbox.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        response_frame = Box(self.bottom_frame)
        response_frame.grid(row=0, column=1, sticky=tk.NSEW, padx=10, pady=10)

        response_header = Box(response_frame)
        response_header.pack(fill=tk.X)

        response_header_title = HeaderTitle(response_header, "Response")
        response_header_title.pack(side=tk.LEFT)

        self.response_textbox = TextBox(response_frame, "Select request to display its response contents.")
        self.response_textbox.configure(state=tk.DISABLED)
        self.response_textbox.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        response_render_button = ActionButton(
            response_header,
            text="Show response render",
            command=lambda: show_response_view(self.wastt, self.hostname, self.response_textbox.get_text())
        )
        response_render_button.pack(side=tk.RIGHT, padx=(0, 10))

        # ================================================
        # Positions tab
        # ================================================
        wrapper = DarkBox(positions_tab)
        wrapper.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        positions_header = HeaderTitle(wrapper, text="Positions")
        positions_header.grid(row=1, column=0, padx=10, pady=(5, 0), sticky=tk.W)

        self.positions_textbox = TextBox(wrapper, text="Enter request here.")
        self.positions_textbox.insert_text(positions.get_text())

        tags = positions.tag_names()
        for tag in tags:
            tag_ranges = positions.tag_ranges(tag)
            for start, end in zip(tag_ranges[0::2], tag_ranges[1::2]):
                self.positions_textbox.tag_add(tag, start, end)
                self.positions_textbox.tag_config(tag, background=color_highlight_bg, foreground=color_highlight)
        self.positions_textbox.configure(state=tk.DISABLED)
        self.positions_textbox.grid(row=2, column=0, padx=(20, 10), pady=(0, 20), sticky=tk.NSEW)

        payloads_header = HeaderTitle(wrapper, text="Sent payloads")
        payloads_header.grid(row=1, column=1, padx=10, pady=(5, 0), sticky=tk.W)

        if self.intruder_tab.attack_type == 2:
            self.payloads_frame = ctk.CTkScrollableFrame(wrapper, fg_color="transparent", bg_color="transparent")
            for var, payloads in payloads.items():
                payloads_label = Label(
                    self.payloads_frame,
                    text=f"Payloads for positions of \"{var}\"",
                    anchor=tk.W,
                    justify=tk.LEFT
                )
                payloads_label.pack(fill=tk.X, padx=10, pady=(10, 0))
                payloads_textbox = TextBox(self.payloads_frame, text=payloads.get_text(), height=150)
                payloads_textbox.pack(fill=tk.X, padx=10, pady=(10, 0))
        else:
            self.payloads_textbox = TextBox(wrapper, text=payloads.get(0).get_text())
            self.payloads_textbox.grid(row=2, column=1, padx=(10, 20), pady=(0, 20), sticky=tk.NSEW)

        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_columnconfigure(1, weight=1)
        wrapper.grid_rowconfigure(2, weight=1)

        self.show_tab("Results")

    def on_closing(self) -> None:
        """
        WASTT/Intruder/Results:
            Handles the window closing event by checking the status of the ongoing attack
            and displaying a confirmation dialog if an attack is pending.
        """
        if not self.attack_ceased:
            confirm = ConfirmDialog(
                self,
                self.wastt,
                "There is currently attack pending. Do you want to close the window?",
                "Warning",
                "Cancel",
                lambda: confirm.destroy(),
                "Keep attack in the background",
                lambda: (self.withdraw(), self.wastt.focus_set(), confirm.destroy(), self.wastt.deiconify()),
                "Abort the attack",
                lambda: (self.abort_attack(), self.withdraw(), confirm.destroy(), self.wastt.deiconify()),
                width=550,
                height=100
            )
        else:
            self.withdraw()

    def show_tab(self, tab_name: str) -> None:
        """
        WASTT/Intruder/Results:
            Displays the specified tab and hides all others.

            This method is responsible for showing the tab associated with the
            provided tab name while ensuring that all other tabs are hidden. It
            also updates the navigation buttons to reflect the active tab.

            Parameters:
            tab_name: str - Name of the tab to be shown.
        """
        for name, tab in self.tabs.items():
            if name == tab_name:
                tab.pack(side="top", fill="both", expand=True)
                self.tab_nav_buttons[name].select(True)
            else:
                tab.pack_forget()
                self.tab_nav_buttons[name].select(False)

    def show_request_content(self, _event) -> None:
        """
        WASTT/Intruder/Results:
            Displays the content of the selected attack request and its corresponding response in
            the user interface. If no item is selected, placeholder text is displayed in the content
            textboxes indicating that a selection is needed.

            Parameters:
            _event: object - Represents the triggering event passed in the callback mechanism of the UI framework.
        """
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

    def on_click_outside_item(self, _event) -> None:
        """
        WASTT/Intruder/Results:
            Handles the event when a click occurs outside of a list item in the attack request list.

            This method is triggered when a user clicks outside of the list items in the
            attack_request_list. If the click did not occur on a 'cell' region,
            any current selection in the list will be cleared.

            Parameters:
            _event: object - The event object containing details of the click, including its x and y
                coordinates.
        """
        region = self.attack_request_list.identify_region(_event.x, _event.y)
        if region != "cell":
            self.attack_request_list.selection_remove(self.attack_request_list.selection())

    def generate_random_request(self) -> None:
        """
        WASTT/Intruder/Results:
            Generates and populates a random HTTP request entry in a graphical user interface widget.
            The method creates synthetic data representative of HTTP communication, simulating both
            request and response contents. The generated data is then inserted into a list-based widget
            used for displaying attack request entries.
        """
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

    def add_attack_flow(self, data: dict) -> None:
        """
        WASTT/Intruder/Results:
            Logs and updates the state of an attack flow in a GUI application. The function handles adding
            details about attack requests, such as payloads, positions, status codes, errors, timeouts,
            request content, and response content to a UI component, while also writing this information
            to a log file. Additionally, it logs and reflects changes in the UI when the attack is
            completed, aborted, or encounters an error.

            Parameters:
            data: dict - A dictionary containing the attack flow values such as payload, position,
            status_code, error, timeout, req_con (request content), and res_con (response content).
            It also contains a 'status' key to indicate whether the attack is completed, aborted,
            or has errored.
        """
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

    def check_queue(self) -> None:
        """
        WASTT/Intruder/Results:
            This method continually monitors and processes data from a queue. It retrieves items
            and attempts to process them using the `add_attack_flow` method. Any exceptions during
            processing are handled with logging. The method schedules itself to recheck the queue
            at regular intervals, ensuring continuous operation.
        """
        while not self.queue.empty():
            try:
                data = self.queue.get()
                self.add_attack_flow(data)
            except Exception as e:
                dprint(f"Error INTR001: {e}")
        self.wastt.after(100, self.check_queue)

    def pause_attack(self) -> None:
        """
        WASTT/Intruder/Results:
            Pauses or resumes the ongoing attack based on the current state of the
            attack. Updates the control flags, button configuration, and attack
            status label accordingly.
        """
        if self.attack_paused:
            self.control_flags["pause"].clear()
            self.pause_button.configure(text="Pause", image=icon_pause)
            self.attack_status_label.configure(text="Attack is ongoing.")
        else:
            self.control_flags["pause"].set()
            self.pause_button.configure(text="Resume", image=icon_start)
            self.attack_status_label.configure(text="Attack is paused.")
        self.attack_paused = not self.attack_paused

    def abort_attack(self) -> None:
        """
        WASTT/Intruder/Results:
            Aborts an ongoing attack by setting the "abort" control flag. This method ensures
            the execution of any running attack is terminated promptly and allows for safe
            halting of processes.
        """
        self.control_flags["abort"].set()

    def sort_by_column(self, col: str, reverse: bool) -> None:
        """
        WASTT/Intruder:
            Sorts the list by column which header was clicked.

        Parametetrs:
            col: str - column header name
            reverse: bool - reverse order
        """
        index_list = [(self.attack_request_list.set(k, col), k) for k in self.attack_request_list.get_children('')]
        index_list.sort(reverse=reverse)

        for index, (val, k) in enumerate(index_list):
            self.attack_request_list.move(k, '', index)

        self.attack_request_list.heading(col, command=lambda: self.sort_by_column(col, not reverse))


class IntruderTab(ctk.CTkFrame):
    """
    WASTT/Intruder/Tab:
        Represents a user interface component for managing intruder attack operations.

        The IntruderTab class builds an interactive panel within a framework, facilitating
        the creation, configuration, and execution of attack types at a detailed level. It
        provides a modular and visually organized layout to define the target host, payloads,
        and positions, enabling streamlined workflows for the user. The interface includes
        validation mechanisms, event handling, and clear separation between the toolbar's
        actions, positions, and content management.
    """
    def __init__(self, master, unique_id, visual_id, content=None, hostname=None):
        super().__init__(master)
        self.configure(
            fg_color=color_bg,
            bg_color="transparent",
            corner_radius=10
        )
        self.intruder = master
        self.wastt = master.wastt
        self.unique_id = unique_id
        self.id = visual_id
        self.hostname = hostname
        self.is_empty = True if content is None else False

        # ================================================
        # Top bar:
        # attack type dropdown menu, attack commence and results button, attack info
        # intruder doc info, card closing and debug gen button
        # ================================================
        top_bar = Box(self)
        top_bar.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 0), sticky=tk.EW)

        attack_type_label = ctk.CTkLabel(top_bar, text="Attack type")
        attack_type_label.pack(padx=(20, 5), pady=10, side=tk.LEFT)

        self.attack_type_options = [
            "Sniper attack",
            "Battering ram attack",
            "Pitchfork attack"
        ]
        selected_option = tk.StringVar(value=self.attack_type_options[0])
        self.attack_type_dropdown = ctk.CTkOptionMenu(
            top_bar,
            width=200,
            corner_radius=10,
            variable=selected_option,
            values=self.attack_type_options,
            command=self._on_attack_option_select
        )
        self.attack_type_dropdown.pack(padx=(0, 10), pady=10, side=tk.LEFT)
        self.attack_type = 0

        self.attack_button = ActionButton(
            top_bar,
            text="Start attack",
            image=icon_attack,
            command=self._on_attack_button_click,
            state=tk.DISABLED
        )
        self.attack_button.pack(padx=10, pady=10, side=tk.LEFT)
        self.reload_dialog = None
        self.results_button = ActionButton(
            top_bar,
            text="Show attack results",
            image=icon_logs,
            command=self.show_attack,
            state=tk.DISABLED
        )
        self.results_button.pack(padx=10, pady=10, side=tk.LEFT)
        self.attack_info = Label(
            top_bar,
            text="No attack started.",
            anchor=tk.W
        )
        self.attack_info.pack(padx=10, pady=10, side=tk.LEFT)

        self.attack_timestamp = None
        self.control_flags = {
            "pause": Event(),
            "abort": Event()
        }

        info_button = InfoButton(
            top_bar,
            self,
            "http://localhost:8080/intruder.html"
        )
        info_button.pack(side=tk.RIGHT, padx=5, pady=0)

        if self.id != 0:
            self.delete_frame_button = ActionButton(
                top_bar,
                text="Delete the card",
                width=30,
                image=icon_delete,
                command=lambda: self.intruder.delete_tab(self.id),
                compound="left",
                corner_radius=32
            )
            self.delete_frame_button.pack(padx=10, pady=10, side=tk.RIGHT)

        gen_button = ActionButton(
            top_bar,
            text="Generate an attack",
            image=icon_random,
            command=self.generate_seed_intrusion
        )
        if RUNNING_CONFIG["debug_mode"]:
            gen_button.pack(padx=10, pady=10, side=tk.RIGHT)

        # ================================================
        # Left column:
        # Positions textbox
        # ================================================
        left_column = Box(self)
        left_column.grid(row=1, column=0, padx=(10, 5), pady=(0, 10), sticky=tk.NSEW)

        positions_header = Box(left_column)
        positions_header.pack(side=tk.TOP, fill=tk.X, padx=10, pady=0)

        positions_header_title = HeaderTitle(positions_header, "Positions")
        positions_header_title.pack(side=tk.LEFT, padx=(0, 10), pady=0)

        add_button = ActionButton(
            positions_header,
            text="Add position",
            image=icon_add,
            command=self.add_position
        )
        add_button.pack(side=tk.LEFT, padx=5, pady=0)

        clear_button = ActionButton(
            positions_header,
            text="Clear position(s)",
            image=icon_delete,
            command=self.clear_position,
            fg_color=color_acc3,
            hover_color=color_acc4
        )
        clear_button.pack(side=tk.LEFT, padx=5, pady=0)

        self.positions_textbox = TextBox(left_column, text="")
        self.positions_textbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        if content is not None:
            self.positions_textbox.insert_text(content)
        self.positions_textbox.bind("<<Modified>>", self._on_positions_textbox_change)

        self.positions_var_gen_id = 0

        # ================================================
        # Right column:
        # Target host text entry
        # Payloads textbox
        # ================================================
        self.right_column = Box(self)
        self.right_column.grid(row=1, column=1, padx=(5, 10), pady=(0, 10), sticky=tk.NSEW)

        target_bar = Box(self.right_column)
        target_bar.pack(side=tk.TOP, fill=tk.X, padx=(0, 10), pady=0)

        target_bar_title = HeaderTitle(target_bar, "Target")
        target_bar_title.pack(side=tk.LEFT, padx=(0, 10), pady=0)

        self.hostname_entry = TextEntry(target_bar, width=350)
        if self.hostname is not None:
            self.hostname_entry.insert(0, self.hostname)
        self.hostname_entry.pack(side=tk.LEFT, padx=(0, 10), pady=0)
        self.hostname_entry.bind("<KeyRelease>", self._on_positions_textbox_change)

        payloads_header = Box(self.right_column)
        payloads_header.pack(side=tk.TOP, fill=tk.X, padx=(0, 10), pady=0)

        payloads_header_title = HeaderTitle(payloads_header, "Payloads")
        payloads_header_title.pack(side=tk.LEFT, padx=(0, 10), pady=0)

        self.payloads_textbox_var = tk.StringVar(payloads_header)
        self.payloads_textbox_var.set("All")
        self.payloads_textbox_dropdown = ctk.CTkOptionMenu(
            payloads_header,
            width=200,
            corner_radius=10,
            variable=self.payloads_textbox_var,
            values=[],
            command=self.switch_payloads_textbox,
            state=tk.DISABLED,
        )
        self.payloads_textbox_dropdown.pack(side=tk.LEFT, padx=(0, 10), pady=0)

        payloads_load_button = ActionButton(
            payloads_header,
            text="Load from file",
            image=icon_load_file,
            command=self.load_payloads
        )
        payloads_load_button.pack(side=tk.LEFT, padx=(0, 10), pady=0)
        payloads_clear_button = ActionButton(
            payloads_header,
            text="Clear payloads",
            image=icon_delete,
            command=self.clear_payloads,
            fg_color=color_acc3,
            hover_color=color_acc4
        )
        payloads_clear_button.pack(side=tk.LEFT, padx=(0, 10), pady=0)

        self.payloads_textboxes: Dict[Union[int, str], TextBox] = {0: TextBox(self.right_column)}
        self.current_payloads_textbox = self.payloads_textboxes[0]
        self.current_payloads_textbox.pack(fill=tk.BOTH, expand=True, padx=(0, 10), pady=(5, 10))

        self.payload_placeholder = Label(
            self.right_column,
            text="Add payload position to get payload frame.",
            justify=tk.LEFT,
            anchor=tk.W
        )

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._on_attack_option_select(self.attack_type_options[0])

    def update_number(self, id_number: int) -> None:
        """
        WASTT/Intruder/Tab:
            Updates the ID number for the object and configures a button to delete a
            corresponding tab based on the updated ID. When the ID is not equal to
            zero, the delete button is linked to delete the tab associated with the
            updated ID.

            Parameters:
            id_number: int - The new ID number to set for the object. This value
                is used to update the object's ID and determine the behavior of the
                delete button.
        """
        self.id = id_number
        if self.id != 0:
            self.delete_frame_button.configure(
                command=lambda: self.intruder.delete_tab(self.id),
            )

    def _on_positions_textbox_change(self, _event) -> None:
        """
        WASTT/Intruder/Tab:
            Handles changes to the positions_textbox content and updates related state
            variables and UI components accordingly.

            This method is triggered when the text in the positions_textbox UI element
            is modified. It resets the modified flag, checks the content of the text box,
            and updates the UI's state based on whether the textbox and the hostname entry
            contain text. It enables or disables the attack_button depending on these
            conditions.

            Parameters:
            _event: object - The event object associated with the change, provided by the GUI framework.
        """
        self.positions_textbox.edit_modified(False)

        if len(self.positions_textbox.get_text()) > 0:
            self.is_empty = False
            if len(self.hostname_entry.get()) > 0:
                self.attack_button.configure(state=tk.NORMAL)
            else:
                self.attack_button.configure(state=tk.DISABLED)
        else:
            self.is_empty = True
            self.attack_button.configure(state=tk.DISABLED)

    def _on_attack_option_select(self, choice: str) -> None:
        """
        WASTT/Intruder/Tab:
            Handles the selection of an attack option and updates the related UI elements accordingly.

            This method is triggered when an attack type is selected by the user from a dropdown or
            similar UI component. It maps the selected choice to its corresponding index, updates
            the relevant textbox dropdown for payloads, and switches the payloads textbox based
            on the selected attack type.

            Parameters:
            choice: str - The option selected by the user representing the attack type.
        """
        self.attack_type = self.attack_type_options.index(choice)
        self.update_payloads_textbox_dropdown()
        self.switch_payloads_textbox()

    def _on_attack_button_click(self) -> None:
        """
        WASTT/Intruder/Tab:
            Handles the logic that is executed when the attack button is clicked.

            If an attack queue with the current unique ID exists, prompts the user with a
            confirmation dialog to either reload the attack with new parameters, which will
            overwrite previous results, or to show the results of the last attack. If no
            existing attack queue corresponds to the current ID, a new attack is started
            immediately.
        """
        queue_id = self.unique_id

        if queue_id in self.intruder.attack_queues:
            confirm = ConfirmDialog(
                master=self,
                root=self.intruder.wastt,
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

    def start_attack(self) -> None:
        """
        WASTT/Intruder/Tab:
            Starts an attack process by initializing all necessary components, such as payloads,
            positions, and threads for producing and consuming attack results. This function
            is responsible for managing the attack lifecycle from beginning to initial display
            of the results window.
        """
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
            ErrorDialog(self, self.wastt, "No payloads")
            return
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
                ErrorDialog(self, self.wastt, "No positions")
                return
            dprint(f"On positions:\n{positions}"
                   f"================================================\n")

        self.control_flags['pause'].clear()
        self.control_flags['abort'].clear()

        if uuid in self.intruder.attack_queues:
            del self.intruder.attack_queues[uuid]
            dprint(f"[DEBUG] Found attack queue with ID: {uuid}. Deleting it.")

        self.intruder.attack_queues[uuid] = queue.Queue()
        attack_queue = self.intruder.attack_queues[uuid]

        if uuid in self.intruder.results_windows:
            self.intruder.results_windows[uuid].destroy()
            del self.intruder.results_windows[uuid]
            dprint(f"[DEBUG] Found results window ID: {uuid}. Deleting it.")

        results_window = IntruderResult(
            master=self,
            gui=self.wastt,
            hostname=hostname,
            positions=self.positions_textbox,
            payloads=self.payloads_textboxes,
            timestamp=self.attack_timestamp,
            q=attack_queue,
            control_flags=self.control_flags
        )
        self.intruder.results_windows[uuid] = results_window

        def producer(q: queue.Queue, attack_type: int) -> None:
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

        if uuid in self.intruder.producer_threads:
            self.intruder.producer_threads[uuid].join(timeout=1)
            del self.intruder.producer_threads[uuid]
            dprint(f"[DEBUG] Found producer thread with ID: {uuid}. Deleting it.")

        producer_thread = Thread(target=producer, args=(
            attack_queue,
            self.attack_type
        ))
        producer_thread.start()
        self.intruder.producer_threads[uuid] = producer_thread

        def consumer() -> None:
            while True:
                try:
                    data = attack_queue.get(timeout=1)
                    results_window.add_attack_flow(data)
                except queue.Empty:
                    continue

        if uuid in self.intruder.consumer_threads:
            del self.intruder.consumer_threads[uuid]
            dprint(f"[DEBUG] Found consumer thread with ID: {uuid}. Deleting it.")

        consumer_thread = Thread(target=consumer, daemon=True)
        consumer_thread.start()
        self.intruder.consumer_threads[uuid] = consumer_thread

        self.attack_info.configure(text=f"Attack started at {self.attack_timestamp}.")
        self.results_button.configure(state=tk.NORMAL)

        results_window.deiconify()
        results_window.lift()
        results_window.focus_force()

    def show_attack(self) -> None:
        """
        WASTT/Intruder/Tab:
            Displays the attack details window or prompts an error dialog if the attack ID is not
            associated with an existing attack.
        """
        if self.unique_id in self.intruder.results_windows:
            results_window = self.intruder.results_windows[self.unique_id]
            results_window.deiconify()
            results_window.lift()
        else:
            ErrorDialog(self, self.wastt, "No attack with ID: {self.unique_id} found.")

    def generate_seed_intrusion(self) -> None:
        """
        WASTT/Intruder/Tab:
            Generates and sets up the initial HTTP intrusion payload and additional payload data or tags
            based on the selected attack type.

            The method begins by resetting any existing positions and clearing or reinitializing
            payload textboxes. It then preloads a seed HTTP request string into the positions textbox
            and updates the hostname entry field as a default placeholder (e.g., "https://www.example.com").
            Based on the current attack type, the method populates and highlights specific regions in
            the positions textbox with tag placeholders and associates them with either generic or
            attack-specific payloads.

            Sections within the positions textbox are highlighted with corresponding tags, which help
            identify these regions for specific payloads. If the `attack_type` is not 2, the system
            inserts generic payloads; otherwise, attack-specific payloads are set up with different
            highlighted tags and content.
        """
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

    def _get_cursor_position(self) -> str:
        """
        WASTT/Intruder/Tab:
            Returns the current cursor position within the text box.

            This method retrieves the position of the text insertion cursor
            inside the associated text box widget.
        """
        return self.positions_textbox.index(tk.INSERT)

    def _get_selection(self) -> (str, None):
        """
        WASTT/Intruder/Tab:
            Retrieves the current text selection from the positions_textbox widget.

            This method attempts to fetch the selected text from the positions_textbox
            widget. If no text is selected or if an error occurs during retrieval, it
            returns None.

            Returns:
            str - The currently selected text from the positions_textbox if successful,
            otherwise None.
        """
        try:
            return self.positions_textbox.selection_get()
        except tk.TclError:
            return None

    def _get_selection_indices(self) -> ((int, int), (None, None)):
        """
        WASTT/Intruder/Tab:
            Gets the start and end indices of the currently selected text in the positions_textbox widget.
            If there is no selection, it returns None for both start and end indices.

            Returns:
            tuple of (int, int) or (None, None) - A tuple containing the start and end indices of the selected text in the
                positions_textbox widget. Returns None, None if no selection is present.
        """
        try:
            start_index = self.positions_textbox.index(tk.SEL_FIRST)
            end_index = self.positions_textbox.index(tk.SEL_LAST)
            return start_index, end_index
        except tk.TclError:
            return None, None

    def _is_overlapping(self, start: str, end: str) -> bool:
        """
        WASTT/Intruder/Tab:
            Checks if a new tag range overlaps with any existing tag ranges.

            This function is used to verify whether the proposed tag range, defined
            by 'start' and 'end', overlaps with any existing tag ranges in the
            text widget the function operates on. The function checks three
            scenarios: if the new range's start lies within an existing range, if
            the new range's end lies within an existing range, or if the new range
            encompasses an existing range. If any of the conditions are met, the
            function returns True, indicating an overlap.

            Parameters:
            start: str - The starting position of the new tag range.
            end: str - The ending position of the new tag range.

            Returns:
            bool - True if the new tag range overlaps with any existing range,
                  otherwise False.
        """
        for tag in self.positions_textbox.tag_names():
            if tag == "sel":
                continue
            tag_ranges = self.positions_textbox.tag_ranges(tag)
            dprint(f"[DEBUG] Checking tag range: {tag_ranges}")
            for i in range(0, len(tag_ranges), 2):
                tag_start = self.positions_textbox.index(tag_ranges[i])
                tag_end = self.positions_textbox.index(tag_ranges[i + 1])
                if (self.positions_textbox.compare(start, ">=", tag_start) and self.positions_textbox.compare(start,
                                                                                                              "<",
                                                                                                              tag_end)):
                    # Case when a new tag's start is within the already existing tag
                    dprint(
                        f"[Debug] Intruder: You are trying to create a variable tag ({start, end}) with its beginning inside the already exisiting one ({tag_start, tag_end})!")
                    return True
                elif (self.positions_textbox.compare(end, ">", tag_start) and self.positions_textbox.compare(end, "<=",
                                                                                                             tag_end)):
                    # Case when a new tag's end is within the already existing tag
                    dprint(
                        f"[Debug] Intruder: You are trying to create a variable tag ({start, end}) with its ending inside the already exisiting one ({tag_start, tag_end})!")
                    return True
                elif (self.positions_textbox.compare(start, "<", tag_start) and self.positions_textbox.compare(end, ">",
                                                                                                               tag_end)):
                    # Case when the already existing tag is confined within a new tag's range
                    dprint(
                        f"[Debug] Intruder: You are trying to create a variable tag ({start, end}) that would contain the already exisiting one ({tag_start, tag_end})!")
                    return True
        return False

    def add_position(self) -> None:
        """
        WASTT/Intruder/Tab:
            Adds a new position or tag in the text box at the cursor location or for the selected text.

            If there is no selection, a unique variable name is generated, and a positional marker is added
            to the text box with the corresponding tag and style. In case of a selection, a variable name is
            derived from the selection text, formatted, and added as a marker with tagging and styling.
            Handles overlapping conditions, pre-existing variable names, and multi-line selections.
        """
        cursor = self._get_cursor_position()
        selection = self._get_selection()
        selection_indices = self._get_selection_indices()
        dprint(f"[DEBUG] Adding position on cursor pos: {cursor}, selection: {selection}, selection indices: {selection_indices}")

        if selection is None:
            var_name = f"var{self.positions_var_gen_id}"
            var_string = f"§{var_name}§"
            self.positions_var_gen_id += 1

            if not self._is_overlapping(cursor, cursor + "+1c"):
                self.positions_textbox.tag_config(var_name, background=color_highlight_bg, foreground=color_highlight)
                self.positions_textbox.insert(cursor, var_string)

                next_cursor = self._get_cursor_position()
                self.positions_textbox.tag_add(var_name, cursor, next_cursor)

                if self.attack_type == 2:
                    self.add_payload(var_name)
            else:
                ErrorDialog(self, self.wastt, "Cursor is overlapping with an existing tag.")
        else:
            var_name = re.sub(r'\s+', '_', selection)
            var_name = re.sub(r'[^a-zA-Z0-9_]', '', var_name)
            var_string = f"§{var_name}§"
            x, y = selection_indices

            if var_name in self.positions_textbox.tag_names():
                ErrorDialog(self, self.wastt,
                            f"Variable with the name {var_name} currently exists. Chose different name.")
                return

            if x.split('.')[0] == y.split('.')[0]:
                if not self._is_overlapping(x, y):
                    self.positions_textbox.delete(x, y)
                    self.positions_textbox.insert(x, var_string)
                    y = self._get_cursor_position()
                    self.positions_textbox.tag_config(var_name, background=color_highlight_bg, foreground=color_highlight)
                    self.positions_textbox.tag_add(var_name, x, y)
                    if self.attack_type == 2:
                        self.add_payload(var_name)
                else:
                    ErrorDialog(self, self.wastt, "Selection is overlapping with an existing tag.")
            else:
                ErrorDialog(self, self.wastt, "Selection cannot span over multiple lines!")

    def clear_position(self) -> None:
        """
        WASTT/Intruder/Tab:
            Clears the positions by removing text tags and updating payload textboxes. The behavior of
            this function depends on the current cursor position and selection state in the positions
            textbox. If no selection is made, it evaluates whether the cursor is within an existing tag,
            removing the tag in such cases, or prompts the user to confirm clearing all positions if no
            tag is found. If there is a selection, it clears tags overlapping or within the selection.
        """
        cursor = self._get_cursor_position()
        selection = self._get_selection()
        selection_indices = self._get_selection_indices()
        dprint(f"[DEBUG] Cursor pos: {cursor} Selection: {selection} Selection indices: {selection_indices}")

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
                    self.intruder.wastt,
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

    def clear_all_positions(self) -> None:
        """
        WASTT/Intruder/Tab:
            Removes all position-related tags and their associated data from the positions_textbox.

            This method iterates over all tags in the `positions_textbox`, excluding the "sel" tag,
            and removes their associated content, tag metadata, and corresponding UI elements in the
            `payloads_textboxes` dictionary. It refreshes the UI controls after completing the cleanup
            process.
        """
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

    def add_payload(self, name: str) -> None:
        """
        WASTT/Intruder/Tab:
            Adds a payload to the internal payloads dictionary and updates the associated UI components.

            Parameters:
            name: str - The name of the payload to add.
        """
        self.payload_placeholder.pack_forget()
        self.payloads_textboxes[name] = TextBox(self.right_column)
        self.update_payloads_textbox_dropdown()

    def update_payloads_textbox_dropdown(self) -> None:
        """
        WASTT/Intruder/Tab:
            Updates the payloads textbox dropdown based on the current attack type.

            The function modifies the state and values of the payloads dropdown and
            manages the visibility of payload textboxes depending on the `attack_type`.
            If `attack_type` is not equal to 2, the dropdown is disabled, and payload
            textboxes associated with nonzero positions are hidden. If `attack_type`
            equals 2, the dropdown is enabled with selectable keys corresponding to
            existing payload textboxes. The first available key is selected if possible;
            otherwise, no position is selected.
        """
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

    def switch_payloads_textbox(self, choice: str = None) -> None:
        """
        WASTT/Intruder/Tab:
            Switches the currently visible payloads textbox based on the given choice and the attack type.

            This method manages the visibility and arrangement of payloads textboxes within
            the user interface. It hides any currently visible payloads textboxes and displays
            the appropriate one based on the specified choice. If no choice is provided and the
            attack type is 2, the method attempts to make a selection based on available keys
            or displays a placeholder if no suitable textbox is found.

            Parameters:
            choice: str - optional - The key corresponding to the desired payloads textbox
                                    to display. Defaults to None.
        """
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

    def load_payloads(self) -> None:
        """
        WASTT/Intruder/Tab:
            Opens a file dialog to load text payloads from a file and populates a text widget with its content.

            This method allows users to select a file via a file dialog and loads the content
            of the selected text file into a TKinter text widget. If an error occurs during
            this process, an error message is printed to the console.
        """
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

    def clear_payloads(self) -> None:
        """
        WASTT/Intruder/Tab:
            Clears the contents of the currently active payloads textbox widget.

            This method is used to remove all text content from the textbox widget
            referenced by the `current_payloads_textbox` attribute. It performs this
            operation only when the attribute is not set to None, ensuring that the
            method is not executed on an uninitialized or missing widget reference.
        """
        try:
            if self.current_payloads_textbox is not None:
                self.current_payloads_textbox.delete("1.0", tk.END)
        except AttributeError as e:
            ErrorDialog(self, self.wastt, e)


class Intruder(ctk.CTkFrame):
    """
    WASTT/Intruder:
        A GUI frame containing navigable tabs for organizing
        content and functionality in an application. Designed to support dynamic addition of tabs
        with unique identifiers and associated navigation buttons.

        The class allows for the management of multiple tabs, including switching between them,
        adding new tabs, and organizing the associated resources like result windows, attack queues,
        and threads for each tab. It uses a visual navigation system where each tab has a corresponding
        button. The first tab is initialized at the start and cannot be removed.
    """
    def __init__(self, master, root):
        super().__init__(master)
        self.configure(fg_color=color_bg_br, bg_color="transparent", corner_radius=10)
        self.wastt = root

        # ================================================
        # Tabs and their respective nav buttons,
        # results_windows, attack_queues, producer_threads and consumer_threads
        # each tab has two IDs: visual_id and immutable unique_id
        # ================================================
        self.tabs = []
        self.tab_nav_buttons = []
        self.current_tab = 0
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
        tab_add_button = NavButton(
            self.tab_nav,
            text="",
            icon=icon_add,
            command=self.add_tab,
            background=color_bg_br,
            background_selected=color_bg
        )
        tab_add_button.pack(side="right")

        # ================================================
        # Initialising the first tab
        # ================================================
        self.tabs.append(
            IntruderTab(self, 0, 0)
        )
        self.show_tab(self.current_tab)

    def add_tab(self, new_tab: IntruderTab = None) -> None:
        """
        WASTT/Intruder:
            Adds a new tab to the application's interface. The tab includes a
            navigation button and, if not supplied, a newly instantiated tab
            object. The method assigns a visual ID to the tab, appends it to
            the tab collection, and sets it as the currently visible tab.

            Parameters:
            new_tab: IntruderTab - optional - A pre-defined tab object to be
            added. If None, a new tab will be created and appended to
            the collection.
        """
        if len(self.tab_nav_buttons) < 10:
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
        else:
            ErrorDialog(self, self.wastt, "Maximum number of tabs reached.")

    def show_tab(self, tab_id: int) -> None:
        """
        WASTT/Intruder:
            Show the specified tab in a tabbed interface by its ID, hiding all other tabs.

            This method updates the current visible tab based on the given tab ID,
            ensuring only the selected tab is displayed while others are hidden.
            Additionally, it visually updates the state of navigation buttons to reflect
            the selected tab.

            Parameters:
            tab_id: int - The index of the tab to display. Must correspond to an
            existing tab in the interface.
        """
        self.current_tab = tab_id
        for i, tab in enumerate(self.tabs):
            if i == tab_id:
                self.tab_nav_buttons[i].select(True)
                tab.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 10))
            else:
                self.tab_nav_buttons[i].select(False)
                tab.pack_forget()

    def delete_tab(self, visual_id: int) -> None:
        """
        WASTT/Intruder:
            Deletes a tab and cleans up all associated resources. This method is responsible
            for managing the threads, queues, and GUI elements connected to the specified tab.
            It ensures proper disposal of resources and updates the graphical interface
            accordingly.

            Parameters:
            visual_id: int - The visual index of the tab to be deleted.
        """
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

    def update_tab_numbering(self) -> None:
        """
        WASTT/Intruder:
            Updates the numbering and associated command for each tab navigation button. Ensures that the
            buttons are labeled correctly and the corresponding tab is displayed when clicked. Synchronizes
            the numbering within the tabs with the button numbers.
        """
        for i, button in enumerate(self.tab_nav_buttons):
            button.main_button.configure(text=str(i + 1), command=lambda t=i: self.show_tab(t))
            self.tabs[i].update_number(i)

    def add_request_to_intruder_tab(self, content: str, host: str = None) -> None:
        """
        WASTT/Intruder:
            Adds a request to an available tab in the intruder interface or creates a new
            tab if all existing tabs are occupied.

            This method attempts to find an empty tab among the existing tabs in the
            intruder interface. If an empty tab is found, it will be populated with the
            provided request content and host information. If all tabs are occupied,
            a new tab will be created to accommodate the new request. The method also
            ensures that any newly created tabs update the internal counters and
            navigation appropriately.

            Parameters:
            content: str - The request content to be inserted into the tab.
            host: str - optional - The hostname associated with the request. If not supplied, it
                defaults to None.
        """
        for tab in self.tabs:
            if tab.is_empty:
                tab.hostname = host
                tab.hostname_entry.insert(0, host)
                tab.positions_textbox.insert_text(content)
                tab.is_empty = False
                dprint(f"[DEBUG] Adding request to an empty tab (visual ID: {tab.id}).")
                return
        else:
            new_tab = IntruderTab(self, self.unique_id_counter, len(self.tab_nav_buttons), content, host)
            self.unique_id_counter += 1
            self.add_tab(new_tab)
            dprint(f"[DEBUG] Adding request to the new tab (visual ID: {new_tab.id}).")

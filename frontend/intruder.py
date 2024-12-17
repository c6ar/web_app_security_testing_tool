import pickle
import socket
import asyncio
import threading
from common import *
from backend.intruder import *
def load_payload(payloads_text):
    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])

    if file_path:
        try:
            with open(file_path, 'r') as file:
                file_content = file.read()
            payloads_text.delete("1.0", tk.END)
            payloads_text.insert("1.0", file_content)
        except Exception as e:
            print(f"Error reading the file: {e}")


def clear_payload(payloads_text):
    payloads_text.delete("1.0", tk.END)


class IntruderResult(ctk.CTkToplevel):
    def __init__(self, master, gui, hostname, positions, payloads, timestamp, **kwargs):
        super().__init__(master, **kwargs)
        self.loop = asyncio.new_event_loop()  # Tworzymy pętlę asyncio dla tego obiektu
        self.start_async_servers()

        self.title("Intruder Attack's Results")
        self.intruder_tab = master
        self.root = gui.gui_root
        self.configure(fg_color=color_bg, bg_color=color_bg)
        width = int(int(self.root.winfo_width()) * 0.9)
        height = int(int(self.root.winfo_height()) * 0.9)
        self.geometry(f"{width}x{height}")
        self.attributes("-topmost", True)
        center_window(self.root, self, width, height)

        self.tab_nav = ctk.CTkFrame(self, fg_color=color_bg, bg_color=color_bg)
        self.tab_nav.pack(side="top", fill="x", padx=15, pady=(5, 0))

        self.results_tab = ctk.CTkFrame(self, fg_color=color_bg_br, bg_color="transparent", corner_radius=10)
        self.positions_tab = ctk.CTkFrame(self, fg_color=color_bg_br, bg_color="transparent", corner_radius=10)

        self.hostname = hostname
        self.timestamp = timestamp
        self.host_label = ctk.CTkLabel(self.tab_nav, text=f"Attack on: {self.hostname} started on {self.timestamp}")
        self.host_label.pack(side=tk.LEFT, padx=(10, 15))
        self.tabs = {
            "Results": self.results_tab,
            "Positions": self.positions_tab
        }
        self.tab_nav_buttons = {}
        for name in self.tabs.keys():
            self.tab_nav_buttons[name] = NavButton(self.tab_nav, text=name.upper(), command=lambda t=name: self.show_tab(t))
            self.tab_nav_buttons[name].pack(side=tk.LEFT)

        # TODO FRONTEND P2: Add a button that aborts the attack.
        self.add_random_button = NavButton(self.tab_nav, text="Add random request", icon=icon_random, command=self.generate_random_request)
        self.add_random_button.pack(side=tk.RIGHT)

        """
         > RESULTS TAB
        """
        self.results_paned_window = tk.PanedWindow(self.results_tab, orient=tk.VERTICAL, sashwidth=10,
                                                   background=color_bg_br)
        self.results_paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.top_frame = ctk.CTkFrame(self.results_paned_window, corner_radius=10, fg_color=color_bg, bg_color="transparent")
        self.results_paned_window.add(self.top_frame, height=350)

        request_columns = ("Request No.", "Position", "Payload", "Status code", "Response received", "Error", "Timeout", "Length", "Request Content", "Response Content")
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

        self.bottom_frame = ctk.CTkFrame(self.results_paned_window, corner_radius=10, fg_color=color_bg, bg_color="transparent")
        # self.results_paned_window.add(self.bottom_frame)

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

        self.response_header = HeaderTitle(self.response_frame, "Response")
        self.response_header.pack(fill=tk.X)

        self.response_textbox = TextBox(self.response_frame, "Select request to display its response contents.")
        self.response_textbox.configure(state=tk.DISABLED)
        self.response_textbox.pack(pady=10, padx=10, fill="both", expand=True)

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
                self.positions_textbox.tag_config(tag, background="#8b115f", foreground="#b9d918")
        self.positions_textbox.configure(state=tk.DISABLED)
        self.positions_textbox.grid(row=2, column=0, padx=(20, 10), pady=(0, 20), sticky="nsew")

        self.payloads_header = HeaderTitle(self.wrapper, text="Sent payloads")
        self.payloads_header.grid(row=1, column=1, padx=10, pady=(5, 0), sticky="w")

        self.payloads_frame = ctk.CTkScrollableFrame(self.wrapper, fg_color="transparent", bg_color="transparent")
        self.payloads_frame.grid(row=2, column=1, padx=(10, 20), pady=(0, 20), sticky="nsew")

        if self.intruder_tab.attack_type == 2:
            for var, payloads in payloads.items():
                payloads_label = ctk.CTkLabel(self.payloads_frame, text=f"Payloads for positions of \"{var}\"", anchor=tk.W, justify=tk.LEFT)
                payloads_label.pack(fill=tk.X, padx=10, pady=(10, 0))
                payloads_textbox = TextBox(self.payloads_frame, text=payloads.get_text(), height=150)
                payloads_textbox.pack(fill=tk.X, padx=10, pady=(10, 0))
        else:
            payloads_textbox = TextBox(self.payloads_frame, text=payloads.get(0).get_text())
            payloads_textbox.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        self.wrapper.grid_columnconfigure(0, weight=1)
        self.wrapper.grid_columnconfigure(1, weight=1)
        self.wrapper.grid_rowconfigure(2, weight=1)

        self.show_tab("Results")

        self.flow = None
        """
        Asyncs servers to catch respones
        """

        # TODO FRONTEND P2: Give out confirm dialog with 3 options: to stop the attack and close the window,
        #  to stop the attack and save it in the chronology or to keep attack running in the background.
        self.protocol("WM_DELETE_WINDOW", self.hide_window)

    def hide_window(self):
        self.withdraw()

    def show_tab(self, tab_name):
        for name, tab in self.tabs.items():
            if name == tab_name:
                tab.pack(side="top", fill="both", expand=True)
                self.tab_nav_buttons[name].set_selected(True)
            else:
                tab.pack_forget()
                self.tab_nav_buttons[name].set_selected(False)

    def show_request_content(self, event):
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
        status_code = f"{random.choice(['400','401','402','403','404'])}"
        resp_rec = random.randint(1, 100)
        error = False
        timeout = False
        req_con = f"HTTP/1.1\nHost: {self.hostname}\nValue = {payload}\nProxy-Connection: keep-alive\n{random.choice(['random stuff here', 'Header Lorem Ipsum', 'ETC...'])}\n"
        res_con = f"{status_code} {resp_rec} \n{random.choice(['Response Lorem Ipsum.', 'Some HTTP gibberish here.'])}\nEnd of Response."
        length = len(res_con)
        random_request = [rn, pos, payload, status_code, resp_rec, error, timeout, length, req_con, res_con]

        self.attack_request_list.insert("", tk.END, values=random_request)
        if len(self.attack_request_list.selection()) == 0:
            self.attack_request_list.selection_add(self.attack_request_list.get_children()[0])

    def add_attack_flow(self, data):
        rn = len(self.attack_request_list.get_children()) + 1
        pos = data['position']
        payload = data['payload']
        status_code = data['status_code']
        resp_rec = data['resp_rec']
        error = data['error']
        timeout = data['timeout']
        req_con = data['req_con']
        res_con = data['res_con']
        length = len(res_con)
        request = [rn, pos, payload, status_code, resp_rec, error, timeout, length, req_con, res_con]

        self.attack_request_list.insert("", tk.END, values=request)
        if len(self.attack_request_list.selection()) == 0:
            self.attack_request_list.selection_add(self.attack_request_list.get_children()[0])

    def start_async_servers(self):
        """
        Starts the asyncio servers in a separate thread to handle scope updates and flow killing asynchronously.
        """

        def run_servers():
            asyncio.set_event_loop(self.loop)
            tasks = [
                self.listen_for_responses(),

            ]
            self.loop.run_until_complete(asyncio.gather(*tasks))

        thread = threading.Thread(target=run_servers, daemon=True)
        thread.start()

    async def listen_for_responses(self):
        server = await asyncio.start_server(
            self.handle_responses, HOST, BACK_FRONT_INTRUDERRESPONSES
        )
        async with server:
            await server.serve_forever()

    async def handle_responses(self, reader, writer):
        data = await reader.read(4096)
        if data:
            self.flow = pickle.loads(data)
            self.add_attack_flow(self.flow)
        writer.close()
        await writer.wait_closed()


class IntruderTab(ctk.CTkFrame):
    def __init__(self, master, id_number, content=None, host=None):
        super().__init__(master)
        self.hosturl = host
        self.configure(
            fg_color=color_bg,
            corner_radius=10,
            background_corner_colors=(color_bg_br, color_bg_br, color_bg_br, color_bg_br)
        )
        self.gui = master
        self.id = id_number
        self.is_empty = True

        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        self.hostname_label = ctk.CTkLabel(self.top_bar, text="Host URL:")
        self.hostname_label.pack(padx=(10, 5), pady=10, side="left")

        self.hostname_entry = TextEntry(self.top_bar, width=350)
        if self.hosturl is not None:
            self.hostname_entry.insert(0, self.hosturl)
        self.hostname_entry.pack(padx=(0, 10), pady=10, side="left")
        self.hostname_entry.bind("<KeyRelease>", self.on_positions_textbox_change)

        self.attack_type_label = ctk.CTkLabel(self.top_bar, text="Attack type:")
        self.attack_type_label.pack(padx=(10, 5), pady=10, side="left")

        self.attack_type_options = ["Sniper attack", "Battering ram attack", "Pitchfork attack"]
        selected_option = tk.StringVar(value=self.attack_type_options[0])
        self.attack_type_dropdown = ctk.CTkOptionMenu(self.top_bar, width=200, corner_radius=10, variable=selected_option,
                                                      values=self.attack_type_options, command=self.on_attack_option_select)
        self.attack_type_dropdown.pack(padx=(0, 10), pady=10, side="left")
        self.attack_type = 0

        self.start_attack_button = ActionButton(
            self.top_bar,
            text="Start attack",
            image=icon_attack,
            command=self.start_attack,
            state=tk.DISABLED
        )
        self.start_attack_button.pack(padx=10, pady=10, side="left")

        # TODO FRONTEND P2: Add a dropdown with saved and ongoing attacks.
        self.show_last_ongoing_button = ActionButton(
            self.top_bar,
            text="Show last ongoing attack",
            image=icon_attack,
            command=self.show_last_ongoing
        )
        self.show_last_ongoing_button.pack(padx=10, pady=10, side="left")

        if self.id != 0:
            self.delete_frame_button = ctk.CTkButton(
                self.top_bar,
                text="Delete the card",
                width=30,
                image=icon_delete,
                command=lambda: self.gui.delete_tab(self.id),
                compound="left",
                corner_radius=32
            )
            self.delete_frame_button.pack(padx=10, pady=10, side="right")
        self.positions_header = HeaderTitle(self, "Positions")
        self.positions_header.pack(fill=tk.X, padx=10, pady=0)

        self.positions_wrapper = ctk.CTkFrame(self, fg_color="transparent", corner_radius=10)
        self.positions_wrapper.pack(fill=tk.X, padx=10, pady=0)

        self.monoscape_font = ctk.CTkFont(family="Courier New", size=14, weight="normal")
        self.positions_textbox = TextBox(self.positions_wrapper, text="Insert your header with variables.", height=224)
        self.positions_textbox.pack(side="left", fill=tk.X, expand=True, padx=10, pady=10)
        if content is not None:
            self.positions_textbox.insert_text(content)
            self.is_empty = False
        self.positions_textbox.bind("<<Modified>>", self.on_positions_textbox_change)

        self.positions_var_gen_id = 0

        self.positions_buttons = ctk.CTkFrame(self.positions_wrapper, fg_color="transparent")
        self.positions_buttons.pack(side="left", fill=tk.Y)

        self.add_button = ctk.CTkButton(self.positions_buttons, text="Add §", command=self.add_position)
        self.add_button.pack(side="top", padx=5, pady=10)

        self.clear_button = ctk.CTkButton(self.positions_buttons, text="Clear §", command=self.clear_position)
        self.clear_button.pack(side="top", padx=5, pady=10)

        self.payloads_header = HeaderTitle(self, "Payloads")
        self.payloads_header.pack(fill=tk.X, padx=10, pady=0)

        self.payloads_wrapper = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=10)
        self.payloads_wrapper.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        self.payloads_frames = {}
        self.payloads_textboxes = {}

        self.payload_placeholder = ctk.CTkLabel(self.payloads_wrapper,
                                                text="Add payload position to get payload frame.",
                                                justify="left",
                                                anchor="w")

        self.on_attack_option_select("Sniper attack")

        self.attack_result = {}
        self.last_timestamp = None

    def update_number(self, id_number):
        self.id = id_number
        if self.id != 0:
            self.delete_frame_button.configure(
                command=lambda: self.gui.delete_tab(self.id),
            )

    def on_positions_textbox_change(self, event):
        self._reset_positions_modified_flag()
        if len(self.positions_textbox.get_text()) > 0 and self.positions_textbox.get_text() != "Insert your header with variables.":
            self.is_empty = False
            self.positions_textbox.configure(font=self.positions_textbox.monoscape_font)
            if len(self.hostname_entry.get()) > 0:
                self.start_attack_button.configure(state=tk.NORMAL)
            else:
                self.start_attack_button.configure(state=tk.DISABLED)
        else:
            self.is_empty = True
            self.positions_textbox.configure(font=self.positions_textbox.monoscape_font_italic)
            self.start_attack_button.configure(state=tk.DISABLED)

    def on_attack_option_select(self, choice):
        self.attack_type = self.attack_type_options.index(choice)

        if self.attack_type == 0 or self.attack_type == 1:
            if len(self.payloads_frames) == 0 or self.payloads_frames.get(0) is None:
                self.add_payload()
            else:
                for name, frame in self.payloads_frames.items():
                    if name == 0:
                        frame.pack(side="top", fill=tk.BOTH, expand=True, padx=10, pady=5)
                    else:
                        frame.pack_forget()
        elif self.attack_type == 2:
            if self.payloads_frames.get(0) is not None and self.payloads_frames[0].winfo_ismapped():
                self.payloads_frames[0].pack_forget()

            for name in self.positions_textbox.tag_names():
                if name == "sel":
                    continue
                if self.payloads_frames.get(name) is not None:
                    if not self.payloads_frames[name].winfo_ismapped():
                        self.payloads_frames[name].pack(side="top", fill=tk.X, padx=10, pady=5)
                else:
                    self.add_payload(name)

            if len(self.payloads_frames) == 0 or (
                    len(self.payloads_frames) == 1 and self.payloads_frames.get(0) is not None):
                self.payload_placeholder.pack(fill=tk.X, padx=10, pady=10)

    def _reset_positions_modified_flag(self):
        self.positions_textbox.edit_modified(False)

    def start_attack(self):
        if len(self.payloads_textboxes) >= 1:
            payloads = {}
            if self.attack_type == 0 or self.attack_type == 1:
                payloads = self.payloads_textboxes[0].get_text()
            else:
                for var, textbox in self.payloads_textboxes.items():
                    payloads[var] = textbox.get_text()

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            tags =  self.positions_textbox.tag_names()
            positions = {}
            for tag in tags:
                ranges = self.positions_textbox.tag_ranges(tag)
                for start, end in zip(ranges[0::2], ranges[1::2]):
                    positions[str(start)] = str(end)
            self.last_timestamp = timestamp
            self.show_results(timestamp)
            if self.attack_type == 0:
                 sniper_attack(payloads, self.positions_textbox.get_text(),positions)
            elif self.attack_type == 1:
                 ram_attack(payloads, self.positions_textbox.get_text())
            else:
                #TODO 3rd option of attack
                pass



    def show_last_ongoing(self):
        if len(self.attack_result) > 0:
            self.attack_result[self.last_timestamp].deiconify()
            self.attack_result[self.last_timestamp].lift()

    def show_results(self, timestamp):
        self.attack_result[timestamp] = IntruderResult(self, self.gui, self.hosturl, self.positions_textbox, self.payloads_textboxes, timestamp)

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
            # print(f"Debug: Checking tag range: {tag_ranges}")
            for i in range(0, len(tag_ranges), 2):
                tag_start = self.positions_textbox.index(tag_ranges[i])
                tag_end = self.positions_textbox.index(tag_ranges[i + 1])
                if (self.positions_textbox.compare(start, ">=", tag_start) and self.positions_textbox.compare(start, "<",
                                                                                                              tag_end)):
                    # Case when a new tag's start is within the already existing tag
                    # print(f"Debug Intruder/Variable: You are trying to create a variable tag ({start, end}) with its beginning inside the already exisiting one ({tag_start, tag_end})!")
                    return True
                elif (self.positions_textbox.compare(end, ">", tag_start) and self.positions_textbox.compare(end, "<=",
                                                                                                             tag_end)):
                    # Case when a new tag's end is within the already existing tag
                    # print(f"Debug Intruder/Variable: You are trying to create a variable tag ({start, end}) with its ending inside the already exisiting one ({tag_start, tag_end})!")
                    return True
                elif (self.positions_textbox.compare(start, "<", tag_start) and self.positions_textbox.compare(end, ">",
                                                                                                               tag_end)):
                    # Case when the already existing tag is confined within a new tag's range
                    # print(f"Debug Intruder/Variable: You are trying to create a variable tag ({start, end}) that would contain the already exisiting one ({tag_start, tag_end})!")
                    return True
        return False

    def add_position(self):
        cursor = self.get_cursor_position()
        selection = self.get_selection()
        selection_indices = self.get_selection_indices()
        # print(f"Debug:\n cursor pos: {cursor}\n selection: {selection}\n selection indices: {selection_indices}")

        if selection is None:
            var_name = f"var{self.positions_var_gen_id}"
            var_string = f"§{var_name}§"
            self.positions_var_gen_id += 1

            if not self.is_overlapping(cursor, cursor + "+1c"):
                # TODO FRONTEND P3: Add tag coloring respective for the theme dark vs light.
                self.positions_textbox.tag_config(var_name, background="#8b115f", foreground="#b9d918")
                self.positions_textbox.insert(cursor, var_string)

                next_cursor = self.get_cursor_position()
                self.positions_textbox.tag_add(var_name, cursor, next_cursor)

                if self.attack_type == 2:
                    self.add_payload(var_name)
            else:
                print("Error Intruder/Variable: Cursor is overlapping with an existing tag.")
        else:
            var_name = re.sub(r'\s+', '_', selection)
            var_name = re.sub(r'[^a-zA-Z0-9_]', '', var_name)
            var_string = f"§{var_name}§"
            x, y = selection_indices

            new_var = True
            for tag in self.positions_textbox.tag_names():
                if tag == var_name:
                    new_var = False

            if x.split('.')[0] == y.split('.')[0]:
                if not self.is_overlapping(x, y):
                    self.positions_textbox.delete(x, y)
                    self.positions_textbox.insert(x, var_string)
                    y = self.get_cursor_position()
                    self.positions_textbox.tag_config(var_name, background="#8b115f", foreground="#b9d918")
                    self.positions_textbox.tag_add(var_name, x, y)
                    if new_var and self.attack_type == 2:
                        self.add_payload(var_name)
                else:
                    print("Error Intruder/Variable: Selection is overlapping with an existing tag.")
            else:
                print("Error Intruder/Variable: Selection cannot span over multiple lines!")

    def clear_position(self):
        cursor = self.get_cursor_position()
        selection = self.get_selection()
        selection_indices = self.get_selection_indices()
        # print(f"Debug:\n cursor pos: {cursor}\n selection: {selection}\n selection indices: {selection_indices}")

        if selection is None:
            # Case 1: Cursor is withing the existing tag.
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
                    if self.positions_textbox.compare(cursor, ">=", tag_start) and self.positions_textbox.compare(cursor, "<",
                                                                                                                  tag_end):
                        # Cursor is inside an existing tag, remove the tag
                        self.positions_textbox.tag_remove(tag, tag_start, tag_end)
                        self.positions_textbox.tag_delete(tag)
                        self.positions_textbox.delete(tag_start, tag_end)
                        self.positions_textbox.insert(tag_start, tag)
                        self.payloads_frames[tag].pack_forget()
                        del self.payloads_frames[tag]
                        tag_found = True
                        break
            # Case 2: Cursor is outside of any tag, remove all the tags.
            if not tag_found:
                self.clear_all_positions_confirm()
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
                            (self.positions_textbox.compare(x, ">=", tag_start) and self.positions_textbox.compare(x, "<",
                                                                                                                   tag_end)) or \
                            (self.positions_textbox.compare(y, ">", tag_start) and self.positions_textbox.compare(y, "<=",
                                                                                                                  tag_end)):
                        # Tag is overlapping or within the selection, remove the tag
                        self.positions_textbox.tag_remove(tag, tag_start, tag_end)
                        self.positions_textbox.tag_delete(tag)
                        self.positions_textbox.delete(tag_start, tag_end)
                        self.positions_textbox.insert(tag_start, tag)
                        self.payloads_frames[tag].pack_forget()
                        del self.payloads_frames[tag]
        if len(self.payloads_frames) == 0 or (len(self.payloads_frames) == 1 and self.payloads_frames.get(0) is not None):
            self.payload_placeholder.pack(fill=tk.X, padx=10, pady=10)

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
                self.payloads_frames[tag].pack_forget()
                del self.payloads_frames[tag]
        self.payload_placeholder.pack(fill=tk.X, padx=10, pady=10)

    def clear_all_positions_confirm(self):
        confirmation = ConfirmDialog(self, self.gui.gui_root,
                                     "Are you sure you want to clear all the positions?",
                                     "Yes", lambda: (self.clear_all_positions(), confirmation.destroy()),
                                     "No", lambda: confirmation.destroy())

    def add_payload(self, new_var=None):
        self.payload_placeholder.pack_forget()

        payloads_frame = ctk.CTkFrame(self.payloads_wrapper, fg_color="transparent", bg_color="transparent")
        if new_var is not None:
            payloads_frame.pack(fill=tk.X, padx=10, pady=0)

            payloads_subtitle = HeaderTitle(payloads_frame, text=f"Payloads for positions of \"{new_var}\"", size=18, height=18, pady=0)
            payloads_subtitle.pack(side="top", anchor="w", padx=0, pady=5)

            payloads_text = TextBox(payloads_frame, height=112)
        else:
            payloads_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=0)

            payloads_text = TextBox(payloads_frame)

        payloads_text.pack(side="left", fill=tk.X, expand=True, padx=(0, 10), pady=10)

        payloads_buttons = ctk.CTkFrame(payloads_frame, fg_color="transparent", bg_color="transparent")
        payloads_buttons.pack(side="right", fill=tk.Y, padx=(10, 0), pady=10)

        load_button = ctk.CTkButton(payloads_buttons, text="Load", command=lambda: load_payload(payloads_text))
        load_button.pack(side="top", padx=0, pady=(0, 5))

        clear_button = ctk.CTkButton(payloads_buttons, text="Clear", command=lambda: clear_payload(payloads_text),
                                     fg_color=color_acc3, hover_color=color_acc4)
        clear_button.pack(side="top", padx=0, pady=5)

        if new_var is not None:
            self.payloads_frames[new_var] = payloads_frame
            self.payloads_textboxes[new_var] = payloads_text
        else:
            self.payloads_frames[0] = payloads_frame
            self.payloads_textboxes[0] = payloads_text


class GUIIntruder(ctk.CTkFrame):
    def __init__(self, master, root):
        super().__init__(master)
        self.configure(fg_color=color_bg_br, bg_color="transparent", corner_radius=10)
        self.gui_root = root

        self.tabs = []
        self.tab_nav = ctk.CTkFrame(self, fg_color="transparent")
        self.tab_nav.pack(side="top", fill="x", padx=15, pady=(10, 0))
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
        self.tabs.append(IntruderTab(self, 0))
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
            new_tab = IntruderTab(self, new_tab_id)
        self.tabs.append(new_tab)
        self.show_tab(new_tab_id)

    def show_tab(self, tab_id):
        self.current_tab = tab_id
        for i, tab in enumerate(self.tabs):
            if i == tab_id:
                self.tab_nav_buttons[i].set_selected(True)
                tab.pack(side="top", fill="both", expand=True, padx=5, pady=(0, 5))
            else:
                self.tab_nav_buttons[i].set_selected(False)
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

    def add_request_to_intruder_tab(self, content, host=None):
        for tab in self.tabs:
            if tab.is_empty:
                tab.hosturl = host
                tab.hostname_entry.insert(0, host)
                tab.positions_textbox.insert_text(content)
                tab.is_empty = False
                return
        else:
            new_tab = IntruderTab(self, len(self.tab_nav_buttons), content, host)
            self.add_tab(new_tab)

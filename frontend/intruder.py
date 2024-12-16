from common import *


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

        self.payloads = None

        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        self.hosturl_label = ctk.CTkLabel(self.top_bar, text="Host URL")
        self.hosturl_label.pack(padx=10, pady=10, side="left")

        self.hosturl_entry = TextEntry(self.top_bar, width=350)
        if self.hosturl is not None:
            self.hosturl_entry.insert(0, self.hosturl)
        self.hosturl_entry.pack(padx=(0, 10), pady=10, side="left")
        self.hosturl_entry.bind("<KeyRelease>", self.on_positions_textbox_change)

        self.start_attack_button = ActionButton(
            self.top_bar,
            text="Start attack",
            image=icon_attack,
            command=self.start_attack,
            state=tk.DISABLED
        )
        self.start_attack_button.pack(padx=10, pady=10, side="left")

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
        self.payloads_wrapper.pack(fill=tk.BOTH, expand=1, padx=10, pady=0)

        self.payloads_frames = {}

        self.payload_placeholder = ctk.CTkLabel(self.payloads_wrapper,
                                                text="Add variable position to get payload frame.",
                                                justify="left")
        self.payload_placeholder.pack(fill=tk.X, padx=10, pady=10)

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
            if len(self.hosturl_entry.get()) > 0:
                self.start_attack_button.configure(state=tk.NORMAL)
            else:
                self.start_attack_button.configure(state=tk.DISABLED)
        else:
            self.is_empty = True
            self.positions_textbox.configure(font=self.positions_textbox.monoscape_font_italic)
            self.start_attack_button.configure(state=tk.DISABLED)

    def _reset_positions_modified_flag(self):
        self.positions_textbox.edit_modified(False)

    def start_attack(self):
        print(f"Starting an attack...\nCurrent payloads:\n\t{self.payloads}")

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
                self.positions_textbox.tag_config(var_name, background="#8b115f", foreground="#b9d918")
                self.positions_textbox.insert(cursor, var_string)

                next_cursor = self.get_cursor_position()
                self.positions_textbox.tag_add(var_name, cursor, next_cursor)

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
                    if new_var:
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
        if len(self.payloads_frames) == 0:
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
        if len(self.payloads_frames) == 0:
            self.payload_placeholder.pack(fill=tk.X, padx=10, pady=10)

    def clear_all_positions_confirm(self):
        confirmation = ConfirmDialog(self, self.gui.gui_root,
                                     "Are you sure you want to clear all the positions?",
                                     "Yes", lambda: (self.clear_all_positions(), confirmation.destroy()),
                                     "No", lambda: confirmation.destroy())

    def add_payload(self, new_var):
        self.payload_placeholder.pack_forget()

        payloads_frame = ctk.CTkFrame(self.payloads_wrapper, fg_color="transparent", bg_color="transparent")
        payloads_frame.pack(fill=tk.X, padx=0, pady=0)

        payloads_subtitle = HeaderTitle(payloads_frame, text=new_var, size=18, height=18, pady=5)
        payloads_subtitle.pack(side="top", anchor="w", padx=0, pady=5)

        payloads_text = TextBox(payloads_frame, height=112)
        payloads_text.pack(side="left", fill=tk.X, expand=True, padx=(0, 10), pady=10)

        payloads_buttons = ctk.CTkFrame(payloads_frame, fg_color="transparent", bg_color="transparent")
        payloads_buttons.pack(side="right", fill=tk.Y, padx=(10, 0), pady=10)

        load_button = ctk.CTkButton(payloads_buttons, text="Load", command=lambda: load_payload(payloads_text))
        load_button.pack(side="top", padx=0, pady=(0, 5))

        clear_button = ctk.CTkButton(payloads_buttons, text="Clear", command=lambda: clear_payload(payloads_text),
                                     fg_color=color_acc3, hover_color=color_acc4)
        clear_button.pack(side="top", padx=0, pady=5)

        self.payloads_frames[new_var] = payloads_frame


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
                tab.hosturl_entry.insert(0, host)
                tab.positions_textbox.insert_text(content)
                tab.is_empty = False
                return
        else:
            new_tab = IntruderTab(self, len(self.tab_nav_buttons), content, host)
            self.add_tab(new_tab)

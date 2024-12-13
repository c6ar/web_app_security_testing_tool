import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from common import *
from functools import partial
import re


class IntruderNav(ctk.CTkFrame):
    def __init__(self, master, frames):
        super().__init__(master)
        self.configure(fg_color="transparent")
        self.master = master
        self.frames = frames
        self.current_frame = 0
        self.buttons = []
        self.buttons.append(NavButton(self,
                                      text="1",
                                      command=partial(self.show_frame, 0),
                                      font=ctk.CTkFont(family="Calibri", size=14, weight="normal"),
                                      background=color_bg_br,
                                      background_selected=color_bg))
        self.buttons[0].pack(side="left")
        self.add_button = NavButton(self,
                                    text="+",
                                    command=self.add_frame,
                                    font=ctk.CTkFont(family="Calibri", size=20, weight="normal"),
                                    background=color_bg_br)
        self.add_button.pack(side="right", padx=(10, 0))
        self.pack(side="top", fill="x", padx=15, pady=(10, 0))
        self.frames.append(IntruderFrame(master, 0, self))
        self.show_frame(0)

    def show_frame(self, n):
        self.current_frame = n
        # print(f"Debug Intruder: Showing frame: {n + 1}")
        for i, frame in enumerate(self.frames):
            if i == n:
                self.buttons[i].set_selected(True)
                frame.pack(side="top", fill="both", expand=True, padx=5, pady=(0, 5))
            else:
                self.buttons[i].set_selected(False)
                frame.pack_forget()

    def add_frame(self):
        new_id = len(self.buttons)
        # print(f"Debug Intruder: Adding frame: {new_id + 1}")
        new_frame_button = NavButton(self,
                                     text=str(new_id + 1),
                                     command=partial(self.show_frame, new_id),
                                     font=ctk.CTkFont(family="Calibri", size=14, weight="normal"),
                                     background=color_bg_br,
                                     background_selected=color_bg
                                     )
        self.buttons.append(new_frame_button)
        new_frame_button.pack(side="left", padx=(10, 0))

        new_frame = IntruderFrame(self.master, new_id, self)
        self.frames.append(new_frame)

    def delete_frame(self, n):
        # print(f"Debug Intruder: Deleting frame: {n + 1}")
        if self.current_frame == n:
            self.show_frame(n - 1)

        self.frames[n].pack_forget()
        self.frames.pop(n)
        self.buttons[n].pack_forget()
        self.buttons.pop(n)

        self.update_numbering()

    def update_numbering(self):
        for i, button in enumerate(self.buttons):
            button.main_button.configure(text=str(i + 1), command=partial(self.show_frame, i))
            self.frames[i].update_number(i)


class IntruderFrame(ctk.CTkFrame):
    def __init__(self, master, id_number, nav):
        super().__init__(master)
        self.configure(
            fg_color=color_bg,
            corner_radius=10,
            background_corner_colors=(color_bg_br, color_bg_br, color_bg_br, color_bg_br)
        )
        self.id = id_number
        self.nav = nav

        self.payloads = None

        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        self.start_attack_button = ctk.CTkButton(
            self.top_bar,
            text="Start attack",
            width=30,
            image=icon_attack,
            command=partial(self.start_attack, self.payloads),
            compound="left",
            corner_radius=32
        )
        self.start_attack_button.pack(padx=10, pady=10, side="left")

        if self.id != 0:
            icon_delete = ctk.CTkImage(
                light_image=Image.open(f"{ASSET_DIR}\\icon_delete.png"),
                dark_image=Image.open(f"{ASSET_DIR}\\icon_delete.png"), size=(20, 20))
            self.delete_frame_button = ctk.CTkButton(
                self.top_bar,
                text="Delete the card",
                width=30,
                image=icon_delete,
                command=partial(self.nav.delete_frame, self.id),
                compound="left",
                corner_radius=32
            )
            self.delete_frame_button.pack(padx=10, pady=10, side="right")

        self.positions_header = HeaderTitle(self, "Positions")
        self.positions_header.pack(fill=tk.X, padx=10, pady=0)

        self.positions_wrapper = ctk.CTkFrame(self, fg_color="transparent", corner_radius=10)
        self.positions_wrapper.pack(fill=tk.X, padx=10, pady=0)

        self.monoscape_font = ctk.CTkFont(family="Courier New", size=14, weight="normal")
        self.positions_text = ctk.CTkTextbox(self.positions_wrapper, height=224, wrap="none", font=self.monoscape_font,
                                             state="normal", padx=5, pady=5)
        self.positions_text.pack(side="left", fill=tk.X, expand=True, padx=10, pady=10)
        self.positions_text.insert("0.0", "Insert your variables = here.\nOr here = var")

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
                                                text="Add variable position to get payload frame.")
        self.payload_placeholder.pack(fill=tk.X, padx=10, pady=10)

    def update_number(self, id_number):
        self.id = id_number
        if self.id != 0:
            self.delete_frame_button.configure(
                command=partial(self.nav.delete_frame, self.id)
            )

    def start_attack(self, payloads):
        print(f"Starting an attack...\nCurrent payloads:\n\t{payloads}")

    def get_cursor_position(self):
        return self.positions_text.index(tk.INSERT)

    def get_selection(self):
        try:
            return self.positions_text.selection_get()
        except tk.TclError:
            return None

    def get_selection_indices(self):
        try:
            start_index = self.positions_text.index(tk.SEL_FIRST)
            end_index = self.positions_text.index(tk.SEL_LAST)
            return start_index, end_index
        except tk.TclError:
            return None, None

    def is_overlapping(self, start, end):
        for tag in self.positions_text.tag_names():
            if tag == "sel":
                continue
            tag_ranges = self.positions_text.tag_ranges(tag)
            # print(f"Debug: Checking tag range: {tag_ranges}")
            for i in range(0, len(tag_ranges), 2):
                tag_start = self.positions_text.index(tag_ranges[i])
                tag_end = self.positions_text.index(tag_ranges[i + 1])
                if (self.positions_text.compare(start, ">=", tag_start) and self.positions_text.compare(start, "<",
                                                                                                        tag_end)):
                    # Case when a new tag's start is within the already existing tag
                    # print(f"Debug Intruder/Variable: You are trying to create a variable tag ({start, end}) with its beginning inside the already exisiting one ({tag_start, tag_end})!")
                    return True
                elif (self.positions_text.compare(end, ">", tag_start) and self.positions_text.compare(end, "<=",
                                                                                                       tag_end)):
                    # Case when a new tag's end is within the already existing tag
                    # print(f"Debug Intruder/Variable: You are trying to create a variable tag ({start, end}) with its ending inside the already exisiting one ({tag_start, tag_end})!")
                    return True
                elif (self.positions_text.compare(start, "<", tag_start) and self.positions_text.compare(end, ">",
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
                self.positions_text.tag_config(var_name, background="#8b115f", foreground="#b9d918")
                self.positions_text.insert(cursor, var_string)

                next_cursor = self.get_cursor_position()
                self.positions_text.tag_add(var_name, cursor, next_cursor)

                self.add_payload(var_name)
            else:
                print("Error Intruder/Variable: Cursor is overlapping with an existing tag.")
        else:
            var_name = re.sub(r'\s+', '_', selection)
            var_name = re.sub(r'[^a-zA-Z0-9_]', '', var_name)
            for tag in self.positions_text.tag_names():
                if tag == var_name:
                    print(
                        f"Error Intruder/Variable: Cannot add variable. There currently is variable by this name \"{var_name}\".\nCurrent variable names in use:\n\t{self.positions_text.tag_names()}")
                    return
            var_string = f"§{var_name}§"
            x, y = selection_indices

            if x.split('.')[0] == y.split('.')[0]:
                if not self.is_overlapping(x, y):
                    self.positions_text.delete(x, y)
                    self.positions_text.insert(x, var_string)
                    y = self.get_cursor_position()
                    self.positions_text.tag_config(var_name, background="#8b115f", foreground="#b9d918")
                    self.positions_text.tag_add(var_name, x, y)
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
            for tag in self.positions_text.tag_names():
                if tag == "sel":
                    continue
                tag_ranges = self.positions_text.tag_ranges(tag)
                for i in range(0, len(tag_ranges), 2):
                    tag_start = self.positions_text.index(tag_ranges[i])
                    tag_end = self.positions_text.index(tag_ranges[i + 1])
                    if self.positions_text.compare(cursor, ">=", tag_start) and self.positions_text.compare(cursor, "<",
                                                                                                            tag_end):
                        # Cursor is inside an existing tag, remove the tag
                        self.positions_text.tag_remove(tag, tag_start, tag_end)
                        self.positions_text.tag_delete(tag)
                        self.positions_text.delete(tag_start, tag_end)
                        self.positions_text.insert(tag_start, tag)
                        self.payloads_frames[tag].pack_forget()
                        del self.payloads_frames[tag]
                        return
            # Case 2: Cursor is outside of any tag, remove all the tags.
            self.clear_all_positions_confirm()
        else:
            # Remove all tags that are overlapping or within the selection
            x, y = selection_indices
            for tag in self.positions_text.tag_names():
                if tag == "sel":
                    continue
                tag_ranges = self.positions_text.tag_ranges(tag)
                for i in range(0, len(tag_ranges), 2):
                    tag_start = self.positions_text.index(tag_ranges[i])
                    tag_end = self.positions_text.index(tag_ranges[i + 1])
                    if (self.positions_text.compare(x, "<=", tag_start) and self.positions_text.compare(y, ">=",
                                                                                                        tag_end)) or \
                            (self.positions_text.compare(x, ">=", tag_start) and self.positions_text.compare(x, "<",
                                                                                                             tag_end)) or \
                            (self.positions_text.compare(y, ">", tag_start) and self.positions_text.compare(y, "<=",
                                                                                                            tag_end)):
                        # Tag is overlapping or within the selection, remove the tag
                        self.positions_text.tag_remove(tag, tag_start, tag_end)
                        self.positions_text.tag_delete(tag)
                        self.positions_text.delete(tag_start, tag_end)
                        self.positions_text.insert(tag_start, tag)
                        self.payloads_frames[tag].pack_forget()
                        del self.payloads_frames[tag]

    def clear_all_positions(self):
        for tag in self.positions_text.tag_names():
            if tag == "sel":
                continue
            tag_ranges = self.positions_text.tag_ranges(tag)
            for i in range(0, len(tag_ranges), 2):
                tag_start = self.positions_text.index(tag_ranges[i])
                tag_end = self.positions_text.index(tag_ranges[i + 1])
                self.positions_text.tag_remove(tag, tag_start, tag_end)
                self.positions_text.tag_delete(tag)
                self.positions_text.delete(tag_start, tag_end)
                self.positions_text.insert(tag_start, tag)
                self.payloads_frames[tag].pack_forget()
                del self.payloads_frames[tag]

    def clear_all_positions_confirm(self):
        confirmation = ConfirmDialog(self,
                                     "Are you sure you want to clear all the positions?",
                                     "Yes", lambda: (self.clear_all_positions(), confirmation.destroy()),
                                     "No", lambda: confirmation.destroy())

    def add_payload(self, new_var):
        self.payload_placeholder.pack_forget()

        payloads_frame = ctk.CTkFrame(self.payloads_wrapper, fg_color="transparent", bg_color="transparent")
        payloads_frame.pack(fill=tk.X, padx=0, pady=0)

        payloads_subtitle = HeaderTitle(payloads_frame, text=new_var, size=18, height=18, pady=5)
        payloads_subtitle.pack(side="top", anchor="w", padx=0, pady=5)

        payloads_text = ctk.CTkTextbox(payloads_frame, height=112, wrap="none", font=self.monoscape_font,
                                       state="normal", padx=5, pady=5)
        payloads_text.pack(side="left", fill=tk.X, expand=True, padx=(0, 10), pady=10)

        payloads_buttons = ctk.CTkFrame(payloads_frame, fg_color="transparent", bg_color="transparent")
        payloads_buttons.pack(side="right", fill=tk.Y, padx=(10, 0), pady=10)

        load_button = ctk.CTkButton(payloads_buttons, text="Load", command=lambda: self.load_payload(payloads_text))
        load_button.pack(side="top", padx=0, pady=(0, 5))

        clear_button = ctk.CTkButton(payloads_buttons, text="Clear", command=lambda: self.clear_payload(payloads_text),
                                     fg_color=color_acc3, hover_color=color_acc4)
        clear_button.pack(side="top", padx=0, pady=5)

        self.payloads_frames[new_var] = payloads_frame

    def load_payload(self, payloads_text):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])

        if file_path:
            try:
                with open(file_path, 'r') as file:
                    file_content = file.read()

                payloads_text.delete("1.0", tk.END)

                payloads_text.insert("1.0", file_content)

            except Exception as e:
                print(f"Error reading the file: {e}")

    def clear_payload(self, payloads_text):
        payloads_text.delete("1.0", tk.END)


class GUIIntruder(ctk.CTkFrame):
    def __init__(self, master, root):
        super().__init__(master)
        self.configure(fg_color="transparent")
        self.root = root
        self.frames = []
        self.nav = IntruderNav(self, self.frames)

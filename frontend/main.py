import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import pyperclip
import os
from pathlib import Path
from mod1 import *
import socket
import subprocess
color_bg = "#222"
color_bg_br = "#333"
color_acc = "#d68f13"
color_acc2 = "#ffab17"


class NavButton(ctk.CTkFrame):
    def __init__(self, master, text, command, font):
        super().__init__(master)

        text_width = font.measure(text)
        button_width = text_width + 25

        self.main_button = ctk.CTkButton(self)
        self.main_button.configure(
            width=button_width,
            corner_radius=0,
            fg_color=color_bg,
            bg_color=color_bg,
            hover_color=color_acc,
            text=text,
            command=command,
            font=font)
        self.main_button.pack()

        self.bottom_border = ctk.CTkFrame(self, height=3, width=self.main_button.winfo_reqwidth(), fg_color=color_bg)
        self.bottom_border.pack(side="bottom", fill="x")

        self.selected = False

    def set_selected(self, value):
        self.selected = value
        if self.selected:
            self.main_button.configure(fg_color=color_bg_br)
            self.bottom_border.configure(fg_color=color_acc)
        else:
            self.main_button.configure(fg_color=color_bg)
            self.bottom_border.configure(fg_color=color_bg)


class FancyTreeview(ttk.Treeview):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.popup_menu = tk.Menu(self, tearoff=0)
        self.popup_menu.add_command(label="Delete", command=self.delete_selected)
        self.popup_menu.add_command(label="Select All", command=self.select_all)
        self.popup_menu.add_command(label="Copy", command=self.copy_selected)
        self.bind("<Button-3>", self.popup)  # Right-click event

    def popup(self, event):
        try:
            self.popup_menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.popup_menu.grab_release()

    def delete_selected(self):
        for item in self.selection():
            self.delete(item)

    def select_all(self):
        for item in self.get_children():
            self.selection_add(item)

    def copy_selected(self):
        selected_items = self.selection()
        copied_text = ""
        for item in selected_items:
            values = self.item(item, 'values')
            copied_text += ", ".join(values) + "\n"
        pyperclip.copy(copied_text.strip())


class FileTree(ttk.Frame):
    """
    Class created using code from: https://pythonassets.com/posts/treeview-in-tk-tkinter/
    """
    def __init__(self, window: tk.Tk | tk.Toplevel, path) -> None:
        super().__init__(window)
        # show="tree" removes the column header, since we
        # are not using the table feature.
        self.treeview = ttk.Treeview(self, show="tree")
        self.treeview.grid(row=0, column=0, sticky="nsew")
        # Call the item_opened() method each item an item
        # is expanded.
        self.treeview.tag_bind(
            "fstag", "<<TreeviewOpen>>", self.item_opened)
        # Make sure the treeview widget follows the window
        # when resizing.
        for w in (self, window):
            w.rowconfigure(0, weight=1)
            w.columnconfigure(0, weight=1)
        self.grid(row=0, column=0, sticky="nsew")
        # This dictionary maps the treeview items IDs with the
        # path of the file or folder.
        self.fsobjects: dict[str, Path] = {}
        self.file_image = tk.PhotoImage(file="frontend\\file.png") 
        self.folder_image = tk.PhotoImage(file="frontend\\folder.png")

        self.popup_menu = tk.Menu(self.treeview, tearoff=0)
        self.popup_menu.add_command(label="Delete", command=self.delete_selected)
        self.popup_menu.add_command(label="Select All", command=self.select_all)
        self.popup_menu.add_command(label="Copy", command=self.copy_selected)
        self.treeview.bind("<Button-3>", self.popup)  # Right-click event

        # Load directory from Path.

        self.load_tree(path)

    def popup(self, event):
        try:
            self.popup_menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.popup_menu.grab_release()

    def delete_selected(self):
        for item in self.treeview.selection():
            self.treeview.delete(item)

    def select_all(self):
        for item in self.treeview.get_children():
            self.treeview.selection_add(item)

    def copy_selected(self):
        selected_items = self.treeview.selection()
        copied_text = ""
        for item in selected_items:
            copied_text += f"\"{self.fsobjects[item]}\"\n"
        pyperclip.copy(copied_text.strip())

    def safe_iterdir(self, path: Path) -> tuple[Path, ...] | tuple[()]:
        """
        Like `Path.iterdir()`, but do not raise on permission errors.
        """
        try:
            return tuple(path.iterdir())
        except PermissionError:
            print("You don't have permission to read", path)
            return ()

    def get_icon(self, path: Path) -> tk.PhotoImage:
        """
        Return a folder icon if `path` is a directory and
        a file icon otherwise.
        """
        return self.folder_image if path.is_dir() else self.file_image

    def insert_item(self, name: str, path: Path, parent: str = "") -> str:
        """
        Insert a file or folder into the treeview and return the item ID.
        """
        iid = self.treeview.insert(
            parent, tk.END, text=name, tags=("fstag",),
            image=self.get_icon(path))
        self.fsobjects[iid] = path

        return iid

    def load_tree(self, path: Path, parent: str = "") -> None:
        """
        Load the contents of `path` into the treeview.
        """
        for fsobj in self.safe_iterdir(path):
            fullpath = path / fsobj
            child = self.insert_item(fsobj.name, fullpath, parent)
            # Preload the content of each directory within `path`.
            # This is necessary to make the folder item expandable.
            if fullpath.is_dir():
                for sub_fsobj in self.safe_iterdir(fullpath):
                    self.insert_item(sub_fsobj.name, fullpath / sub_fsobj, child)

    def load_subitems(self, iid: str) -> None:
        """
        Load the content of each folder inside the specified item
        into the treeview.
        """
        for child_iid in self.treeview.get_children(iid):
            if self.fsobjects[child_iid].is_dir():
                self.load_tree(self.fsobjects[child_iid],
                            parent=child_iid)

    def item_opened(self, _event: tk.Event) -> None:
        """
        Handler invoked when a folder item is expanded.
        """
        # Get the expanded item.
        iid = self.treeview.selection()[0]
        # If it is a folder, loads its content.
        self.load_subitems(iid)


class GUIDash(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.configure(fg_color="transparent")
        self.target_title = ctk.CTkLabel(self, text="DASHBOARD PLACEHOLDER.")
        self.target_title.pack(pady=5)


class GUITarget(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.configure(fg_color="transparent")

        self.targetnav = ctk.CTkFrame(self, fg_color=color_bg)
        self.targetnav.pack(side="top", fill="x", padx=0, pady=0)

        buttons_set = {
            "Site Map": self.show_sitemap,
            "Scope": self.show_scope,
            "Issue Definitions": self.show_definitions
        }

        self.navbuttons = {}

        for name, command in buttons_set.items():
            self.navbuttons[name] = NavButton(self.targetnav, text=name, command=command, font=ctk.CTkFont(family="Calibri", size=14, weight="normal"))
            self.navbuttons[name].pack(side="left")

        self.content_wrapper = ctk.CTkFrame(self, fg_color="transparent")
        self.content_wrapper.pack(side="top", fill="both", expand=True)

        self.show_sitemap()

    def show_sitemap(self):
        self.clear_content_frame()

        self.paned_window = tk.PanedWindow(self.content_wrapper, orient=tk.HORIZONTAL, background=color_bg, width=self.winfo_reqwidth() // 3)
        self.paned_window.pack(fill="both", expand=True)

        # Left pane (vertical)
        self.left_pane = ctk.CTkFrame(self.paned_window, bg_color="transparent")
        self.paned_window.add(self.left_pane)

        # Right PanedWindow (vertical orientation)
        self.right_paned_window = tk.PanedWindow(self.paned_window, orient=tk.VERTICAL)
        self.paned_window.add(self.right_paned_window, stretch="always")

        # Top right pane
        self.top_right_pane = ctk.CTkFrame(self.right_paned_window, bg_color="transparent")
        self.right_paned_window.add(self.top_right_pane, stretch="always")

        # Bottom right pane
        self.bottom_right_pane = ctk.CTkFrame(self.right_paned_window, bg_color="transparent")
        self.right_paned_window.add(self.bottom_right_pane, stretch="always")

        # Example content for the panes

        current_directory = os.path.dirname(os.path.abspath(__file__))
        files = os.listdir(current_directory)
        self.current_path = Path.cwd()
        self.site_map_tree = FileTree(self.left_pane, path=self.current_path)
        # self.site_map_tree.heading('pages', text='Pages')
        # for i, file_name in enumerate(files):
        #     self.site_map_tree.insert('', 'end', values=(file_name))
        self.site_map_tree.pack(fill='both', expand=True)

        self.top_right_label = ctk.CTkLabel(self.top_right_pane, text="Top Right Pane", anchor="center")
        self.top_right_label.pack(fill="both", expand=True, padx=10, pady=10)

        self.bottom_right_label = ctk.CTkLabel(self.bottom_right_pane, text="Bottom Right Pane", anchor="center")
        self.bottom_right_label.pack(fill="both", expand=True, padx=10, pady=10)

        self.select_button(self.navbuttons["Site Map"])

        self.update_idletasks()  # Ensure the window is fully drawn before configuring panes
        self.paned_window.paneconfigure(self.left_pane, minsize=self.winfo_reqwidth() // 3)

    def show_scope(self):
        self.clear_content_frame()
        self.target_title = ctk.CTkLabel(self.content_wrapper, text="Scope content here")
        self.target_title.pack(pady=5)
        self.select_button(self.navbuttons["Scope"])

    def show_definitions(self):
        self.clear_content_frame()
        self.target_title = ctk.CTkLabel(self.content_wrapper, text="Definitions content here")
        self.target_title.pack(pady=5)
        self.select_button(self.navbuttons["Issue Definitions"])

    def clear_content_frame(self):
        for widget in self.content_wrapper.winfo_children():
            widget.pack_forget()

    def select_button(self, selected_button):
        for button in self.navbuttons.values():
            if button == selected_button:
                button.set_selected(True)
            else:
                button.set_selected(False)


class GUIProxy(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.configure(fg_color="transparent")
        self.target_title = ctk.CTkLabel(self, text="Proxy tab content here")
        self.target_title.pack(pady=5)
        self.scan_button = ctk.CTkButton(self, text="Start Scan", command=self.scan)
        self.scan_button.pack(pady=5)
        self.scan_textbox = ctk.CTkTextbox(self, width=700, height=450)

    def scan(self):
        path = r"C:\Users\kacpe\OneDrive\Dokumenty\GitHub\web_app_security_testing_tool1\backend"
        command = f"start cmd /K mitmdump -s proxy.py "

        try:
            # Uruchamiamy nowy proces z otwartym terminalem w podanej lokalizacji
            subprocess.Popen(command, cwd=path, shell=True)
            print(f"Uruchomiono: {command}")
        except Exception as e:
            print(f"Error starting mitmdump: {e}")



class GUIIntruder(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.configure(fg_color="transparent")


class GUIRepeater(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.configure(fg_color="transparent")
        self.inspect_label = ctk.CTkLabel(self, text="Inspecting HTTP requests and responses...")
        self.inspect_label.pack(pady=5)
        self.inspect_button = ctk.CTkButton(self, text="Start Inspection", command=self.inspect)
        self.inspect_button.pack(pady=5)

    def inspect(self):
        self.inspect_label.configure(text="Inspection started...")


class GUILogs(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.configure(fg_color="transparent")

        self.logs_label = ctk.CTkLabel(self, text="Displaying logs...")
        self.logs_label.pack(pady=5)
        self.logs_button = ctk.CTkButton(self, text="Show Logs", command=self.show_logs_content)
        self.logs_button.pack(pady=5)

    def show_logs_content(self):
        self.logs_label.pack_forget()
        self.logs_label.configure(text="Logs displayed.")
        self.logs_button.pack(pady=25)
        self.logs_label.pack(pady=5)


class GUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Security Testing App")
        self.geometry("1880x900+10+20")
        self.configure(fg_color=color_bg, bg_color=color_bg)

        self.mainnav = ctk.CTkFrame(self, bg_color=color_bg, fg_color=color_bg)
        self.mainnav.pack(side="top", fill="x", padx=0, pady=0)

        buttons_set = {
            "Dashboard": self.show_dashboard,
            "Target": self.show_target,
            "Proxy": self.show_proxy,
            "Intruder": self.show_intruder,
            "Repeater": self.show_repeater,
            "Logs": self.show_logs
        }

        self.navbuttons = {}

        for name, command in buttons_set.items():
            self.navbuttons[name] = NavButton(self.mainnav, text=name, command=command,
                                              font=ctk.CTkFont(family="Calibri", size=15, weight="bold"))
            self.navbuttons[name].pack(side="left")

        self.content_wrapper = ctk.CTkFrame(self, fg_color=color_bg_br, bg_color=color_bg_br)
        self.content_wrapper.pack(side="top", fill="both", expand=True)

        self.dashboard_frame = GUIDash(self.content_wrapper)
        self.target_frame = GUITarget(self.content_wrapper)
        self.proxy_frame = GUIProxy(self.content_wrapper)
        self.intruder_frame = GUIIntruder(self.content_wrapper)
        self.repeater_frame = GUIRepeater(self.content_wrapper)
        self.logs_frame = GUILogs(self.content_wrapper)

        self.show_target()

    def show_dashboard(self):
        self.clear_content_frame()
        self.dashboard_frame.pack(side="top", fill="both", expand=True)
        self.select_button(self.navbuttons["Dashboard"])

    def show_target(self):
        self.clear_content_frame()
        self.target_frame.pack(side="top", fill="both", expand=True)
        self.select_button(self.navbuttons["Target"])

    def show_proxy(self):
        self.clear_content_frame()
        self.proxy_frame.pack(side="top", fill="both", expand=True)
        self.select_button(self.navbuttons["Proxy"])

    def show_intruder(self):
        self.clear_content_frame()
        self.intruder_frame.pack(side="top", fill="both", expand=True)
        self.select_button(self.navbuttons["Intruder"])

    def show_repeater(self):
        self.clear_content_frame()
        self.repeater_frame.pack(side="top", fill="both", expand=True)
        self.select_button(self.navbuttons["Repeater"])

    def show_logs(self):
        self.clear_content_frame()
        self.logs_frame.pack(side="top", fill="both", expand=True)
        self.select_button(self.navbuttons["Logs"])

    def clear_content_frame(self):
        for widget in self.content_wrapper.winfo_children():
            widget.pack_forget()

    def select_button(self, selected_button):
        for button in self.navbuttons.values():
            if button == selected_button:
                button.set_selected(True)
            else:
                button.set_selected(False)


if __name__ == "__main__":
    app = GUI()
    app.mainloop()
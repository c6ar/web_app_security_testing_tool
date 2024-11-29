from head import *
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import pyperclip
import os


class FileTree(ttk.Frame):
    """
    Class created using code from: https://pythonassets.com/posts/treeview-in-tk-tkinter/
    Klasa do przepisania
    """
    def __init__(self, window, path) -> None:
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
        self.file_image = tk.PhotoImage(file=f"{ASSET_DIR}\\file.png")
        self.folder_image = tk.PhotoImage(file=f"{ASSET_DIR}/folder.png")

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

class GUITarget(ctk.CTkFrame):
    def __init__(self, master, root):
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

        CURRENT_DIRectory = os.path.dirname(os.path.abspath(__file__))
        files = os.listdir(CURRENT_DIRectory)
        self.current_path = Path.cwd()
        print(self.current_path)


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

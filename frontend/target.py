from head import *
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import pyperclip
import os




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

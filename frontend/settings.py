from common import *


class Settings(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.root = master
        self.title("WASTT settings")
        self.configure(fg_color=color_bg_br, bg_color=color_bg_br)
        self.protocol("WM_DELETE_WINDOW", self.on_settings_close)
        self.transient(master)

        settings_width = int(master.winfo_width() * 0.5)
        settings_height = int(master.winfo_height() * 0.9)
        center_window(master, self, settings_width, settings_height)

        self.withdraw()
        self.settings_changed = False
        self.settings_status_label = None

        wrapper = ctk.CTkScrollableFrame(self, fg_color="transparent", bg_color="transparent")
        wrapper.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        label_width = int(settings_width / 5)

        # TODO FRONTEND P2: Next to each label there will be an info icon, after clicking, opens a info window like About
        #  that can be dismissed with esc, space and enter
        #  and it describes settings
        # ================================================
        # General settings isle
        # ================================================
        general_isle = DarkBox(wrapper)
        general_isle.pack(fill=tk.X, padx=10, pady=(10, 5))
        general_header = HeaderTitle(general_isle, "General settings")
        general_header.pack(fill=tk.X, padx=10, pady=(10, 5))

        theme_box = Box(general_isle)
        theme_box.pack(fill=tk.X, padx=10, pady=5)
        theme_label = Label(theme_box, text="Theme", width=label_width, anchor=tk.E)
        theme_label.pack(side=tk.LEFT, padx=(10, 5), pady=5)
        self.theme_options = ctk.CTkOptionMenu(
            theme_box,
            values=["System", "Light", "Dark"],
            width=200,
            command=lambda option: self.on_settings_change()
        )
        self.theme_options.pack(side=tk.LEFT, padx=(5, 10), pady=5)

        lang_box = Box(general_isle)
        lang_box.pack(fill=tk.X, padx=10, pady=(10, 15))
        lang_label = Label(lang_box, text="Language", width=label_width, anchor=tk.E)
        lang_label.pack(side=tk.LEFT, padx=(10, 5), pady=5)
        self.lang_options = ctk.CTkOptionMenu(
            lang_box,
            values=["English", "Polish", "German", "Spanish"],
            width=200,
            command=lambda option: self.on_settings_change()
        )
        self.lang_options.pack(side=tk.LEFT, padx=(5, 10), pady=5)

        # ================================================
        # Proxy settings isle
        # ================================================
        proxy_isle = DarkBox(wrapper)
        proxy_isle.pack(fill=tk.X, padx=10, pady=5)

        proxy_header = HeaderTitle(proxy_isle, "Proxy settings")
        proxy_header.pack(fill=tk.X, padx=10, pady=(10, 5))

        proxy_ip_port_box = Box(proxy_isle)
        proxy_ip_port_box.pack(fill=tk.X, padx=10, pady=5)
        proxy_ip_port_label = Label(proxy_ip_port_box, text="Address & Port", width=label_width, anchor=tk.E)
        proxy_ip_port_label.pack(side=tk.LEFT, padx=(10, 5), pady=5)
        self.proxy_ip_input = TextEntry(proxy_ip_port_box, width=200)
        self.proxy_ip_input.bind("<KeyRelease>", self.on_settings_change)
        self.proxy_ip_input.insert(0, RUNNING_CONFIG['proxy_host_address'])
        self.proxy_ip_input.pack(side=tk.LEFT, padx=(5, 0), pady=5)
        proxy_colon_label = Label(proxy_ip_port_box, text=":", anchor=tk.E)
        proxy_colon_label.pack(side=tk.LEFT, padx=0, pady=5)
        self.proxy_port_input = TextEntry(proxy_ip_port_box, width=100)
        self.proxy_port_input.insert(0, RUNNING_CONFIG['proxy_port'])
        self.proxy_port_input.bind("<KeyRelease>", self.on_settings_change)
        self.proxy_port_input.pack(side=tk.LEFT, padx=(0, 10), pady=5)

        proxy_rerun_box = Box(proxy_isle)
        proxy_rerun_box.pack(fill=tk.X, padx=10, pady=(10, 5))
        proxy_rerun_box.grid_columnconfigure(0, minsize=label_width + 10)
        proxy_re_run_label = Label(
            proxy_rerun_box,
            text="Reload proxy",
            width=label_width,
            anchor=tk.E
        )
        proxy_re_run_label.grid(row=0, column=0, sticky=tk.E, padx=(10, 5), pady=5)
        self.proxy_re_run_with_scope_checkbox = ctk.CTkCheckBox(
            proxy_rerun_box,
            text="Retain current scope on reload",
            width=100
        )
        self.proxy_re_run_with_scope_checkbox.grid(row=0, column=1, padx=5, pady=5)
        proxy_re_run_button = ActionButton(
            proxy_rerun_box,
            text="Reload proxy process",
            image=icon_reload,
            command=self.reload_proxy,
            corner_radius=5
        )
        proxy_re_run_button.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        proxy_logs_box = Box(proxy_isle)
        proxy_logs_box.pack(fill=tk.X, padx=10, pady=(10, 5))
        proxy_logs_box.grid_columnconfigure(0, minsize=label_width + 10)
        proxy_logs_label = Label(proxy_logs_box, text="Proxy logging", width=label_width, anchor=tk.E)
        proxy_logs_label.grid(row=0, column=0, sticky=tk.E, padx=(10, 5), pady=5)
        self.proxy_logs_checkbox = ctk.CTkCheckBox(
            proxy_logs_box,
            text="Log Proxy output to a file.",
            command=self.change_proxy_logs_location_click
        )
        self.proxy_logs_checkbox.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.proxy_logs_location_input = TextEntry(
            proxy_logs_box,
            width=450
        )
        self.proxy_logs_location_input.insert(0, RUNNING_CONFIG['proxy_logs_location'])
        self.proxy_logs_location_input.bind("<KeyRelease>", self.on_settings_change)
        self.proxy_logs_location_input.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W + tk.E)
        self.proxy_logs_location_button = ActionButton(
            proxy_logs_box,
            text="",
            image=icon_folder,
            width=25,
            corner_radius=5,
            command=self.select_log_file_dir
        )
        self.proxy_logs_location_button.grid(row=1, column=2, padx=5, pady=5, sticky=tk.E)
        if RUNNING_CONFIG['proxy_logging']:
            self.proxy_logs_checkbox.select()
            self.proxy_logs_location_input.configure(state=tk.NORMAL)
            self.proxy_logs_location_button.configure(state=tk.NORMAL)
        else:
            self.proxy_logs_location_input.configure(state=tk.DISABLED)
            self.proxy_logs_location_button.configure(state=tk.DISABLED)

        proxy_cmd_box = Box(proxy_isle)
        proxy_cmd_box.pack(fill=tk.X, padx=10, pady=10)
        proxy_cmd_box_label = Label(proxy_cmd_box, text="Proxy terminal", width=label_width, anchor=tk.E)
        proxy_cmd_box_label.pack(side=tk.LEFT, padx=(10, 5), pady=5)
        self.proxy_cmd_box_checkbox = ctk.CTkCheckBox(
            proxy_cmd_box,
            text="Show Proxy output in terminal window.",
            command=self.change_proxy_logs_location_click
        )
        if RUNNING_CONFIG['proxy_console']:
            self.proxy_cmd_box_checkbox.select()
        self.proxy_cmd_box_checkbox.pack(side=tk.LEFT, padx=5, pady=(5, 10))

        # ================================================
        # Ports settings sub-isle
        # ================================================
        ports_header = HeaderTitle(proxy_isle, "Backend - Frontend ports", size=18)
        ports_header.pack(fill=tk.X, padx=10, pady=5)

        configurations = {
            'back_front_request_to_traffic_port': "HTTP Traffic (Back >> Front)",
            'back_front_request_to_intercept_port': "Intercept Traffic (Back >> Front)",
            'front_back_forward_request_port': "Forward Request (Front >> Back)",
            'front_back_drop_request_port': "Drop Request (Front >> Back)",
            'front_back_scope_update_port': "Scope Update (Front >> Back)",
            'front_back_intercept_toggle_port': "Toggle Web Interceptor (Front >> Back)"
        }
        self.bf_port_inputs = {}

        for config_key, text in configurations.items():
            box = Box(proxy_isle)
            box.pack(fill=tk.X, padx=10, pady=5)

            label = Label(box, text=text, width=label_width+80, anchor=tk.E)
            label.pack(side=tk.LEFT, padx=(10, 5), pady=5)

            self.bf_port_inputs[config_key] = TextEntry(box, width=100)
            self.bf_port_inputs[config_key].insert(0, RUNNING_CONFIG[config_key])
            self.bf_port_inputs[config_key].bind("<KeyRelease>", self.on_settings_change)
            self.bf_port_inputs[config_key].pack(side=tk.LEFT, padx=(5, 0), pady=5)

        # ================================================
        # Browser settings isle
        # ================================================
        browser_isle = DarkBox(wrapper)
        browser_isle.pack(fill=tk.X, padx=10, pady=5)
        browser_settings = HeaderTitle(browser_isle, "Browser settings")
        browser_settings.pack(fill=tk.X, padx=10, pady=(10, 5))
        label1 = Label(browser_isle, text="Arguments for the Selenium browser will be here.")
        label1.pack(side=tk.LEFT, padx=20, pady=20)
        # TODO FRONTEND P3: Browser settings.

        # ================================================
        # Logs settings isle
        # ================================================
        logs_isle = DarkBox(wrapper)
        logs_isle.pack(fill=tk.X, padx=10, pady=5)
        logs_settings = HeaderTitle(logs_isle, "Logs settings")
        logs_settings.pack(fill=tk.X, padx=10, pady=(10, 5))
        label2 = Label(logs_isle, text="Logs default saving locations will be here.")
        label2.pack(side=tk.LEFT, padx=20, pady=20)
        # TODO FRONTEND P3: Logs settings.

        # ================================================
        # Debug settings isle
        # ================================================
        debug_isle = DarkBox(wrapper)
        debug_isle.pack(fill=tk.X, padx=10, pady=5)
        debug_settings = HeaderTitle(debug_isle, "Debug settings")
        debug_settings.pack(fill=tk.X, padx=10, pady=(10, 5))

        debug_mode_box = Box(debug_isle)
        debug_mode_box.pack(fill=tk.X, padx=10, pady=10)
        debug_mode_label = Label(debug_mode_box, text="Debug mode", width=label_width, anchor=tk.E)
        debug_mode_label.pack(side=tk.LEFT, padx=(10, 5), pady=5)
        self.debug_mode_checkbox = ctk.CTkCheckBox(
            debug_mode_box,
            text="Show all application operations in the Python's output.",
            command=self.on_settings_change
        )
        if RUNNING_CONFIG['debug_mode']:
            self.debug_mode_checkbox.select()
        self.debug_mode_checkbox.pack(side=tk.LEFT, padx=5, pady=(5, 10))

        debug_running_conf_box = Box(debug_isle)
        debug_running_conf_box.pack(fill=tk.X, padx=10, pady=10)
        debug_running_conf_label = Label(debug_running_conf_box, text="Show running conf", width=label_width, anchor=tk.E)
        debug_running_conf_label.pack(side=tk.LEFT, padx=(10, 5), pady=5)
        self.debug_running_conf_checkbox = ctk.CTkCheckBox(
            debug_running_conf_box,
            text="Show currently running configuration on app's start up in the Python's output.",
            command=self.on_settings_change
        )
        if RUNNING_CONFIG['debug_show_running_config']:
            self.debug_running_conf_checkbox.select()
        self.debug_running_conf_checkbox.pack(side=tk.LEFT, padx=5, pady=(5, 10))

        # ================================================
        # Bottom Bar
        # ================================================
        bottom_bar = ctk.CTkFrame(
            self,
            fg_color=color_bg,
            bg_color="transparent",
            corner_radius=10
        )
        bottom_bar.pack(fill=tk.X, padx=(15, 25), pady=(5, 20))
        self.settings_status_label = ctk.CTkLabel(bottom_bar, text="Settings unchanged.")
        self.settings_status_label.pack(side=tk.LEFT, padx=10, pady=10)
        self.save_button = ActionButton(
            bottom_bar,
            text="Save",
            command=self.save_settings,
            state=tk.DISABLED
        )
        self.cancel_button = ActionButton(
            bottom_bar,
            text="Cancel",
            command=self.destroy,
            fg_color=color_acc3,
            hover_color=color_acc4
        )
        self.cancel_button.pack(side=tk.RIGHT, padx=10, pady=10)
        self.save_button.pack(side=tk.RIGHT, padx=10, pady=10)

    def on_settings_change(self, _event=None):
        self.settings_status_label.configure(text="Settings has been changed. Save to apply changes.")
        self.save_button.configure(state=tk.NORMAL)
        self.settings_changed = True

    def on_settings_close(self):
        if self.settings_changed:
            confirm = ConfirmDialog(
                self.root,
                self,
                "You have unsaved changes. Do you want to save them?",
                "Save changes?",
                "Save",
                lambda: (self.save_settings(), confirm.destroy()),
                "Cancel",
                lambda: confirm.destroy(),
                "Discard",
                lambda: (self.destroy_window(), confirm.destroy())
            )
        else:
            self.destroy_window()

    def destroy_window(self):
        self.root.settings_window = None
        self.destroy()

    def reload_proxy(self, retain_scope=False):
        if retain_scope or self.proxy_re_run_with_scope_checkbox.get():
            current_scope = self.root.proxy_tab.current_scope
            self.root.proxy_tab.run_mitmdump(current_scope)
            dprint("[DEBUG] Reloading with scope.")
        else:
            self.root.proxy_tab.run_mitmdump()
            dprint("[DEBUG] Reloading without scope.")

    def change_proxy_logs_location_click(self):
        self.on_settings_change()
        if self.proxy_logs_checkbox.get():
            self.proxy_logs_location_input.configure(state=tk.NORMAL, text_color=color_text)
            self.proxy_logs_location_button.configure(state=tk.NORMAL, fg_color=color_acc)
        else:
            self.proxy_logs_location_input.configure(state=tk.DISABLED, text_color="gray")
            self.proxy_logs_location_button.configure(state=tk.DISABLED, fg_color="gray")

    def select_log_file_dir(self):
        self.on_settings_change()
        file_path = filedialog.askdirectory(
            initialdir=RUNNING_CONFIG['proxy_logs_location'],
            title="Select directory for proxy logs"
        )
        if file_path:
            self.proxy_logs_location_input.delete(0, tk.END)
            self.proxy_logs_location_input.insert(0, file_path)

    def save_settings(self):
        new_config = {
            "theme": self.theme_options.get(),
            "lang": self.lang_options.get(),
            "proxy_host_address": self.proxy_ip_input.get(),
            "proxy_port": self.proxy_port_input.get(),
            "proxy_logging": self.proxy_logs_checkbox.get(),
            "proxy_logs_location": self.proxy_logs_location_input.get(),
            "proxy_console": self.proxy_cmd_box_checkbox.get(),
            "debug_mode": False,
            "debug_show_running_config": False
        }
        for port_key, port_input in self.bf_port_inputs.items():
            new_config[port_key] = port_input.get()

        dprint("================================================\n"
               "[DEBUG] New config:")
        for key, value in new_config.items():
            dprint(f"\t{key}: {value}")
        dprint("================================================")

        # TODO FRONTEND P2: If settings such as Proxy require restart show pop-up first.
        if (new_config["proxy_console"] != RUNNING_CONFIG["proxy_console"] or
                new_config["proxy_host_address"] != RUNNING_CONFIG["proxy_host_address"] or
                new_config["proxy_port"] != RUNNING_CONFIG["proxy_port"]):
            RUNNING_CONFIG["proxy_console"] = new_config["proxy_console"]
            self.reload_proxy(retain_scope=True)

        # TODO FRONTEND P2: Full implementation of settings.
        # TODO FRONTEND P2: If settings such as Theme or Language require restart show pop-up.
        # save_config(new_config)

        dprint("[DEBUG] Saving settings.")
        self.destroy_window()

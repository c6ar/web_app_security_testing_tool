from common import *

# TODO FRONTEND P3: Logs/Reporting


class GUILogs(ctk.CTkFrame):
    def __init__(self, master, root):
        super().__init__(master)
        self.configure(fg_color=color_bg_br, bg_color="transparent", corner_radius=10)
        self.gui = root

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self.traffic_widget = ctk.CTkFrame(self, fg_color=color_bg, bg_color="transparent", corner_radius=10)
        self.traffic_widget.grid(row=0, column=0, padx=(10, 5), pady=(10, 5), sticky="nsew")
        self.traffic_widget_header = Box(self.traffic_widget)
        self.traffic_widget_header.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 5))
        self.traffic_widget_header_title = HeaderTitle(self.traffic_widget_header, text="HTTP Traffic")
        self.traffic_widget_header_title.pack(side=tk.LEFT, padx=0, pady=0)
        if RUNNING_CONFIG["proxy_logging"]:
            def find_most_recent_traffic_log():
                import glob
                log_dir = traffic_logs_location
                log_files = glob.glob(os.path.join(log_dir, "traffic-*.log"))
                if not log_files:
                    ErrorDialog(self, self.gui, "Could not find any log files. Please check the logs folder for errors.")
                    return ""
                return max(log_files, key=os.path.getmtime)

            traffic_logs_location = Path(RUNNING_CONFIG['proxy_logs_location']) / "http_traffic"

            self.traffic_logs_folder_button = ActionButton(
                self.traffic_widget_header,
                text="Open logs folder",
                image=icon_folder,
                command=lambda: os.startfile(traffic_logs_location)
            )
            self.traffic_logs_button = ActionButton(
                self.traffic_widget_header,
                text="Open recent logs files",
                image=icon_load_file,
                command=lambda: os.startfile(find_most_recent_traffic_log())
            )
            self.traffic_logs_folder_button.pack(side=tk.RIGHT, anchor=tk.CENTER, padx=10, pady=0)
            self.traffic_logs_button.pack(side=tk.RIGHT, anchor=tk.CENTER, padx=10, pady=0)

            self.traffic_logs_textbox = TextBox(self.traffic_widget, text="")
            traffic_recent_log = find_most_recent_traffic_log()
            if len(traffic_recent_log) > 0:
                with open(traffic_recent_log, "r") as f:
                    self.traffic_logs_textbox.insert_text(f.read())
                    self.traffic_logs_textbox.configure(state=tk.DISABLED)
            self.traffic_logs_textbox.pack(side=tk.BOTTOM, expand=True, fill=tk.BOTH, anchor=tk.CENTER, padx=10, pady=(0, 10))
        else:
            self.traffic_widget_label = ctk.CTkLabel(self.traffic_widget, text="HTTP Traffic logs are currently turned off.\n"
                                                                               "Turn on proxy logging in the settings to have Intercepted requests logged to the file.")
            self.traffic_widget_label.pack(expand=True, anchor=tk.CENTER)

        self.intercept_widget = ctk.CTkFrame(self, fg_color=color_bg, bg_color="transparent", corner_radius=10)
        self.intercept_widget.grid(row=0, column=1, padx=(5, 10), pady=(10, 5), sticky="nsew")
        self.intercept_widget_header = Box(self.intercept_widget,)
        self.intercept_widget_header.pack(fill=tk.X, padx=10, pady=(10, 5))
        self.intercept_widget_header_title = HeaderTitle(self.intercept_widget_header, text="Web Interceptor")
        self.intercept_widget_header_title.pack(side=tk.LEFT, padx=0, pady=0)
        if RUNNING_CONFIG["proxy_logging"]:
            def find_most_recent_intercept_log():
                import glob
                log_dir = intercept_logs_location
                log_files = glob.glob(os.path.join(log_dir, "interceptor-*.log"))
                if not log_files:
                    ErrorDialog(self, self.gui, "Could not find any log files. Please check the logs folder for errors.")
                    return ""
                most_recent_log = max(log_files, key=os.path.getmtime)
                return most_recent_log

            intercept_logs_location = Path(RUNNING_CONFIG['proxy_logs_location']) / "web_interceptor"\

            self.intercept_logs_folder_button = ActionButton(
                self.intercept_widget_header,
                text="Open logs folder",
                image=icon_folder,
                command=lambda: os.startfile(intercept_logs_location)
            )
            self.intercept_logs_button = ActionButton(
                self.intercept_widget_header,
                text="Open recent logs files",
                image=icon_load_file,
                command=lambda: os.startfile(find_most_recent_intercept_log())
            )
            self.intercept_logs_folder_button.pack(side=tk.RIGHT, anchor=tk.CENTER, padx=10, pady=0)
            self.intercept_logs_button.pack(side=tk.RIGHT, anchor=tk.CENTER, padx=10, pady=0)

            self.intercept_logs_textbox = TextBox(self.intercept_widget, text="")
            intercept_recent_log = find_most_recent_intercept_log()
            if len(intercept_recent_log) > 0:
                with open(intercept_recent_log, "r") as f:
                    self.intercept_logs_textbox.insert_text(f.read())
                    self.intercept_logs_textbox.configure(state=tk.DISABLED)
            self.intercept_logs_textbox.pack(side=tk.BOTTOM, expand=True, fill=tk.BOTH, anchor=tk.CENTER, padx=10, pady=(0, 10))
        else:
            self.intercept_widget_label = ctk.CTkLabel(self.intercept_widget,
                                                       text="Web Interceptor logs are currently turned off.\n"
                                                            "Turn on proxy logging in the settings to have Intercepted requests logged to the file.")
            self.intercept_widget_label.pack(expand=True, anchor=tk.CENTER)

        self.repeater_widget = ctk.CTkFrame(self, fg_color=color_bg, bg_color="transparent", corner_radius=10)
        self.repeater_widget.grid(row=1, column=0, padx=(10, 5), pady=(5, 10), sticky="nsew")
        self.repeater_widget_header = HeaderTitle(self.repeater_widget, text="Repeater")
        self.repeater_widget_header.pack(fill=tk.X, padx=10, pady=10)
        self.repeater_widget_label = ctk.CTkLabel(self.repeater_widget, text="Logs from Repeater will be here.")
        self.repeater_widget_label.pack(expand=True, anchor=tk.CENTER)

        self.intruder_widget = ctk.CTkFrame(self, fg_color=color_bg, bg_color="transparent", corner_radius=10)
        self.intruder_widget.grid(row=1, column=1, padx=(5, 10), pady=(5, 10), sticky="nsew")
        self.intruder_widget_header = HeaderTitle(self.intruder_widget, text="Intruder")
        self.intruder_widget_header.pack(fill=tk.X, padx=10, pady=10)
        self.intruder_widget_label = ctk.CTkLabel(self.intruder_widget, text="Logs from Intruder will be here.")
        self.intruder_widget_label.pack(expand=True, anchor=tk.CENTER)

from common import *

# TODO FRONTEND P1: Logs/Reporting


def find_most_recent_log_file(log_dir: Path = Path(RUNNING_CONFIG['logs_location']), file_naming: str = "*.log") -> str:
    """
    Returns the most recent log file in the given directory.
    """
    import glob
    log_files = glob.glob(os.path.join(log_dir, file_naming))
    if not log_files:
        return ""
    return max(log_files, key=os.path.getmtime)


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

        traffic_logs_location = Path(RUNNING_CONFIG['logs_location']) / "http_traffic"

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
            command=lambda: os.startfile(find_most_recent_log_file(traffic_logs_location, "traffic-*.log"))
        )
        self.traffic_logs_folder_button.pack(side=tk.RIGHT, anchor=tk.CENTER, padx=10, pady=0)
        self.traffic_logs_button.pack(side=tk.RIGHT, anchor=tk.CENTER, padx=10, pady=0)

        self.traffic_logs_textbox = TextBox(self.traffic_widget, text="")
        traffic_recent_log = find_most_recent_log_file(traffic_logs_location, "traffic-*.log")
        if len(traffic_recent_log) > 0:
            with open(traffic_recent_log, "r") as f:
                self.traffic_logs_textbox.insert_text(f.read())
                self.traffic_logs_textbox.configure(state=tk.DISABLED)
        self.traffic_logs_textbox.pack(side=tk.BOTTOM, expand=True, fill=tk.BOTH, anchor=tk.CENTER, padx=10, pady=(0, 10))

        self.intercept_widget = ctk.CTkFrame(self, fg_color=color_bg, bg_color="transparent", corner_radius=10)
        self.intercept_widget.grid(row=0, column=1, padx=(5, 10), pady=(10, 5), sticky="nsew")
        self.intercept_widget_header = Box(self.intercept_widget,)
        self.intercept_widget_header.pack(fill=tk.X, padx=10, pady=(10, 5))
        self.intercept_widget_header_title = HeaderTitle(self.intercept_widget_header, text="Web Interceptor")
        self.intercept_widget_header_title.pack(side=tk.LEFT, padx=0, pady=0)

        interceptor_logs_location = Path(RUNNING_CONFIG['logs_location']) / "web_interceptor"\

        self.intercept_logs_folder_button = ActionButton(
            self.intercept_widget_header,
            text="Open logs folder",
            image=icon_folder,
            command=lambda: os.startfile(interceptor_logs_location)
        )
        self.intercept_logs_button = ActionButton(
            self.intercept_widget_header,
            text="Open recent logs files",
            image=icon_load_file,
            command=lambda: os.startfile(find_most_recent_log_file(interceptor_logs_location, "interceptor-*.log"))
        )
        self.intercept_logs_folder_button.pack(side=tk.RIGHT, anchor=tk.CENTER, padx=10, pady=0)
        self.intercept_logs_button.pack(side=tk.RIGHT, anchor=tk.CENTER, padx=10, pady=0)

        self.intercept_logs_textbox = TextBox(self.intercept_widget, text="")
        intercept_recent_log = find_most_recent_log_file(interceptor_logs_location, "interceptor-*.log")
        if len(intercept_recent_log) > 0:
            with open(intercept_recent_log, "r") as f:
                self.intercept_logs_textbox.insert_text(f.read())
                self.intercept_logs_textbox.configure(state=tk.DISABLED)
        self.intercept_logs_textbox.pack(side=tk.BOTTOM, expand=True, fill=tk.BOTH, anchor=tk.CENTER, padx=10, pady=(0, 10))

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

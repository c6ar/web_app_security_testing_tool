from frontend.common import *

logs_location = RUNNING_CONFIG.get("logs_location", "")
if not logs_location:
    app_dir = Path(__file__).resolve().parent.parent
    logs_location = app_dir / "logs"
else:
    logs_location = Path(logs_location)
logs_path = Path(logs_location)


class LogWidget(ctk.CTkFrame):
    """
    WASTT/Logs:
        Represents a widget for displaying and managing log files.

        This class provides a graphical user interface widget that manages log files
        for a specific purpose. It initializes with a title, allows loading the most
        recently updated log file from the specified directory, and provides buttons
        to open the logs directory or the most recent log file. It is designed to
        display the content of log files in a text box, marking it as read-only.
    """
    def __init__(self, master, title: str, logs_dir: str, file_naming: str):
        super().__init__(master)
        self.configure(fg_color=color_bg, bg_color="transparent", corner_radius=10)
        logs_path.mkdir(parents=True, exist_ok=True)
        self.logs_directory = Path(logs_path) / logs_dir
        self.file_naming = file_naming

        self.recent_log = self.find_most_recent_log_file()

        self.header = Box(self)
        self.header.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 5))
        self.header_title = HeaderTitle(self.header, text=title)
        self.header_title.pack(side=tk.LEFT, padx=0, pady=0)

        self.traffic_logs_folder_button = ActionButton(
            self.header,
            text="Open module logs folder",
            image=icon_folder,
            command=lambda: os.startfile(self.logs_directory)
        )
        self.traffic_logs_folder_button.pack(side=tk.RIGHT, anchor=tk.CENTER, padx=10, pady=0)
        if len(self.recent_log) > 0:
            self.traffic_logs_button = ActionButton(
                self.header,
                text="Open recent logs file",
                image=icon_load_file,
                command=lambda: os.startfile(self.recent_log)
            )
            self.traffic_logs_button.pack(side=tk.RIGHT, anchor=tk.CENTER, padx=10, pady=0)

        self.traffic_logs_textbox = TextBox(self, text="")
        if len(self.recent_log) > 0:
            with open(self.recent_log, "r") as f:
                self.traffic_logs_textbox.insert_text(f.read())
                self.traffic_logs_textbox.configure(state=tk.DISABLED)
        else:
            self.traffic_logs_textbox.insert_text("Log file empty.")
            self.traffic_logs_textbox.configure(state=tk.DISABLED)
        self.traffic_logs_textbox.pack(side=tk.BOTTOM, expand=True, fill=tk.BOTH, anchor=tk.CENTER, padx=10, pady=(0, 10))

    def find_most_recent_log_file(self) -> str:
        """
        Returns the most recent log file in the given directory.
        """
        import glob
        log_files = glob.glob(os.path.join(self.logs_directory, self.file_naming))
        if not log_files:
            return ""
        return max(log_files, key=os.path.getmtime)


class Logs(ctk.CTkFrame):
    """
    WASTT/Logs:
        A user interface component for managing and displaying log-related widgets.

        This class creates a logged-themed user interface frame composed of various widgets
        for viewing and accessing different categories of logs. The frame features sections
        for HTTP Traffic logs, Request Interceptor logs, Intruder logs, and Repeater logs.
        It includes buttons for opening a logs directory and accessing online log details,
        providing a clean and user-friendly design with advanced layout handling.
    """
    def __init__(self, master, root):
        super().__init__(master)
        self.configure(fg_color=color_bg_br, bg_color="transparent", corner_radius=10)
        self.wastt = root

        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self.traffic_widget = None
        self.intercept_widget = None
        self.intruder_widget = None
        self.repeater_widget = None

        top_bar = DarkBox(self)
        top_bar.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky=tk.EW)
        header_title = HeaderTitle(top_bar, text="Logs")
        header_title.pack(side=tk.LEFT, padx=5, pady=5)
        info_button = InfoButton(
            top_bar,
            self,
            "http://localhost:8080/logs.html"
        )
        info_button.pack(side=tk.RIGHT, padx=5, pady=0)

        logs_folder_button = ActionButton(
            top_bar,
            text="Open logs directory",
            image=icon_folder,
            command=lambda: os.startfile(logs_path)
        )
        logs_folder_button.pack(side=tk.RIGHT, padx=5, pady=0)

        self.draw_logs()

    def draw_logs(self) -> None:
        """
        Initializes and arranges the log widgets for displaying various logs
        in the interface. Each widget is configured with a specific title,
        logs directory, and file naming pattern, and is placed in the grid
        layout with appropriate padding and positioning.
        """
        self.traffic_widget = LogWidget(
            self,
            title="HTTP Traffic",
            logs_dir="http_traffic",
            file_naming="traffic-*.log"
        )
        self.traffic_widget.grid(row=1, column=0, padx=(10, 5), pady=5, sticky="nsew")

        self.intercept_widget = LogWidget(
            self,
            title="Request Interceptor",
            logs_dir="web_interceptor",
            file_naming="interceptor-*.log"
        )
        self.intercept_widget.grid(row=1, column=1, padx=(5, 10), pady=5, sticky="nsew")

        self.intruder_widget = LogWidget(
            self,
            title="Intruder",
            logs_dir="intruder",
            file_naming="intruder-*.log"
        )
        self.intruder_widget.grid(row=2, column=0, padx=(10, 5), pady=(5, 10), sticky="nsew")

        self.repeater_widget = LogWidget(
            self,
            title="Repeater",
            logs_dir="repeater",
            file_naming="repeater-*.log"
        )
        self.repeater_widget.grid(row=2, column=1, padx=(5, 10), pady=(5, 10), sticky="nsew")

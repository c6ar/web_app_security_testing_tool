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
        self.traffic_widget_header = HeaderTitle(self.traffic_widget, text="HTTP Traffic")
        self.traffic_widget_header.pack(fill=tk.X, padx=10, pady=10)
        self.traffic_widget_label = ctk.CTkLabel(self.traffic_widget, text="Logs from HTTP Traffics will be here.")
        self.traffic_widget_label.pack(expand=True, anchor=tk.CENTER)

        self.intercept_widget = ctk.CTkFrame(self, fg_color=color_bg, bg_color="transparent", corner_radius=10)
        self.intercept_widget.grid(row=0, column=1, padx=(5, 10), pady=(10, 5), sticky="nsew")
        self.intercept_widget_header = HeaderTitle(self.intercept_widget, text="Web Interceptor")
        self.intercept_widget_header.pack(fill=tk.X, padx=10, pady=10)
        self.intercept_widget_label = ctk.CTkLabel(self.intercept_widget, text="Logs from Web Interceptor will be here.")
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

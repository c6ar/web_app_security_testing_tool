# noinspection PyUnresolvedReferences
from common import *
from proxy import Proxy
from intruder import Intruder
from repeater import Repeater
from logs import Logs
from settings import Settings


class WASTT(ctk.CTk):
    """
    Class WASTT represents the main window of the Web App Security Testing Tool (WASTT).

    This class inherits from the ctk.CTk parent class and serves as the core interface of
    the application. It implements various functionalities for web application security
    testing, including multiple tabs for Proxy, Intruder, Repeater, and Logs modules. It also contains About and Settings windows for informational
    and configurational purposes. WASTT establishes a structured layout, initializes features,
    and necessary threads.
    """
    def __init__(self):
        super().__init__()
        self.title("WASTT | Web App Security Testing Tool")
        # TODO FRONTEND P2: Adding screen responsiveness to this app.
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.initial_width = int(screen_width * 0.9)
        self.initial_height = int(screen_height * 0.9)
        center_x = (screen_width // 2) - (self.initial_width // 2)
        self.iconbitmap(f"{ASSET_DIR}\\wastt.ico")
        self.geometry(f"{self.initial_width}x{self.initial_height}+{center_x}+10")
        self.configure(fg_color=color_bg, bg_color=color_bg)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.browser_opened = False
        self.browser = None
        self.stop_threads = False

        tab_nav = Box(self)
        tab_nav.pack(side=tk.TOP, fill=tk.X, padx=15, pady=(5, 0))

        about_button = NavButton(tab_nav, text="ABOUT", icon=icon_info, command=self.show_about)
        about_button.pack(side=tk.RIGHT)
        self.about_window = None

        settings_button = NavButton(tab_nav, text="SETTINGS", icon=icon_settings, command=self.show_settings)
        settings_button.pack(side=tk.RIGHT)
        self.settings_window = None

        tab_wrapper = Box(self)
        tab_wrapper.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # TODO P1: Adding HTML Documentation/About like in Settings
        self.proxy_tab = Proxy(tab_wrapper, self)
        self.intruder_tab = Intruder(tab_wrapper, self)
        self.repeater_tab = Repeater(tab_wrapper, self)
        self.logs_tab = Logs(tab_wrapper, self)

        self.tabs = {
            "Proxy": self.proxy_tab,
            "Intruder": self.intruder_tab,
            "Repeater": self.repeater_tab,
            "Logs": self.logs_tab
        }
        self.tab_nav_buttons = {}
        for name in self.tabs.keys():
            self.tab_nav_buttons[name] = NavButton(tab_nav, text=name.upper(), command=lambda t=name: self.show_tab(t))
            self.tab_nav_buttons[name].pack(side=tk.LEFT)

        self.http_server_thread = None
        self.start_http_server()

        self.show_tab("Proxy")
        print("[INFO] Starting the WASTT app.")

    def show_tab(self, tab_name) -> None:
        """
        Switches the visible tab in a WASTT's GUI.

        This method iterates through all available tabs and ensures that only the
        specified tab is displayed. It updates the visibility of each tab and the
        state of navigation buttons accordingly.

        Parameters:
            tab_name (str): The name of the tab to be displayed.
        """
        for name, tab in self.tabs.items():
            if name == tab_name:
                tab.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
                self.tab_nav_buttons[name].select(True)
            else:
                tab.pack_forget()
                self.tab_nav_buttons[name].select(False)

    def show_about(self) -> None:
        """
        Displays the "About WASTT" window of the application, providing information about the tool,
        its features, and authorship. Ensures that only one instance of the window is open at a time
        and properly manages the appearance and behavior of the window.
        """
        if self.about_window is None or not self.about_window.winfo_exists():
            self.about_window = ctk.CTkToplevel(self)
            self.about_window.title("About WASTT")
            self.about_window.resizable(False, False)
            self.about_window.transient(self)
            aw_width = 400
            aw_height = 475
            center_window(self, self.about_window, aw_width, aw_height)
            self.about_window.after(250, self.iconbitmap, f"{ASSET_DIR}\\wastt.ico", "")

            app_logo = ctk.CTkImage(light_image=Image.open(f"{ASSET_DIR}\\wastt.png"), dark_image=Image.open(f"{ASSET_DIR}\\wastt.png"),
                                    size=(150, 150))

            logo_label = ctk.CTkLabel(self.about_window, image=app_logo, text="")
            logo_label.pack(fill=tk.X, pady=(30, 15), padx=10)

            title = ctk.CTkLabel(self.about_window, text="WASTT", font=ctk.CTkFont(family="Calibri Light", size=24, weight="normal"), wraplength=350)
            title.pack(fill=tk.X, pady=(5, 0), padx=10)

            subtitle = ctk.CTkLabel(self.about_window, text="Web App Security Testing Tool", font=ctk.CTkFont(family="Calibri", size=18, weight="bold"), wraplength=250)
            subtitle.pack(fill=tk.X, pady=(0, 15), padx=10)

            desc = ctk.CTkLabel(self.about_window,
                                text="This tool includes handy features like a proxy for traffic interception, "
                                     "a repeater for custom request testing, an intruder for automated attacks, "
                                     "comprehensive logging and reporting, and fuzzing tests to identify potential security vulnerabilities. "
                                     "It's designed to help ensure web applications are secure.\n\n"
                                     "The tool was developed for a graduate project."
                                     "\n\nAuthors:\n Baran Cezary, Falisz Lukasz, Gargas Kacper\n\nUKEN © 2024",
                                font=ctk.CTkFont(family="Calibri", size=12, weight="normal"),
                                wraplength=350)
            desc.pack(fill=tk.X, pady=(5, 10), padx=10)

        if self.about_window.state() in ("withdrawn", "iconic", "icon"):
            self.about_window.deiconify()

        self.about_window.focus_force()

    def show_settings(self):
        """
        Displays the settings window if it is not already open. If the window
        exists but is minimized or hidden, it is brought to the foreground.
        """
        if self.settings_window is None:
            self.settings_window = Settings(self)
        self.settings_window.deiconify()
        self.settings_window.focus_set()

    def create_browser(self):
        """
        Creates a new Selenium Chrome/Edge/Firefox Browser instance with custom preset config.
        """
        from config import RUNNING_CONFIG
        dprint(f"[DEBUG] Creating {RUNNING_CONFIG['browser_type']} browser.")
        drivers_path = Path.cwd().parent / "webdrivers"

        from selenium import webdriver

        proxy_host = RUNNING_CONFIG["proxy_host_address"]
        proxy_port = RUNNING_CONFIG["proxy_port"]
        try:
            if RUNNING_CONFIG["browser_type"] == "edge":
                options = webdriver.EdgeOptions()
                if RUNNING_CONFIG["browser_disable_infobars"]:
                    options.add_argument("--disable-infobars")
                    options.add_argument("--disable-notifications")
                if RUNNING_CONFIG["browser_disable_cert_errors"]:
                    options.add_argument("--ignore-certificate-errors")
                options.add_argument(f"--proxy-server={proxy_host}:{proxy_port}")

                driver_path = os.path.join(drivers_path, "msedgedriver.exe")
                driver = webdriver.Edge(
                    service=webdriver.EdgeService(executable_path=driver_path),
                    options=options
                )

            elif RUNNING_CONFIG["browser_type"] == "firefox":
                options = webdriver.FirefoxOptions()
                if RUNNING_CONFIG["browser_disable_infobars"]:
                    options.set_preference("browser.chrome.favicons", False)
                    options.set_preference("dom.webnotifications.enabled", False)
                if RUNNING_CONFIG["browser_disable_cert_errors"]:
                    options.accept_untrusted_certs = True
                options.set_preference("network.proxy.type", 1)
                options.set_preference("network.proxy.http", proxy_host)
                options.set_preference("network.proxy.http_port", int(proxy_port))
                options.set_preference("network.proxy.ssl", proxy_host)
                options.set_preference("network.proxy.ssl_port", int(proxy_port))

                driver_path = os.path.join(drivers_path, "geckodriver.exe")
                driver = webdriver.Firefox(
                    service=webdriver.FirefoxService(executable_path=driver_path),
                    options=options
                )

            else:
                options = webdriver.ChromeOptions()
                if RUNNING_CONFIG["browser_disable_infobars"]:
                    options.add_argument("--disable-infobars")
                    options.add_argument("--disable-notifications")
                if RUNNING_CONFIG["browser_disable_cert_errors"]:
                    options.add_argument("--ignore-certificate-errors")
                options.add_argument(f"--proxy-server={proxy_host}:{proxy_port}")

                driver_path = os.path.join(drivers_path, "chromedriver.exe")
                driver = webdriver.Chrome(
                    service=webdriver.ChromeService(executable_path=driver_path),
                    options=options
                )

            return driver

        except Exception as e:
            ErrorDialog(
                self,
                self,
                "Error",
                f"Failed to create browser: {e}"
            )

    def start_browser_thread(self):
        """
        Starting thread of the open_browser() which opens Selenium Browser according to the app's running config.
        """
        def _open_browser():
            if self.browser is None:
                self.browser = self.create_browser()

            self.browser.get("https://www.example.com")

            try:
                while self.browser_opened and not self.stop_threads:
                    if len(self.browser.window_handles) == 0:
                        self.browser_opened = False
            finally:
                if self.browser is not None:
                    self.browser.quit()
                self.browser = None
                print("[INFO] Closing web browser.")

        if self.browser is None:
            self.browser_opened = True
            threading.Thread(target=_open_browser).start()
            print("[INFO] Opening web browser.")

    def start_http_server(self):
        """
        Starts an HTTP server in a separate thread, serving files from the http_docs folder.
        """
        def _run_http_server():
            try:
                http_files_dir = os.path.join(os.getcwd(), "http_docs")

                if not os.path.exists(http_files_dir):
                    os.makedirs(http_files_dir)

                # noinspection PyTypeChecker
                self.http_server = HTTPServer(
                    ('localhost', 8080),
                    lambda *args, **kwargs: SimpleHTTPRequestHandler(*args, directory=http_files_dir, **kwargs)
                )

                print(f"[HTTP SERVER] Serving files from: {http_files_dir}")
                print(f"[HTTP SERVER] You can access the server at: http://localhost:8080")
                self.http_server.serve_forever()
            except Exception as e:
                print(f"[HTTP SERVER ERROR] Error starting HTTP server: {e}")
        self.http_server_thread = threading.Thread(target=_run_http_server, daemon=True)
        self.http_server_thread.start()
        print("[INFO] Starting HTTP server.")

    def on_close(self):
        """
        Instructions run on GUI closure.
        """
        self.stop_threads = True

        # ================================================
        # STOPPING BROWSER
        # ================================================
        if self.browser is not None:
            self.browser.quit()

        # ================================================
        # STOPPING MITMDUMP PROXY PROCESS
        # ================================================
        if self.proxy_tab.process:
            try:
                self.proxy_tab.process.terminate()
                self.proxy_tab.process.wait()
                print("[INFO] Proxy process has been terminated succesfully.")
            except Exception as e:
                print(f"[ERROR] Proxy process termination failed: {e}")

        # ================================================
        # STOPPING HTTP SERVER
        # ================================================
        if hasattr(self, "http_server"):
            self.http_server.shutdown()
            self.http_server.server_close()
            print("[INFO] HTTP server stopped.")

        print("[INFO] Closing the WASTT app.")
        self.destroy()


wastt = WASTT()
wastt.mainloop()

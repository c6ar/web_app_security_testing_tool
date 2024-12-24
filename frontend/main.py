# noinspection PyUnresolvedReferences
from common import *
from settings import *
from proxy import *
from intruder import *
from repeater import *
from logs import *
from selenium import webdriver
# noinspection PyUnresolvedReferences
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options


class GUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("WASTT | Web App Security Testing Tool")
        # TODO FRONTEND P4: Adding screen responsiveness to this app.
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.initial_width = int(screen_width * 0.9)
        self.initial_height = int(screen_height * 0.9)
        center_x = (screen_width // 2) - (self.initial_width // 2)
        self.geometry(f"{self.initial_width}x{self.initial_height}+{center_x}+10")
        self.configure(fg_color=color_bg, bg_color=color_bg)
        self.iconbitmap(f"{ASSET_DIR}\\wastt.ico")

        self.browser_opened = False
        self.browser = None
        self.requests = None
        self.proxy_process = None
        self.stop_threads = False

        self.tab_nav = DarkBox(self)
        self.tab_nav.pack(side="top", fill="x", padx=15, pady=(5, 0))

        self.about_button = NavButton(self.tab_nav, text="ABOUT", icon=icon_info, command=self.show_about)
        self.about_button.pack(side="right")
        self.about_window = None

        self.settings_button = NavButton(self.tab_nav, text="SETTINGS", icon=icon_settings, command=self.show_settings)
        self.settings_button.pack(side="right")
        self.settings_window = None

        self.tab_content = Box(self)
        self.tab_content.pack(side="top", fill="both", expand=True)

        self.proxy_tab = GUIProxy(self.tab_content, self)
        self.intruder_tab = GUIIntruder(self.tab_content, self)
        self.repeater_tab = GUIRepeater(self.tab_content, self)
        self.logs_tab = GUILogs(self.tab_content, self)

        self.tabs = {
            "Proxy": self.proxy_tab,
            "Intruder": self.intruder_tab,
            "Repeater": self.repeater_tab,
            "Logs": self.logs_tab
        }
        self.tab_nav_buttons = {}
        for name in self.tabs.keys():
            self.tab_nav_buttons[name] = NavButton(self.tab_nav, text=name.upper(), command=lambda t=name: self.show_tab(t))
            self.tab_nav_buttons[name].pack(side=tk.LEFT)

        self.show_tab("Proxy")
        print("[INFO] Starting the WASTT app.")

    def show_tab(self, tab_name):
        for name, tab in self.tabs.items():
            if name == tab_name:
                tab.pack(side="top", fill="both", expand=True)
                self.tab_nav_buttons[name].set_selected(True)
            else:
                tab.pack_forget()
                self.tab_nav_buttons[name].set_selected(False)

    def show_about(self):
        if self.about_window is None or not self.about_window.winfo_exists():
            self.about_window = ctk.CTkToplevel(self)
            self.about_window.title("About WASTT")
            aw_width = 400
            aw_height = 475
            self.about_window.geometry(f"{aw_width}x{aw_height}")
            self.about_window.resizable(False, False)
            self.about_window.transient(self)
            self.about_window.iconbitmap(f"{ASSET_DIR}\\wastt.png")

            center_window(self, self.about_window, aw_width, aw_height)
            self.about_window.focus_set()

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
        if self.settings_window is None:
            self.settings_window = Settings(self)
            self.settings_window.focus_set()
        self.settings_window.deiconify()
        self.settings_window.focus_set()

    def open_browser(self):
        """
        Opening Selenium Chrome Browser with custom preset config.
        """
        options = Options()
        options.add_argument("--enable-logging")
        options.add_argument("--log-level=0")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-notifications")
        proxy_host = RUNNING_CONFIG["proxy_host_address"]
        proxy_port = RUNNING_CONFIG["proxy_port"]
        options.add_argument(f"--proxy-server={proxy_host}:{proxy_port}")
        options.add_argument("--ignore-certificate-errors")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        self.browser = webdriver.Chrome(options=options)
        self.browser.get("https://www.example.com")

        time.sleep(2)

        user32 = ctypes.windll.user32
        user32.ShowWindow(user32.GetForegroundWindow(), 5)
        user32.SetForegroundWindow(user32.GetForegroundWindow())

        try:
            while self.browser_opened and not self.stop_threads:
                # self.requests = driver.get_log('performance')
                if len(self.browser.window_handles) == 0:
                    self.browser_opened = False
        finally:
            if self.browser is not None:
                self.browser.quit()
            self.browser = None
            print("[INFO] Closing web browser.")

    def start_browser_thread(self):
        """
        Starting thread of the GUI.open_browser().
        """
        if self.browser is None:
            self.browser_opened = True
            threading.Thread(target=self.open_browser).start()
            print("[INFO] Opening web browser.")

        elif self.browser and self.browser_opened:
            user32 = ctypes.windll.user32
            user32.ShowWindow(user32.GetForegroundWindow(), 5)
            user32.SetForegroundWindow(user32.GetForegroundWindow())

    def stop_proxy(self):
        """
        Switch WASTT GUI to the Repeater tab.
        """
        if self.proxy_tab.process:
            try:
                self.proxy_tab.process.terminate()
                self.proxy_tab.process.wait()
                print("[INFO] Proxy process has been terminated succesfully.")
            except Exception as e:
                print(f"[ERROR] Proxy process termination failed: {e}")

    def on_close(self):
        """
        Instructions run on GUI closure.
        """
        self.stop_threads = True
        if self.browser is not None:
            self.browser.quit()
        self.stop_proxy()
        self.destroy()
        print("[INFO] Closing the WASTT app.")


wastt = GUI()
wastt.protocol("WM_DELETE_WINDOW", wastt.on_close)
wastt.mainloop()

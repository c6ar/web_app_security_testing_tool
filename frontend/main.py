# noinspection PyUnresolvedReferences
from common import *
from proxy import *
from intruder import *
from repeater import *
from logs import *
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# TODO FRONTEND: Add theme support, after settings implemented.
# TODO FRONTEND: Add lang support only EN and PL.


def load_config():
    # TODO OTHER: Actual implmentation of config logic in the app, probably moving to main.py or separate file.
    default_config = {
        "host_address": "127.0.0.1",
        "port": 8082
    }
    config = default_config.copy()
    try:
        with open("app.conf", "r") as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    if "#" in value:
                        value, _ = value.split("#", 1)
                    config[key.strip()] = value.strip()
    except FileNotFoundError:
        print("App config file could not be open. Default settings loaded.")
    return config


def save_config(config):
    try:
        with open("app.conf", "r") as file:
            lines = file.readlines()

        updated_lines = []
        keys_found = set()
        for line in lines:
            if line.strip() and not line.strip().startswith("#"):
                key, value = line.split("=", 1)
                key = key.strip()
                if key in config:
                    updated_lines.append(f"{key} = {config[key]}\n")
                    keys_found.add(key)
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)

        for key, value in config.items():
            if key not in keys_found:
                updated_lines.append(f"{key} = {value}\n")

        with open("app.conf", "w") as file:
            file.writelines(updated_lines)
            load_config()
    except Exception as e:
        print(f"Error during saving a config: {e}")


class GUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("WASTT | Web App Security Testing Tool")
        self.initial_width = 1200
        self.initial_height = 900
        self.geometry(f"{self.initial_width}x{self.initial_height}+10+20")
        self.configure(fg_color=color_bg, bg_color=color_bg)
        self.iconbitmap(f"{ASSET_DIR}\\wastt.ico")

        self.running_conf = load_config()
        self.browser_opened = False
        self.browser = None
        self.requests = None
        self.proxy_process = None
        self.intercepting = False

        self.tab_nav = ctk.CTkFrame(self, fg_color=color_bg, bg_color=color_bg)
        self.tab_nav.pack(side="top", fill="x", padx=10, pady=(5, 0))

        self.about_button = NavButton(self.tab_nav, text="ABOUT", icon=icon_info, command=self.show_about)
        self.about_button.pack(side="right")
        self.about_window = None

        self.settings_button = NavButton(self.tab_nav, text="SETTINGS", icon=icon_settings, command=self.show_settings)
        self.settings_button.pack(side="right")
        self.settings_window = None
        self.settings_entries = {}

        self.tab_content = ctk.CTkFrame(self, fg_color=color_bg_br, bg_color=color_bg_br)
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
            self.about_window.iconbitmap(f"{ASSET_DIR}\\wastt.ico")
            self.about_window.attributes("-topmost", True)

            center_window(self, self.about_window, aw_width, aw_height)

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

    def show_settings(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            # TODO OTHER: Actual implmentation of config logic in the app, probably moving to main.py or separate file.
            # Settings ideas, appearance (theme), language (EN or PL), Proxy rerun, show Proxy log, turn on Debug mode for the app DEBUG PRINTOUTS
            self.settings_window = ctk.CTkToplevel(self)
            self.settings_window.title("Proxy Settings")
            self.settings_window.attributes("-topmost", True)
            center_window(self, self.settings_window, 500, 650)
            self.settings_window.configure()

            wrapper = ctk.CTkScrollableFrame(self.settings_window, fg_color=color_bg_br, bg_color="transparent")
            wrapper.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

            for key, value in self.running_conf.items():
                frame = ctk.CTkFrame(wrapper, fg_color=color_bg, bg_color="transparent")
                frame.pack(fill=tk.X, padx=10, pady=(10, 5))
                label = ctk.CTkLabel(frame, text=key, width=100)
                label.pack(side=tk.LEFT, padx=10, pady=10)
                entry = TextEntry(frame, width=250)
                entry.insert(0, value)
                entry.pack(side=tk.RIGHT, padx=10, pady=10)
                self.settings_entries[key] = entry

            bottom_bar = ctk.CTkFrame(self.settings_window, fg_color=color_bg_br, bg_color="transparent")
            bottom_bar.pack(fill=tk.X, padx=0, pady=0)

            save_button = ctk.CTkButton(bottom_bar, text="Save", command=self.save_settings, fg_color=color_acc3,
                                        hover_color=color_acc4, corner_radius=32)
            save_button.pack(side=tk.LEFT, padx=10, pady=10)

            cancel_button = ctk.CTkButton(bottom_bar, text="Cancel", command=self.settings_window.destroy,
                                          corner_radius=32)
            cancel_button.pack(side=tk.RIGHT, padx=10, pady=10)

    def save_settings(self):
        # TODO OTHER: Actual implmentation of config logic in the app, probably moving to main.py or separate file.
        for key, entry in self.settings_entries.items():
            self.running_conf[key] = entry.get()
        save_config(self.running_conf)
        self.settings_window.destroy()

    def open_browser(self):
        """
        Opening Selenium Chrome Browser with custom preset config.
        """
        options = Options()
        options.add_argument("--enable-logging")
        options.add_argument("--log-level=0")
        # TODO OTHER: Get certificates stuff working so we can access https with proxy, perhaps from BURP?
        options.add_argument(f"--proxy-server=localhost:8082")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-notifications")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        self.browser = webdriver.Chrome(options=options)
        self.browser.get("http://www.example.com")

        try:
            while self.browser_opened:
                # self.requests = driver.get_log('performance')
                if len(self.browser.window_handles) == 0:
                    self.browser_opened = False
        finally:
            self.proxy_tab.browser_button_update()
            print("Closing Browser Window")
            self.browser.quit()
            self.browser = None

    def start_browser_thread(self):
        """
        Starting thread of the GUI.open_browser().
        """
        if self.browser is None:
            print("Opening Browser Window")
            self.browser_opened = True
            browser_thread = threading.Thread(target=self.open_browser)
            browser_thread.start()
            self.proxy_tab.browser_button_update()
        else:
            try:
                self.browser.switch_to.window(self.browser.current_window_handle)
                self.proxy_tab.browser_button_update()
            except Exception as e:
                print(f"Exception occured: {e}")
                self.browser = None
                self.browser_opened = False
                time.sleep(1)
                self.start_browser_thread()

    def stop_proxy(self):
        """
        Switch WASTT GUI to the Repeater tab.
        """
        if self.proxy_tab.process:
            try:
                self.proxy_tab.process.terminate()
                # self.proxy_frame.process.wait()
                print("Proxy process has been terminated succesfully.")
            except Exception as e:
                print(f"Error while terminating proxy process: {e}")

    def on_close(self):
        # TODO OTHER: Synching of threads(?) - closing app seems clunky.
        """
        Instructions run on GUI closure.
        """
        self.stop_proxy()
        if self.browser is not None:
            self.browser.quit()
        self.destroy()


wastt = GUI()
wastt.protocol("WM_DELETE_WINDOW", wastt.on_close)
wastt.mainloop()

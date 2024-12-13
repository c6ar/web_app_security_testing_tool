from common import *
from proxy import *
from intruder import *
from repeater import *
from logs import *
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# TODO FRONTEND: Add theme support, after settings implemented.
# TODO FRONTEND: Add lang support only EN and PL.
ctk.set_appearance_mode("system")
ctk.set_default_color_theme("dark-blue")


class GUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("WASTT | Web App Security Testing Tool")
        self.initial_width = 1200
        self.initial_height = 900
        self.geometry(f"{self.initial_width}x{self.initial_height}+10+20")
        self.configure(fg_color=color_bg, bg_color=color_bg)
        self.iconbitmap(f"{ASSET_DIR}\\wast_4x.ico")
        self.main_nav = ctk.CTkFrame(self, bg_color=color_bg, fg_color=color_bg)
        self.main_nav.pack(side="top", fill="x", padx=10, pady=(10, 0))

        buttons_set = {
            "Proxy": self.show_proxy,
            "Intruder": self.show_intruder,
            "Repeater": self.show_repeater,
            "Logs": self.show_logs
        }

        self.navbuttons = {}

        for name, command in buttons_set.items():
            self.navbuttons[name] = NavButton(self.main_nav, text=name.upper(), command=command)
            self.navbuttons[name].pack(side="left")

        self.about_button = NavButton(self.main_nav, text="ABOUT", icon=icon_info, command=self.show_about)
        self.about_button.pack(side="right")
        self.about = None

        self.settings_button = NavButton(self.main_nav, text="SETTINGS", icon=icon_settings, command=self.show_settings)
        self.settings_button.pack(side="right")
        self.settings_window = None
        self.settings_entries = {}
        self.running_conf = self.load_config()

        self.content_wrapper = ctk.CTkFrame(self, fg_color=color_bg_br, bg_color=color_bg_br)
        self.content_wrapper.pack(side="top", fill="both", expand=True)

        self.browser_opened = False
        self.browser = None
        self.intercepting = False
        self.requests = None
        self.proxy_process = None

        self.proxy_frame = GUIProxy(self.content_wrapper, self)
        self.intruder_frame = GUIIntruder(self.content_wrapper, self)
        self.repeater_frame = GUIRepeater(self.content_wrapper, self)
        self.logs_frame = GUILogs(self.content_wrapper, self)

        self.show_proxy()

    def show_about(self):
        # TODO FRONTEND: Add proper description on the app.
        self.about = ctk.CTkToplevel(self)
        self.about.title("About WASTT")
        self.about.geometry("300x350")
        self.about.attributes("-topmost", True)

        app_logo = ctk.CTkImage(light_image=Image.open(f"{ASSET_DIR}\\wast@4x.png"), dark_image=Image.open(f"{ASSET_DIR}\\wast@4x.png"),
                                size=(100, 100))

        logo_label = ctk.CTkLabel(self.about, image=app_logo, text="")
        logo_label.pack(pady=(30, 15), padx=10)

        title = ctk.CTkLabel(self.about, text="WASTT", font=ctk.CTkFont(family="Calibri Light", size=24, weight="normal"), wraplength=250)
        title.pack(pady=(5, 0), padx=10)

        subtitle = ctk.CTkLabel(self.about, text="Web App Security Testing Tool", font=ctk.CTkFont(family="Calibri", size=18, weight="bold"), wraplength=250)
        subtitle.pack(pady=(0, 15), padx=10)

        desc = ctk.CTkLabel(self.about,
                            text="App Short Description.\nLorem Ipsum.\n\nAuthors:\n Baran Cezary, Falisz Lukasz, Gargas Kacper\n\nUKEN © 2024",
                            font=ctk.CTkFont(family="Calibri", size=12, weight="normal"),
                            wraplength=250)
        desc.pack(pady=(5, 10), padx=10)

    def show_proxy(self):
        """
        Switch WASTT GUI to the Proxy tab.
        """
        self.clear_content_frame()
        self.proxy_frame.pack(side="top", fill="both", expand=True)
        self.select_button(self.navbuttons["Proxy"])

    def show_intruder(self):
        """
        Switch WASTT GUI to the Intruder tab.
        """
        self.clear_content_frame()
        self.intruder_frame.pack(side="top", fill="both", expand=True)
        self.select_button(self.navbuttons["Intruder"])

    def show_repeater(self):
        """
        Switch WASTT GUI to the Repeater tab.
        """
        self.clear_content_frame()
        self.repeater_frame.pack(side="top", fill="both", expand=True)
        self.select_button(self.navbuttons["Repeater"])

    def show_logs(self):
        """
        Switch WASTT GUI to the Logs tab.
        """
        self.clear_content_frame()
        self.logs_frame.pack(side="top", fill="both", expand=True)
        self.select_button(self.navbuttons["Logs"])

    def clear_content_frame(self):
        """
        Clearing WASTT content wrapper before rendering another tab - while switching them.
        """
        for widget in self.content_wrapper.winfo_children():
            widget.pack_forget()

    def select_button(self, selected_button):
        """
        Selecting main nav button when clicked.
        """
        for button in self.navbuttons.values():
            if button == selected_button:
                button.set_selected(True)
            else:
                button.set_selected(False)

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
            self.proxy_frame.browser_button_update()
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
            self.proxy_frame.browser_button_update()
        else:
            try:
                self.browser.switch_to.window(self.browser.current_window_handle)
                self.proxy_frame.browser_button_update()
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
        if self.proxy_frame.process:
            try:
                self.proxy_frame.process.terminate()
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

    def show_settings(self):
        # TODO OTHER: Actual implmentation of config logic in the app, probably moving to main.py or separate file.
        self.settings_window = ctk.CTkToplevel(self)
        self.settings_window.title("Proxy Settings")
        self.settings_window.attributes("-topmost", True)

        for key, value in self.running_conf.items():
            label = ctk.CTkLabel(self.settings_window, text=key)
            label.pack()
            entry = ctk.CTkEntry(self.settings_window)
            entry.insert(0, value)
            entry.pack()
            self.settings_entries[key] = entry

        save_button = ctk.CTkButton(self.settings_window, text="Save", command=self.save_settings, fg_color=color_acc3,
                                    hover_color=color_acc4, corner_radius=32)
        save_button.pack(side=tk.LEFT, padx=10, pady=10)

        cancel_button = ctk.CTkButton(self.settings_window, text="Cancel", command=self.settings_window.destroy,
                                      corner_radius=32)
        cancel_button.pack(side=tk.RIGHT, padx=10, pady=10)

        self.settings_window.lift()

    def save_settings(self):
        for key, entry in self.settings_entries.items():
            self.running_conf[key] = entry.get()
        self.save_config(self.running_conf)
        self.settings_window.destroy()

    def load_config(self):
        # TODO FRONTEND: Rework this method for the general instead of proxy.
        default_config = {
            "host_address": "127.0.0.1",
            "port": 8082
        }
        config = default_config.copy()
        try:
            with open("proxy.conf", "r") as file:
                for line in file:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        config[key.strip()] = value.strip()
        except FileNotFoundError:
            print("Proxy config file could not be open. Default settings loaded.")
        return config

    def save_config(self, config):
        try:
            with open("proxy.conf", "r") as file:
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

            with open("proxy.conf", "w") as file:
                file.writelines(updated_lines)
                self.load_config()
        except Exception as e:
            print(f"Error during saving a config: {e}")


wastt = GUI()
wastt.protocol("WM_DELETE_WINDOW", wastt.on_close)
wastt.mainloop()

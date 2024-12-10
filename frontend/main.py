import ctypes
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller

from head import *
from proxy import *
from intruder import *
from repeater import *
from logs import *

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
        self.mainnav = ctk.CTkFrame(self, bg_color=color_bg, fg_color=color_bg)
        self.mainnav.pack(side="top", fill="x", padx=10, pady=(10,0))

        buttons_set = {
            "Proxy": self.show_proxy,
            "Intruder": self.show_intruder,
            "Repeater": self.show_repeater,
            "Logs": self.show_logs
        }

        self.navbuttons = {}

        for name, command in buttons_set.items():
            self.navbuttons[name] = NavButton(self.mainnav, text=name.upper(), command=command,
                                              font=ctk.CTkFont(family="Calibri", size=15, weight="bold"))
            self.navbuttons[name].pack(side="left")

        self.about_button = NavButton(self.mainnav, text="ABOUT", command=self.about, font=ctk.CTkFont(family="Calibri", size=15, weight="bold"))
        self.about_button.pack(side="right")

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

    def about(self):
        print("About clicked.")

    def show_proxy(self):
        self.clear_content_frame()
        self.proxy_frame.pack(side="top", fill="both", expand=True)
        self.select_button(self.navbuttons["Proxy"])

    def show_intruder(self):
        self.clear_content_frame()
        self.intruder_frame.pack(side="top", fill="both", expand=True)
        self.select_button(self.navbuttons["Intruder"])

    def show_repeater(self):
        self.clear_content_frame()
        self.repeater_frame.pack(side="top", fill="both", expand=True)
        self.select_button(self.navbuttons["Repeater"])

    def show_logs(self):
        self.clear_content_frame()
        self.logs_frame.pack(side="top", fill="both", expand=True)
        self.select_button(self.navbuttons["Logs"])

    def clear_content_frame(self):
        for widget in self.content_wrapper.winfo_children():
            widget.pack_forget()

    def select_button(self, selected_button):
        for button in self.navbuttons.values():
            if button == selected_button:
                button.set_selected(True)
            else:
                button.set_selected(False)

    def open_browser(self):
        options = Options()
        options.add_argument("--enable-logging")
        options.add_argument("--log-level=0")
        options.add_argument(f"--proxy-server=localhost:8082")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-notifications")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        self.browser = webdriver.Chrome(options=options)
        self.browser.get("about://newtab")

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
        Starting thread of the browser.
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
        """Zatrzymanie procesu proxy"""
        if self.proxy_frame.process:
            try:
                # Użycie terminate() do zakończenia procesu
                self.proxy_frame.process.terminate()  # Wysyła sygnał zakończenia
                # self.proxy_frame.process.wait()  # Czeka na zakończenie procesu
                print("Proces proxy został zatrzymany.")
            except Exception as e:
                print(f"Błąd przy zatrzymywaniu procesu: {e}")

    def on_close(self):
        """Zamykanie aplikacji"""
        self.stop_proxy()
        if self.browser is not None:
            self.browser.quit()
        self.destroy()


wastt = GUI()
wastt.protocol("WM_DELETE_WINDOW", wastt.on_close)
wastt.mainloop()

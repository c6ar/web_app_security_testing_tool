from head import *
from dashboard import *
from proxy import *
from target import *
from intruder import *
from repeater import *
from logs import *

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("dark-blue")


class GUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Security Testing App")
        # self.geometry("1880x900+10+20")
        self.geometry("1200x600+10+20")
        self.configure(fg_color=color_bg, bg_color=color_bg)

        self.mainnav = ctk.CTkFrame(self, bg_color=color_bg, fg_color=color_bg)
        self.mainnav.pack(side="top", fill="x", padx=0, pady=0)

        buttons_set = {
            "Dashboard": self.show_dashboard,
            "Target": self.show_target,
            "Proxy": self.show_proxy,
            "Intruder": self.show_intruder,
            "Repeater": self.show_repeater,
            "Logs": self.show_logs
        }

        self.navbuttons = {}

        for name, command in buttons_set.items():
            self.navbuttons[name] = NavButton(self.mainnav, text=name, command=command,
                                              font=ctk.CTkFont(family="Calibri", size=15, weight="bold"))
            self.navbuttons[name].pack(side="left")

        self.content_wrapper = ctk.CTkFrame(self, fg_color=color_bg_br, bg_color=color_bg_br)
        self.content_wrapper.pack(side="top", fill="both", expand=True)

        self.browser_opened = False
        self.browser = None
        self.intercepting = False
        self.requests = None
        self.proxy_process = None

        self.dashboard_frame = GUIDash(self.content_wrapper, self)
        self.target_frame = GUITarget(self.content_wrapper, self)
        self.proxy_frame = GUIProxy(self.content_wrapper, self)
        self.intruder_frame = GUIIntruder(self.content_wrapper, self)
        self.repeater_frame = GUIRepeater(self.content_wrapper, self)
        self.logs_frame = GUILogs(self.content_wrapper, self)

        self.show_proxy()

    def show_dashboard(self):
        self.clear_content_frame()
        self.dashboard_frame.pack(side="top", fill="both", expand=True)
        self.select_button(self.navbuttons["Dashboard"])

    def show_target(self):
        self.clear_content_frame()
        self.target_frame.pack(side="top", fill="both", expand=True)
        self.select_button(self.navbuttons["Target"])

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
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        driver = webdriver.Chrome(service=Service(), options=options)
        self.browser = driver
        driver.get("http://www.example.com")

        try:
            while self.browser_opened:
                self.requests = driver.get_log('performance')
                self.proxy_frame.Cs_update()
                if len(driver.window_handles) == 0:
                    self.browser_opened = False
        finally:
            self.proxy_frame.browser_button_update()
            print("Closing Browser Window")
            driver.quit()
            self.browser = None

    def start_browser_thread(self):
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
                self.proxy_frame.process.wait()  # Czeka na zakończenie procesu
                print("Proces proxy został zatrzymany.")
            except Exception as e:
                print(f"Błąd przy zatrzymywaniu procesu: {e}")

    def on_close(self):
        """Zamykanie aplikacji"""
        self.stop_proxy()
        app.destroy()  # Zamknięcie głównego okna aplikacji


app = GUI()
app.protocol("WM_DELETE_WINDOW", app.on_close)
app.mainloop()

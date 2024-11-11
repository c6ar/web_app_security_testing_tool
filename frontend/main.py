from head import *
from dashboard import *
from proxy import *
from target import *
from intruder import *
from repeater import *
from logs import *


class GUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Security Testing App")
        self.geometry("1880x900+10+20")
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

        self.intercepting = False

        self.dashboard_frame = GUIDash(self.content_wrapper, self)
        self.target_frame = GUITarget(self.content_wrapper, self)
        self.proxy_frame = GUIProxy(self.content_wrapper, self)
        self.intruder_frame = GUIIntruder(self.content_wrapper, self)
        self.repeater_frame = GUIRepeater(self.content_wrapper, self)
        self.logs_frame = GUILogs(self.content_wrapper, self)

        self.show_target()

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


app = GUI()
app.mainloop()

from common import *


class RepeaterTab(ctk.CTkFrame):
    """
    WASTT/Repeater/Tab:
        RepeaterTab provides a graphical user interface widget for crafting and sending
        HTTP requests, viewing responses, and managing iterations.

        This class is designed for users to create, send, and log HTTP requests.
        Users can enter a request manually or auto-generate one, and responses are displayed
        in a dedicated text box. It includes features for logging requests and responses
        to files, dynamically updating dropdown menus for iterations,
        and loading previous iterations based on selection.
    """
    def __init__(self, master, id_number=0, content=None, hosturl=None):
        super().__init__(master)
        self.hosturl = hosturl
        self.configure(
            fg_color=color_bg,
            corner_radius=10,
            background_corner_colors=(color_bg_br, color_bg_br, color_bg_br, color_bg_br)
        )
        self.repeater = master
        self.wastt = master.wastt
        self.id = id_number
        self.is_empty = True

        logs_location = RUNNING_CONFIG.get("logs_location", "")
        if not logs_location:
            app_dir = Path(__file__).resolve().parent.parent
            logs_location = app_dir / "logs"
        logs_path = Path(logs_location / "repeater")
        logs_path.mkdir(parents=True, exist_ok=True)
        self.log_file = logs_path / f"repeater-{today}.log"

        # ================================================
        # Top Bar
        # ================================================
        top_bar = Box(self)
        top_bar.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky=tk.EW)

        hosturl_label = Label(top_bar, text="Host URL")
        hosturl_label.pack(padx=10, pady=10, side=tk.LEFT)

        self.hosturl_entry = TextEntry(top_bar, width=350)
        if self.hosturl is not None:
            self.hosturl_entry.insert(0, self.hosturl)
        self.hosturl_entry.pack(padx=(0, 10), pady=10, side=tk.LEFT)
        self.hosturl_entry.bind("<KeyRelease>", self.on_request_textbox_change)

        self.send_button = ActionButton(
            top_bar,
            text="Send",
            image=icon_arrow_up,
            command=self.send_request_from_repeater,
            state=tk.DISABLED
        )
        self.send_button.pack(padx=10, pady=10, side=tk.LEFT)

        self.tab_iterations = {}
        self.tab_iteration_keys = []

        self.iteration_var = tk.StringVar(top_bar)
        self.iteration_var.set("Select Iteration")

        self.iteration_dropdown = ctk.CTkOptionMenu(
            top_bar,
            variable=self.iteration_var,
            values=[],
            command=self.select_iteration,
            state=tk.DISABLED,
            width=200
        )
        self.iteration_dropdown.pack(side=tk.LEFT, padx=5, pady=10)

        info_button = InfoButton(
            top_bar,
            self,
            "http://localhost:8080/repeater.html"
        )
        info_button.pack(side=tk.RIGHT, padx=5, pady=0)

        gen_button = ActionButton(
            top_bar,
            text="Generate a request",
            image=icon_random,
            command=self.generate_request,
        )
        if RUNNING_CONFIG["debug_mode"]:
            gen_button.pack(padx=10, pady=10, side=tk.RIGHT)

        if self.id != 0:
            self.delete_tab_button = ActionButton(
                top_bar,
                text="Delete the card",
                image=icon_delete,
                command=lambda: self.repeater.delete_tab(self.id),
            )
            self.delete_tab_button.pack(padx=10, pady=10, side=tk.RIGHT)

        # ================================================
        # Request and response boxes
        # ================================================
        request_header = HeaderTitle(self, text="Request")
        request_header.grid(row=1, column=0, padx=10, pady=(5, 0), sticky=tk.W)

        self.request_textbox = TextBox(self, text="Enter request here.")
        self.request_textbox.configure(font=self.request_textbox.monoscape_font_italic)
        self.request_textbox.grid(row=2, column=0, padx=(20, 10), pady=(0, 20), sticky=tk.NSEW)
        if content is not None:
            self.request_textbox.insert_text(content)
            self.is_empty = False
        self.request_textbox.bind("<<Modified>>", self.on_request_textbox_change)

        response_header = Box(self)
        response_header.grid(row=1, column=1, padx=(10, 20), pady=(5, 0), sticky=tk.EW)

        response_header_title = HeaderTitle(response_header, text="Response")
        response_header_title.pack(side=tk.LEFT, padx=0, pady=0)

        self.response_textbox = TextBox(self, text="Response will appear here.")
        self.response_textbox.configure(state=tk.DISABLED, font=self.response_textbox.monoscape_font_italic)
        self.response_textbox.grid(row=2, column=1, padx=(10, 20), pady=(0, 20), sticky=tk.NSEW)

        self.response_render_button = ActionButton(
            response_header,
            text="Show response render",
            command=lambda: show_response_view(self.repeater, self.hosturl_entry.get(), self.response_textbox.get_text()),
            state=tk.DISABLED
        )
        self.response_render_button.pack(side=tk.RIGHT, padx=0, pady=0)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

    def update_number(self, id_number: int) -> None:
        """
        WASTT/Repeater/Tab:
            Updates the id number of the instance and configures the delete button command
            to delete the tab associated with the updated id.

            Parameters:
            id_number: int - The new id number to be assigned to the instance.
        """
        self.id = id_number
        if self.id != 0:
            self.delete_tab_button.configure(
                command=lambda: self.repeater.delete_tab(self.id)
            )

    def on_request_textbox_change(self, _event) -> None:
        """
        WASTT/Repeater/Tab:
            Updates the state and appearance of the request textbox, send button, and related
            flags in response to changes in the request textbox content.
        """
        self.request_textbox.edit_modified(False)
        if len(self.request_textbox.get_text()) > 0 and self.request_textbox.get_text() != "Enter request here.":
            self.is_empty = False
            self.request_textbox.configure(font=self.request_textbox.monoscape_font)
            if len(self.hosturl_entry.get()) > 0:
                self.send_button.configure(state=tk.NORMAL)
            else:
                self.send_button.configure(state=tk.DISABLED)
        else:
            self.is_empty = True
            self.request_textbox.configure(font=self.request_textbox.monoscape_font_italic)
            self.send_button.configure(state=tk.DISABLED)

    def send_request_from_repeater(self) -> None:
        """
        WASTT/Repeater/Tab:
            Sends an HTTP request from the repeater tab, processes the response, logs the request and response,
            and updates the repeater tab interface with the new data.
        """
        request_text = self.request_textbox.get_text()
        request_host = self.hosturl_entry.get()
        if len(request_text) > 0:
            if len(request_host) > 0:
                try:
                    response = send_http_message(request_host, request_text)
                    response_text = process_response(response)
                    self.add_response_to_repeater_tab(response_text)

                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    with open(self.log_file, "a", encoding="utf-8", errors="replace") as file:
                        file.write(f"\n[{timestamp}] Request to {request_host}:\n{request_text}")
                        file.write(f"\n[{timestamp}] Response from {request_host}:\n{response_text}")

                    self.tab_iterations[timestamp] = [request_text, response_text]
                    self.tab_iteration_keys.insert(0, timestamp)
                    self.update_dropdown_menu()
                except Exception as e:
                    ErrorDialog(self, self.wastt, e)
            else:
                ErrorDialog(self, self.wastt, "Host URL is empty.")
        else:
            ErrorDialog(self, self.wastt, "Request is empty.")

    def add_response_to_repeater_tab(self, response: str) -> None:
        """
        WASTT/Repeater/Tab:
            Adds the given response text to the repeater tab, updates the state of
            the response text box, and enables the response render button.

            Parameters:
            response: str - The text to be added to the response text box.
        """
        self.response_textbox.configure(state=tk.NORMAL)
        self.response_textbox.insert_text(response)
        self.response_textbox.configure(state=tk.DISABLED)
        self.response_render_button.configure(state=tk.NORMAL)

    def update_dropdown_menu(self) -> None:
        """
        WASTT/Repeater/Tab:
            Updates the dropdown menu functionality for iterations in the application, ensuring
            it reflects the latest available options. The dropdown menu is configured to be
            active and populated with the provided iteration keys. If iteration keys are
            available, the most recent iteration is selected as default.
        """
        self.iteration_dropdown.configure(values=self.tab_iteration_keys, state=tk.NORMAL)
        if self.tab_iteration_keys:
            recent_iteration = self.tab_iteration_keys[0]
            self.iteration_var.set(recent_iteration)

    def select_iteration(self, iteration_name: str) -> None:
        """
        WASTT/Repeater/Tab:
            Selects and loads a specific iteration by its name if the iteration exists within the tab iteration keys.

            Parameters:
            iteration_name: str - The name of the iteration to be selected and loaded.
        """
        if iteration_name in self.tab_iteration_keys:
            self.load_iteration(iteration_name)

    def load_iteration(self, iteration_name: str) -> None:
        """
        WASTT/Repeater/Tab:
            Loads and displays the specified iteration's request and response texts into a user interface.
            The method updates the request and response textboxes to reflect the selected iteration's data.
            It ensures correct state management of the textboxes and corresponding user interface
            elements.

            Parameters:
            iteration_name: str - The name of the iteration to be loaded.
        """
        request_text, response_text = self.tab_iterations[iteration_name]
        self.request_textbox.configure(state=tk.NORMAL)
        self.response_textbox.configure(state=tk.NORMAL)
        self.request_textbox.delete("1.0", tk.END)
        self.request_textbox.insert_text(request_text)
        self.response_textbox.delete("1.0", tk.END)
        self.response_textbox.insert_text(response_text)
        self.response_textbox.configure(state=tk.DISABLED)
        self.response_render_button.configure(state=tk.NORMAL)

    def generate_request(self) -> None:
        """
        WASTT/Repeater/Tab:
            Generates and prepares an HTTP request.

            This method constructs an HTTP/2.0 GET request, populates the text box with the generated
            HTTP request string, and updates the URL entry field with the given URL.
        """
        url = "https://www.example.com"
        http_request = "GET / HTTP/2.0"

        self.request_textbox.insert_text(http_request)
        self.hosturl_entry.delete(0, tk.END)
        self.hosturl_entry.insert(0, url)


class Repeater(ctk.CTkFrame):
    """
    WASTT/Repeater:
        Repeater class manages a collection of tabs within a user interface, allowing users to add,
        navigate, update, and delete tabs. Each tab within the Repeater can hold specific content,
        enabling organization and interaction within the application.

        This class is primarily designed for scenarios where dynamic tab management is required.
        It provides user-friendly functionality to seamlessly handle tabbed content, supporting
        actions like adding new tabs, switching between them, and updating their state or content.
        Tabs are managed via a navigation frame that includes buttons for each tab and an add button
        to create new tabs.
    """
    def __init__(self, master, root):
        super().__init__(master)
        self.configure(fg_color=color_bg_br, bg_color="transparent", corner_radius=10)
        self.wastt = root

        # ================================================
        # Tabs and their respective nav buttons,
        # ================================================
        self.tabs = []
        self.tab_nav = ctk.CTkFrame(self, fg_color="transparent")
        self.tab_nav.pack(side=tk.TOP, fill=tk.X, padx=25, pady=(10, 0))
        self.current_tab = 0
        self.tab_nav_buttons = []
        first_tab_button = NavButton(
            self.tab_nav,
            text="1",
            command=lambda: self.show_tab(0),
            background=color_bg_br,
            background_selected=color_bg
        )
        self.tab_nav_buttons.append(first_tab_button)
        first_tab_button.pack(side=tk.LEFT)

        tab_add_button = NavButton(
            self.tab_nav,
            text="",
            icon=icon_add,
            command=self.add_tab,
            background=color_bg_br,
            background_selected=color_bg
        )
        tab_add_button.pack(side=tk.RIGHT)

        # ================================================
        # Initialising the first tab
        # ================================================
        self.tabs.append(
            RepeaterTab(self, self.current_tab)
        )
        self.show_tab(self.current_tab)

    def add_tab(self, new_tab: RepeaterTab = None) -> None:
        """
        WASTT/Repeater:
            Adds a new tab to the interface and displays it.

            If a new_tab instance is not provided, a new instance of RepeaterTab will
            be created and added.

            Parameters:
            new_tab: RepeaterTab - optional - The tab instance to be added. Defaults to None, in which case a new
                    instance of RepeaterTab is created.
        """
        if len(self.tab_nav_buttons) < 20:
            new_tab_id = len(self.tab_nav_buttons)
            new_tab_nav_button = NavButton(
                self.tab_nav,
                text=str(new_tab_id + 1),
                command=lambda: self.show_tab(new_tab_id),
                background=color_bg_br,
                background_selected=color_bg
            )
            self.tab_nav_buttons.append(new_tab_nav_button)
            new_tab_nav_button.pack(side=tk.LEFT, padx=(10, 0))

            if new_tab is None:
                new_tab = RepeaterTab(self, new_tab_id)
            self.tabs.append(new_tab)
            self.show_tab(new_tab_id)
        else:
            ErrorDialog(self, self.wastt, "Maximum number of tabs reached.")

    def show_tab(self, tab_id: int) -> None:
        """
        WASTT/Repeater:
            Updates the displayed tab within a user interface by selecting the provided tab ID and deselecting the others.
            The corresponding tab content is shown while hiding all other tabs.

            Parameters:
            tab_id: int - The ID of the tab to display and activate.
        """
        self.current_tab = tab_id
        for i, tab in enumerate(self.tabs):
            if i == tab_id:
                self.tab_nav_buttons[i].select(True)
                tab.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
            else:
                self.tab_nav_buttons[i].select(False)
                tab.pack_forget()

    def delete_tab(self, tab_id: int) -> None:
        """
        WASTT/Repeater:
            Deletes a tab with the specified tab ID and updates the tab navigation
            accordingly. If the deleted tab is currently active, it switches focus
            to the nearest previous tab.

            Parameters:
            tab_id: int - ID of the tab to be deleted.
        """
        if self.current_tab == tab_id:
            self.show_tab(tab_id - 1)

        self.tabs.pop(tab_id)
        self.tab_nav_buttons[tab_id].pack_forget()
        self.tab_nav_buttons.pop(tab_id)

        self.update_tab_numbering()

    def update_tab_numbering(self) -> None:
        """
        WASTT/Repeater:
            Updates the numbering of tabs and their associated navigational buttons.

            This method iterates through the list of navigation buttons and reassigns a
            number to each button's label, starting from 1. It also updates the internal
            numbering of the corresponding tabs. Each button's command is configured
            to navigate to its respective tab.
        """
        for i, button in enumerate(self.tab_nav_buttons):
            button.main_button.configure(text=str(i + 1), command=lambda t=i: self.show_tab(t))
            self.tabs[i].update_number(i)

    def add_request_to_repeater_tab(self, content: str, host: str = None) -> None:
        """
        WASTT/Repeater:
            Adds a request to an available repeater tab or creates a new one if all existing tabs
            are occupied. This method organizes requests by distributing them to tabs, which can
            either be empty or newly instantiated, ensuring all requests are facilitated.

            Parameters:
            content: str - The content of the request to be added to the repeater tab.
            host: str - optional - The host URL to associate with the request. Defaults to None.
        """
        for tab in self.tabs:
            if tab.is_empty:
                tab.hosturl = host
                tab.hosturl_entry.insert(0, host)
                tab.request_textbox.insert_text(content)
                tab.is_empty = False
                return
        else:
            new_tab = RepeaterTab(self, len(self.tab_nav_buttons), content, host)
            self.add_tab(new_tab)

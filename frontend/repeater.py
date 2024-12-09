from head import *
from functools import partial
import customtkinter as ctk
from proxy import RequestTextBox
from backend.Request import Request2
from backend.global_setup import *
import pickle
import asyncio
import threading
from utils.request_methods import *


class RepeaterNav(ctk.CTkFrame):
    def __init__(self, master, frames):
        super().__init__(master)
        self.configure(fg_color="transparent")
        self.gui = master
        self.frames = frames
        self.current_frame = 0
        self.buttons = []
        self.buttons.append(NavButton(self,
                                      text="1",
                                      command=partial(self.show_frame, 0),
                                      font=ctk.CTkFont(family="Calibri", size=14, weight="normal"),
                                      background=color_bg_br,
                                      background_selected=color_bg))
        self.buttons[0].pack(side="left")
        self.pack(side="top", fill="x", padx=15, pady=(10, 0))
        self.frames.append(RepeaterFrame(self.master, 0, self))
        self.show_frame(0)

    def show_frame(self, n):
        self.current_frame = n
        # print(f"Debug Intruder: Showing frame: {n + 1}")
        for i, frame in enumerate(self.frames):
            if i == n:
                self.buttons[i].set_selected(True)
                frame.pack(side="top", fill="both", expand=True, padx=5, pady=(0, 5))
            else:
                self.buttons[i].set_selected(False)
                frame.pack_forget()

    def add_frame(self, new_frame=None):
        new_id = len(self.buttons)
        # print(f"Debug Intruder: Adding frame: {new_id + 1}")
        new_frame_button = NavButton(self,
                                     text=str(new_id + 1),
                                     command=partial(self.show_frame, new_id),
                                     font=ctk.CTkFont(family="Calibri", size=14, weight="normal"),
                                     background=color_bg_br,
                                     background_selected=color_bg
                                     )
        self.buttons.append(new_frame_button)
        new_frame_button.pack(side="left", padx=(10, 0))

        if new_frame is None:
            new_frame = RepeaterFrame(self.master, new_id, self)
            self.frames.append(new_frame)
        else:
            self.frames.append(new_frame)

    def delete_frame(self, n):
        # print(f"Debug Intruder: Deleting frame: {n + 1}")
        if self.current_frame == n:
            self.show_frame(n - 1)

        self.frames[n].pack_forget()
        self.frames.pop(n)
        self.buttons[n].pack_forget()
        self.buttons.pop(n)

        self.update_numbering()

    def update_numbering(self):
        for i, button in enumerate(self.buttons):
            button.main_button.configure(text=str(i + 1), command=partial(self.show_frame, i))
            self.frames[i].update_number(i)


class RepeaterFrame(ctk.CTkFrame):
    def __init__(self, master, id_number, nav, request=None):
        super().__init__(master)
        self.configure(
            fg_color=color_bg,
            corner_radius=10,
            background_corner_colors=(color_bg_br, color_bg_br, color_bg_br, color_bg_br)
        )
        self.gui = master
        self.id = id_number
        if self.id == 0:
            self.is_empty = True
        else:
            self.is_empty = False
        self.nav = nav

        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        icon_send = ctk.CTkImage(
            light_image=Image.open(f"{ASSET_DIR}\\icon_arrow_up.png"),
            dark_image=Image.open(f"{ASSET_DIR}\\icon_arrow_up.png"), size=(20, 20))

        self.send_button = ctk.CTkButton(
            self.top_bar,
            text="Send",
            width=30,
            image=icon_send,
            command=self.send_request_to_proxy,
            compound="left",
            corner_radius=32
        )
        self.send_button.pack(padx=10, pady=10, side="left")

        icon_delete = ctk.CTkImage(
            light_image=Image.open(f"{ASSET_DIR}\\icon_delete.png"),
            dark_image=Image.open(f"{ASSET_DIR}\\icon_delete.png"), size=(20, 20))
        
        if self.id != 0:
            self.delete_frame_button = ctk.CTkButton(
                self.top_bar,
                text="Delete the card",
                width=30,
                image=icon_delete,
                command=partial(self.nav.delete_frame, self.id),
                compound="left",
                corner_radius=32
            )
            self.delete_frame_button.pack(padx=10, pady=10, side="right")

        self.clear_request_button = ctk.CTkButton(
            self.top_bar,
            text="Clear request",
            width=30,
            image=icon_delete,
            command=self.clear_request,
            compound="left",
            corner_radius=32,
            state=tk.DISABLED
        )
        self.clear_request_button.pack(padx=10, pady=10, side="right")

        self.request_header = HeaderTitle(self, text="Request")
        self.request_header.grid(row=1, column=0, padx=10, pady=(5, 0), sticky="w")

        self.request_textbox = RequestTextBox(self, self.master, text="")
        self.request_textbox.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="nsew")
        if request is not None:
            self.request_textbox.insert_text(request)
            self.is_empty = False
            self.clear_request_button.configure(state=tk.NORMAL)
        self.request_textbox.bind("<<Modified>>", self.on_request_textbox_change)

        self.response_header = HeaderTitle(self, text="Response")
        self.response_header.grid(row=1, column=1, padx=10, pady=(5, 0), sticky="w")

        self.response_textbox = RequestTextBox(self, self.master, text="Response will appear here.")
        self.response_textbox.configure(state="disabled")
        self.response_textbox.grid(row=2, column=1, padx=10, pady=(0, 10), sticky="nsew")

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # TODO Confirm if these async methods can be deleted
        # self.loop = asyncio.new_event_loop()  # Tworzymy pętlę asyncio dla tego obiektu
        # self.start_async_servers()
        #
        # self.flow = None

    def update_number(self, id_number):
        self.id = id_number
        if self.id != 0:
            self.delete_frame_button.configure(
                command=partial(self.nav.delete_frame, self.id)
            )

    def on_request_textbox_change(self, event):
        self._reset_request_modified_flag()
        if len(self.request_textbox.get_text()) > 0:
            self.is_empty = False
            self.clear_request_button.configure(state=tk.NORMAL)

    def clear_request(self):
        self._reset_request_modified_flag()
        self.request_textbox.delete("1.0", tk.END)
        self.is_empty = True
        self.clear_request_button.configure(state=tk.DISABLED)

    def _reset_request_modified_flag(self):
        self.request_textbox.edit_modified(False)

    # TODO Confirm if these async methods can be deleted
    # def start_async_servers(self):
    #     """
    #     Starts the asyncio servers in a separate thread to handle scope updates and flow killing asynchronously.
    #     """
    #
    #     def run_servers():
    #         asyncio.set_event_loop(self.loop)
    #         tasks = [
    #             self.listen_for_flow(),
    #             self.listen_for_response(),
    #         ]
    #         self.loop.run_until_complete(asyncio.gather(*tasks))
    #
    #     thread = threading.Thread(target=run_servers, daemon=True)
    #     thread.start()
    #
    # async def listen_for_flow(self):
    #     server = await asyncio.start_server(
    #         self.handle_flow, HOST, BACK_REPEATER_FLOWSEND_PORT
    #     )
    #     async with server:
    #         await server.serve_forever()
    #
    # async def handle_flow(self, reader, writer):
    #     serialized_flow = await reader.read(4096)
    #     if serialized_flow:
    #         try:
    #             deserialized_flow = pickle.loads(serialized_flow)
    #             self.flow = deserialized_flow
    #
    #         except Exception as e:
    #             print(f"Error while deserialization recived in repeater: {e}")
    #         try:
    #             request2 = Request2.from_request(deserialized_flow.request)
    #             self.gui.add_request_to_repeater_tab(request2.return_http_message())
    #         except Exception as e:
    #             print(f"Error while display request in repeater textbox: {e}")
    #     writer.close()
    #     await writer.wait_closed()
    #
    # async def listen_for_response(self):
    #     server = await asyncio.start_server(
    #         self.handle_response, HOST, BACK_REPEATER_RESPONSESEND_PORT
    #     )
    #     async with server:
    #         await server.serve_forever()
    #
    # async def handle_response(self, reader, writer):
    #     serialized_response = await reader.read(4096)
    #     if serialized_response:
    #         try:
    #             deserialized_response = pickle.loads(serialized_response)
    #         except Exception as e:
    #             print(f"Error while deserialization recived in repeater: {e}")
    #         try:
    #             self.add_response_to_repeater_tab(deserialized_response.content)
    #         except Exception as e:
    #             print(f"Error while display respose in repeater textbox: {e}")
    #     writer.close()
    #
    #     await writer.wait_closed()

    def send_request_to_proxy(self):
        # TODO It correctly parses headers that follow pattern like example.com, headers from wp.pl or kurnik.pl fail
        response = send_http_message(self.request_textbox.get_text())
        self.add_response_to_repeater_tab(process_response(response))

    def add_response_to_repeater_tab(self, response):
        self.response_textbox.configure(state="normal")
        self.response_textbox.insert_text(response)
        self.response_textbox.configure(state="disabled")


class GUIRepeater(ctk.CTkFrame):
    def __init__(self, master, root):
        super().__init__(master)
        self.configure(fg_color="transparent")
        self.root = root
        self.frames = []
        self.nav = RepeaterNav(self, self.frames)

    def add_request_to_repeater_tab(self, request):
        for frame in self.frames:
            if frame.is_empty:
                frame.request_textbox.insert_text(request)
                frame.is_empty = False
                return
        else:
            new_frame = RepeaterFrame(self, len(self.nav.buttons), self.nav, request)
            self.nav.add_frame(new_frame)

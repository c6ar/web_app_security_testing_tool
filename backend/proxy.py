import pickle
from time import sleep

import mitmproxy.http
import socket
from mitmproxy.http import Request
from global_setup import *
import asyncio
import threading
from utils.get_domain import extract_domain


class WebRequestInterceptor:
    def __init__(self):
        self.scope = []
        self.loop = asyncio.new_event_loop()  # Tworzymy pętlę asyncio dla tego obiektu
        self.start_async_servers()
        self.current_flow = None
        self.intercept_state = False
        self.backup= []


    def request(self, flow: mitmproxy.http.HTTPFlow):
        """
        Made for mitmproxy, triggered when new HTTPFlow is created.
        Acts as a bridge between mitmproxy and the rest of the program.
        """
        request = flow.request
        self.current_flow = flow
        flow.intercept()
        if "mozilla.org" in request.host:
            """
            Filters out telemetry 
            """
            flow.request = Request.make(
                method="GET",
                url="https://google.com",
                content="",
                headers={"Accept": "*/*"}
            )
            flow.resume()
        elif extract_domain(request.host) not in self.scope:
            if flow.intercepted:
                flow.resume()
        else:
            self.send_request2_to_scope_tab(request)
            self.recieve_request_from_scope_forward_button(flow)

    def response(self, flow: mitmproxy.http.HTTPFlow):
        if flow.response:
            self.send_flow_to_http_trafic_tab(flow)

    def start_async_servers(self):
        """
        Starts the asyncio servers in a separate thread to handle scope updates and flow killing asynchronously.
        """
        def run_servers():
            asyncio.set_event_loop(self.loop)
            tasks = [
                self.add_host_to_scope(),
                self.listen_for_kill_flow(),
                self.listen_for_intercept_button(),
            ]
            self.loop.run_until_complete(asyncio.gather(*tasks))

        thread = threading.Thread(target=run_servers, daemon=True)
        thread.start()

    async def listen_for_intercept_button(self):
        server = await asyncio.start_server(
            self.handle_toggle_intercept, HOST, FRONT_BACK_INTERCEPTBUTTON_PORT
        )
        async with server:
            await server.serve_forever()

    async def handle_toggle_intercept(self,reader, writer):
        data = await reader.read(4096)
        if data:
            self.intercept_state = not self.intercept_state
            if not self.intercept_state:
                self.backup = self.scope
                self.scope = []
                if self.current_flow.intercepted:
                    self.current_flow.resume()
            else:

                self.scope = self.backup
        writer.close()
        await writer.wait_closed()

    async def add_host_to_scope(self):
        """
        Asynchronously receives and adds hostname to scope.
        """
        server = await asyncio.start_server(
            self.handle_scope_update, HOST, FRONT_BACK_SCOPEUPDATE_PORT
        )
        async with server:
            await server.serve_forever()

    async def handle_scope_update(self, reader, writer):
        """
        Handles incoming scope updates.
        """
        data = await reader.read(4096)
        if data:
            deserialized_request = pickle.loads(data)
            self.backup.append(extract_domain(deserialized_request.host))
            print("\nHost added to scope:", extract_domain(deserialized_request.host))
        writer.close()
        await writer.wait_closed()

    async def listen_for_kill_flow(self):
        """
        Asynchronously listens for flow kill requests.
        """
        server = await asyncio.start_server(
            self.handle_kill_request, HOST, FRONT_BACK_DROPREQUEST_PORT
        )
        async with server:
            await server.serve_forever()

    async def handle_kill_request(self, reader, writer):
        """
        Handles incoming requests to kill a flow.
        """
        data = await reader.read(4096)
        if data:
            bad_request = Request.make(
                method="POST",
                url="https://google.com",
                content="",
                headers={"Accept": "*/*"}
            )

            self.current_flow.request.data = bad_request.data
            self.current_flow.resume()
            print(f"\nReceived request to kill flow")
        writer.close()
        await writer.wait_closed()

    def send_flow_to_http_trafic_tab(self, flow):
        """
        Serializes tab = [flow.reqeust, flow.response] and sends to
        frontend.proxy.GUIProxy.receive_and_add_to_http_traffic
        """
        if flow.response is not None:
            flow_tab = [flow.request, flow.response]
        else:
            flow_tab = flow.request
        try:
            serialized_flow = pickle.dumps(flow_tab)
        except Exception as e:
            print(f"Error przy pakowaniem przed wyslaniem do http: {e}")
            serialized_flow = pickle.dumps(flow.request)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, BACK_FRONT_HISTORYREQUESTS_PORT))
                s.sendall(serialized_flow)
        except Exception as e:
            print(f"\nError while sending request to http tab: {e}")

    def send_request2_to_scope_tab(self, request):
        """
        Serializes request and sends it to GUI scope tab.
        """
        try:
            serialized_request2 = pickle.dumps(request)
        except Exception as e:
            print(f"\nError while serialization before sending to scope tab: {e}")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, BACK_FRONT_SCOPEREQUESTS_PORT))
                s.sendall(serialized_request2)
        except Exception as e:
            print(f"\nError while sending request to scope tab: {e}")

    def recieve_request_from_scope_forward_button(self, flow):
        """
        Receives request from GUI when forward button in scope is pressed.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, FRONT_BACK_FORWARDBUTTON_PORT))
            s.listen()

            conn, addr = s.accept()
            with conn:
                serialized_reqeust = conn.recv(4096)
                if serialized_reqeust:
                    deserialize_reqeust = pickle.loads(serialized_reqeust)
                    flow.request.data = deserialize_reqeust.data
                    if flow.intercepted:
                        flow.resume()

addons = [
    WebRequestInterceptor()
]

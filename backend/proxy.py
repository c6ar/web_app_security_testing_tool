import pickle
from time import sleep

import mitmproxy.http
import socket
from mitmproxy import http
from flask import request

from mitmproxy.http import Request
from global_setup import *
from mitmproxy import http
import asyncio
import threading


#TODO usuwanie requesta ze scope?

#TODO przycisk intercept podmienia  scope filter


class WebRequestInterceptor:
    def __init__(self):
        self.scope = []
        self.loop = asyncio.new_event_loop()  # Tworzymy pętlę asyncio dla tego obiektu
        self.start_async_servers()  # Uruchamiamy serwery asynchroniczne w tle
        self.current_flow = None

    def request(self, flow: mitmproxy.http.HTTPFlow):
        """
        Made for mitmproxy, triggered when new HTTPFlow is created.
        Acts as a bridge between mitmproxy and the rest of the program.
        """
        print(self.scope)
        request = flow.request
        self.current_flow = flow
        flow.intercept()

        if "mozilla.org" in request.host:
            """
            Filters out telemetry 
            """
            flow.request = Request.make(
                method="POST",
                url="https://google.com",
                content="",
                headers={"Accept": "*/*"}
            )
            flow.resume()
        elif request.host not in self.scope:
            if flow.intercepted:
                flow.resume()
            #self.send_flow_to_http_trafic_tab(flow)
        else:
            self.send_request2_to_scope_tab(request)
            self.recieve_reques_from_scope_forward_button(flow)

    def response(self, flow: mitmproxy.http.HTTPFlow ):
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
            ]
            self.loop.run_until_complete(asyncio.gather(*tasks))

        thread = threading.Thread(target=run_servers, daemon=True)
        thread.start()

    async def add_host_to_scope(self):
        """
        Asynchronously receives and adds hostname to scope.
        """
        server = await asyncio.start_server(
            self.handle_scope_update, HOST, FRONT_BACK_SCOPEUPDATE_PORT
        )
        async with server:
            await server.serve_forever()

    async def listen_for_kill_flow(self):
        """
        Asynchronously listens for flow kill requests.
        """
        server = await asyncio.start_server(
            self.handle_kill_request, HOST, FRONT_BACK_DROPREQUEST_PORT
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
            self.scope.append(deserialized_request.host)
            print("Host added to scope:", deserialized_request.host)
        writer.close()
        await writer.wait_closed()

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
            print(f"Received request to kill flow")
            # This is a placeholder; you'll need to replace this with actual flow handling
        writer.close()
        await writer.wait_closed()

    def send_flow_to_http_trafic_tab(self, flow):
        """
        Serializes flow and sends it to GUI HTTP traffic tab.
        """
        try:
            serialized_flow = pickle.dumps(flow)
        except Exception as e:
            print(f"Error while serialization before sending to http traffic tab: {e}")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, BACK_FRONT_HISTORYREQUESTS_PORT))
                s.sendall(serialized_flow)
        except Exception as e:
            print(f"Error while sending request to http tab: {e}")

    def send_request2_to_scope_tab(self, request):
        """
        Serializes request and sends it to GUI scope tab.
        """
        try:
            serialized_request2 = pickle.dumps(request)
        except Exception as e:
            print(f"Error while serialization before sending to scope tab: {e}")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, BACK_FRONT_SCOPEREQUESTS_PORT))
                s.sendall(serialized_request2)
        except Exception as e:
            print(f"Error while sending request to scope tab: {e}")

    def recieve_reques_from_scope_forward_button(self, flow):
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

    def kill_flow(self):
        """
        Kills flow when drop button in scope tab is pressed.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, FRONT_BACK_DROPREQUEST_PORT))
            s.listen()

            while True:
                conn, addr = s.accept()
                with conn:
                    flag = conn.recv(4096)
                    if flag:
                        print("kill")
                        self.current_flow.kill()


addons = [
    WebRequestInterceptor()
]

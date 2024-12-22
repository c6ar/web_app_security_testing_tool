import pickle
import mitmproxy.http
import socket
from mitmproxy import ctx
from mitmproxy.http import Request, Response, HTTPFlow
import asyncio
import threading
from global_setup import *


class WebRequestInterceptor:
    def __init__(self):
        self.scope = []
        self.loop = asyncio.new_event_loop()
        self.start_async_servers()
        self.current_flow = None
        self.intercept_state = False
        self.backup= []
        self.repeater_flow = None
        self.repeater_backup_flow = None


    def request(self, flow: mitmproxy.http.HTTPFlow):
        """
        Made for mitmproxy, triggered when new HTTPFlow is created.
        Acts as a bridge between mitmproxy and the rest of the program.
        """
        request = flow.request
        self.current_flow = flow
        flow.intercept()
        self.repeater_backup_flow = flow.copy()
        telemetry_hosts = [
            # Google Chrome
            "clients4.google.com",
            "clients2.google.com",
            "update.googleapis.com",
            "ssl.gstatic.com",
            "google-analytics.com",

            # Mozilla Firefox
            "incoming.telemetry.mozilla.org",
            "updates.mozilla.org",
            "snippets.cdn.mozilla.net",
            "firefox.settings.services.mozilla.com",

            # Microsoft Edge
            "edge.microsoft.com",
            "config.edge.skype.com",
            "v10.events.data.microsoft.com",
            "bing.com",
            "arc.msn.com",

            # Safari
            "gsp1.apple.com",
            "gs-loc.apple.com",
            "configuration.apple.com",
            "analytics.edge.apple.com",

            # Opera
            "autoupdate.opera.com",
            "api.sec-tunnel.com",
            "sync.opera.com",
            "extensions.gopera.com",

            # Brave
            "cr.brave.com",
            "p3a.brave.com",
            "laptop-updates.brave.com"
        ]
        if  request.host in telemetry_hosts:
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
        elif self.intercept_state and self.scope ==[]:
            print(f"INTERCEPTED REQUEST TO {request.host}"
                  f"\nHostname from the request: {request.host}"
                  f"\nHostnames in the current scope: {self.scope}")
            self.send_request_to_intercept_tab(request)
            self.receive_forwarded_request(flow)
        elif request.host not in self.scope:
            if flow.intercepted:
                flow.resume()

        else:
            print(f"INTERCEPTED REQUEST TO {request.host}"
                  f"\nHostname from the request: {request.host}"
                  f"\nHostnames in the current scope: {self.scope}")
            self.send_request_to_intercept_tab(request)
            self.receive_forwarded_request(flow)

    def response(self, flow: mitmproxy.http.HTTPFlow):
        if flow.response:
            self.send_flow_to_http_trafic_tab(flow)
            self.repeater_flow = flow.copy()

    def start_async_servers(self):
        """
        Starts the asyncio servers in a separate thread to handle scope updates and flow killing asynchronously.
        """
        def run_servers():
            asyncio.set_event_loop(self.loop)
            tasks = [
                self.listen_for_scope_update(),
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

    async def handle_toggle_intercept(self, reader, writer):
        data = await reader.read(4096)
        if data:
            self.intercept_state = not self.intercept_state
            print(self.intercept_state, self.scope)
            if not self.intercept_state:
                self.backup = self.scope
                self.scope = []
                if self.current_flow.intercepted:
                    self.current_flow.resume()
            else:
                self.scope = self.backup.copy()
        print(f"Intercepting state: {self.intercept_state}")
        writer.close()
        await writer.wait_closed()

    async def listen_for_scope_update(self):
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
            operation, *hostnames = pickle.loads(data)
            if operation == "add":
                for hostname in hostnames:
                    self.backup.append(hostname)
                    print(f"Host {hostname} added to the scope.")
            elif operation == "remove":
                for hostname in hostnames:
                    try:
                        self.backup.remove(hostname)
                        print(f"Host {hostname} removed from scope.")
                    except ValueError:
                        print(f"Attempted to remove {hostname} from scope, but could not be found there.")
            elif operation == "clear":
                self.backup.clear()
                print("Scope cleared.")
        print(f"Current scope: {self.backup}")
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
                method="GET",
                url="https://google.com",
                content="",
                headers={"Accept": "*/*"}
            )
            #TODO naprawić kill
            self.current_flow.request.host = "google.com"
            self.current_flow.request.url = "https://google.com"
            self.current_flow.request.port = 443
            self.current_flow.request.scheme = "https"
            self.current_flow.resume()
            if not self.current_flow.intercepted:
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
            print(f"\nError while serialization before sending to http traffic tab: {e}")
            serialized_flow = pickle.dumps(flow.request)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, BACK_FRONT_HISTORYREQUESTS_PORT))
                s.sendall(serialized_flow)
        except Exception as e:
            print(f"\nError while sending request to http tab: {e}")

    def send_request_to_intercept_tab(self, request):
        """
        Serializes request and sends it to GUI scope tab.
        """
        try:
            print(f"\n\nSending intercepted request to Frontend:\n{request.data}")
            serialized_request2 = pickle.dumps(request)
        except Exception as e:
            print(f"\nError while serialization before sending to scope tab: {e}")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, BACK_FRONT_SCOPEREQUESTS_PORT))
                s.sendall(serialized_request2)
        except Exception as e:
            print(f"\nError while sending request to scope tab: {e}")

    def receive_forwarded_request(self, flow):
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
                    deserialized_request = pickle.loads(serialized_reqeust)
                    flow.request.data = deserialized_request.data
                    print(f"\n\nForwarding intercepted request from Frontend:\n{flow.request.data}")
                    if flow.intercepted:
                        flow.resume()


addons = [
    WebRequestInterceptor()
]

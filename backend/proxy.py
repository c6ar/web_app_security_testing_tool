import pickle
import mitmproxy.http
import socket
# noinspection PyUnresolvedReferences
from mitmproxy import ctx
# noinspection PyUnresolvedReferences
from mitmproxy.http import Request, Response, HTTPFlow, Headers
import asyncio
import threading
from config import RUNNING_CONFIG


def send_flow_to_http_trafic_tab(flow):
    """
    Serializes tab = [flow.reqeust, flow.response] and sends to
    frontend.proxy.GUIProxy.receive_and_add_to_http_traffic

    Parameters:
        flow: mitmproxy.http.HTTPFlow object.
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
            s.connect((RUNNING_CONFIG["proxy_host_address"], RUNNING_CONFIG["back_front_request_to_traffic_port"]))
            s.sendall(serialized_flow)
    except Exception as e:
        print(f"\nError while sending request to http tab: {e}")


def send_request_to_intercept_tab(request):
    """
    Serializes request and sends it to GUI scope tab.

    Parameters:
        request: mitmproxy.http.Request object.
    """
    try:
        print(f"======\nSending intercepted request to Frontend:\n{request.data}\n======")
        serialized_request2 = pickle.dumps(request)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((RUNNING_CONFIG["proxy_host_address"], RUNNING_CONFIG["back_front_request_to_intercept_port"]))
                s.sendall(serialized_request2)
        except Exception as e:
            print(f"\nError while sending request to scope tab: {e}")
    except Exception as e:
        print(f"\nError while serialization before sending to scope tab: {e}")


class WebRequestInterceptor:
    """
    A Web Request Interceptor backend logic.

    Acts as a bridge between mitmproxy and the rest of the program.
    """

    def __init__(self):
        """
        Initializes Web Request Interceptor class.
        """
        self.scope = []
        self.loop = asyncio.new_event_loop()
        self.start_async_servers()
        self.current_flow = None
        self.intercept_state = False
        self.backup = []
        self.kill_flow = False

    def request(self, flow: mitmproxy.http.HTTPFlow):
        """
        Method made for mitmproxy process, triggered when new HTTPFlow is created.

        Acts as a bridge between mitmproxy and the rest of the program.

        Parameters:
            flow: mitmproxy.http.HTTPFlow object.
        """
        request = flow.request
        self.current_flow = flow
        if self.intercept_state:
            print(f"======\nProcessing request to {request.host}\n======")
            flow.intercept()

            def extract_domain(full_string):
                """
                Extracts the domain from a string of the format `ads.google.com	`.

                Parameters:
                    full_string (str): The full string containing subdomains and domain.

                Returns:
                    str: The extracted domain (e.g., `google.com`).
                """
                parts = full_string.split('.')
                if len(parts) >= 2:
                    domain = '.'.join(parts[-2:])
                    return domain
                return ""  # Return an empty string if the input is malformed

            if "mozilla.org" in request.host:
                print(f"Received telemetry request to mozilla.org.\n======\nResuming HTTP(S) flow.\n======")
                flow.request = Request.make(
                    method="GET",
                    url="https://google.com",
                    content="",
                    headers={"Accept": "*/*"}
                )
                flow.resume()
            elif not self.scope or request.host in self.scope or extract_domain(request.host) in self.scope:
                if not self.scope:
                    print("Request Interceptor's scope is currently empty.\n======")
                else:
                    print(f"Current Request Interceptor's scope: {self.scope}.\n======")
                print(f"Request to {request.host} has been intercepted.")
                send_request_to_intercept_tab(request)
                self.receive_data_from_frontend(flow)
            elif self.kill_flow:
                flow.kill()
                self.kill_flow = False
            else:
                print(f"Request to {request.host} has been passed throught.\n======")
                if flow.intercepted:
                    flow.resume()
            send_flow_to_http_trafic_tab(flow)
        else:
            print(f"======\nPassing through reqyest to {request.host}\n======")

    # noinspection PyMethodMayBeStatic
    def response(self, flow: mitmproxy.http.HTTPFlow):
        """
        Method made for mitmproxy process, triggered when new HTTPFlow is created.

        Acts as a bridge between mitmproxy and the rest of the program.

        Parameters:
            flow: mitmproxy.http.HTTPFlow object.
        """
        if flow.response:
            send_flow_to_http_trafic_tab(flow)

    def start_async_servers(self):
        """
        Starts the asyncio servers in a separate thread to handle scope updates and flow killing asynchronously.
        """
        def run_servers():
            asyncio.set_event_loop(self.loop)
            tasks = [
                self.listen_for_scope_update(),
                self.listen_for_intercept_button()
            ]
            self.loop.run_until_complete(asyncio.gather(*tasks))

        thread = threading.Thread(target=run_servers, daemon=True)
        thread.start()

    async def listen_for_intercept_button(self):
        """
        Asynchronously listens to the Web Request Interceptor state changes from the frontend.
        """
        async def toggle_intercept(reader, writer):
            """
            Handles the Web Request Interceptor state changes received from the frontend.

            Parameters:
                reader: asyncio.StreamReader object.
                writer: asyncio.StreamWriter object.
            """
            data = await reader.read(4096)
            if data:
                print(f"======\nReceived instruction to change Request Interceptor state.\n======")
                if data.decode('utf-8').lower() == 'false':
                    new_state = False
                else:
                    new_state = True
                self.intercept_state = new_state
                if not self.intercept_state and self.current_flow.intercepted:
                    self.current_flow.resume()
            print(f"Current Request Interceptor state: {self.intercept_state}\n======")
            writer.close()
            await writer.wait_closed()

        server = await asyncio.start_server(
            toggle_intercept, RUNNING_CONFIG["proxy_host_address"], RUNNING_CONFIG["front_back_intercept_toggle_port"]
        )
        async with server:
            await server.serve_forever()

    async def listen_for_scope_update(self):
        """
        Asynchronously listens to Web Request Interceptor scope updates from the frontend.
        """
        async def scope_update(reader, writer):
            """
            Handles incoming scope updates received from the frontend.

            Parameters:
                reader: asyncio.StreamReader object.
                writer: asyncio.StreamWriter object.
            """
            data = await reader.read(4096)
            if data:
                print(f"======\nReceived instruction to update scope of Request Interceptor.\n======")
                operation, *hostnames = pickle.loads(data)
                if operation == "add":
                    for hostname in hostnames:
                        domain = hostname
                        self.scope.append(domain)
                        print(f"Host {domain} added to the scope.\n======")
                elif operation == "remove":
                    for hostname in hostnames:
                        domain = hostname
                        try:
                            self.scope.remove(domain)
                            print(f"Host {domain} removed from scope.\n======")
                        except ValueError:
                            print(f"Attempted to remove {domain} from scope, but could not be found there.\n======")
                elif operation == "clear":
                    self.scope.clear()
                    print("Scope cleared.\n======")
                print(f"Current scope: {self.scope}\n======")
            writer.close()
            await writer.wait_closed()

        server = await asyncio.start_server(
            scope_update, RUNNING_CONFIG["proxy_host_address"], RUNNING_CONFIG["front_back_scope_update_port"]
        )
        async with server:
            await server.serve_forever()

    def receive_data_from_frontend(self, flow):
        """
        Receives request from GUI when forward button in scope is pressed.

        Parameters:
            flow: mitmproxy.http.HTTPFlow object.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((RUNNING_CONFIG["proxy_host_address"], RUNNING_CONFIG["front_back_data_port"]))
            s.listen()
            conn, addr = s.accept()
            with conn:
                serialized_data = conn.recv(4096)
                if serialized_data:
                    deserialized_data = pickle.loads(serialized_data)
                    print(f"======\nReceived data from the frontend.\n======")
                    if deserialized_data[0] == "forward":
                        print("Received instruction to forward the last intercepted request.\n======")
                        if isinstance(deserialized_data[1], Request):
                            print(f"Forwarding intercepted request:\n{flow.request.data}\n======")
                            flow.request.data = deserialized_data[1].data
                    elif deserialized_data[0] == "drop":
                        print("Received instruction to drop the last intercepted request.\n======")

                        # drop_string = ("GET /en/drop.html HTTP/1.1\n"
                        #                "host: localhost:8080)\n"
                        #                "connection: keep-alive\n"
                        #                "user-Agent: CustomClient/1.0\n"
                        #                "accept: text/html")
                        # from backend.Request import Request2
                        # drop_request = Request2.from_http_message(drop_string)
                        # drop_request.host = "localhost"
                        # drop_request.port = 8080
                        # drop_request.scheme = "http"

                        # flow.request = drop_request

                        target_url = "http://localhost:8080/en/drop.html"

                        response = Response.make(
                            302,  # HTTP status code for redirect
                            b"",  # Empty content (no body needed for redirect)
                            Headers(
                                Location=target_url  # Redirect Location header
                            )
                        )

                        flow.response = response
                        flow.resume()
                        self.kill_flow = True
                    else:
                        print("Received unknown instruction.\n======\nResuming current flow.\n======")
                if flow.intercepted:
                    flow.resume()


addons = [
    WebRequestInterceptor()
]

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


def lprint(msg, h=False, i=False):
    """
    Logs a message to the console and to the log file if enabled.

    Parameters:
        msg: str, the message to be logged and displayed to the console / Proxy terminal.
        h: bool, optional. If True, saves events to HTTP Traffic logs.
        i: bool, optional. If True, saves events to WebInterceptor logs.
    """
    if RUNNING_CONFIG["proxy_logging"]:
        from pathlib import Path
        from datetime import datetime
        log_path = Path(RUNNING_CONFIG["proxy_logs_location"])
        date = datetime.now().strftime("%Y-%m-%d")
        log_file = log_path / f"proxy-{date}.log"

        log_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        lines = msg.split('\n')

        with log_file.open("a") as file:
            for line in lines:
                if "======" not in line:
                    file.write(f"[{timestamp}] {line}\n")
        if h:
            log_file = log_path / "http_traffic" / f"traffic-{date}.log"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with log_file.open("a") as file:
                for line in lines:
                    if "======" not in line:
                        file.write(f"[{timestamp}] {line}\n")
        if i:
            log_file = log_path / "web_interceptor" / f"interceptor-{date}.log"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with log_file.open("a") as file:
                for line in lines:
                    if "======" not in line:
                        file.write(f"[{timestamp}] {line}\n")

    print(msg)


def send_flow_to_http_trafic_tab(flow):
    """
    Serializes tab = [flow.reqeust, flow.response] and sends to
    frontend.proxy.GUIProxy.receive_and_add_to_http_traffic

    Parameters:
        flow: mitmproxy.http.HTTPFlow object.
    """
    if flow.response is not None:
        flow_tab = [flow.request, flow.response]
        lprint(f"======\nSending request with response to HTTP Traffic Tab:\n{flow_tab}\n======", h=True)
    else:
        flow_tab = flow.request
        lprint(f"======\nSending sole request to HTTP Traffic Tab:\n{flow_tab}\n======", h=True)
    try:
        serialized_flow = pickle.dumps(flow_tab)
    except Exception as e:
        lprint(f"\nError while serialization before sending to http traffic tab: {e}")
        serialized_flow = pickle.dumps(flow.request)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((RUNNING_CONFIG["proxy_host_address"], RUNNING_CONFIG["back_front_request_to_traffic_port"]))
            s.sendall(serialized_flow)
    except Exception as e:
        lprint(f"\nError while sending request to http tab: {e}")


def send_request_to_intercept_tab(request):
    """
    Serializes request and sends it to GUI scope tab.

    Parameters:
        request: mitmproxy.http.Request object.
    """
    try:
        lprint(f"======\nSending intercepted request to Web Interceptor Tab:\n{request.data}\n======", i=True)
        serialized_request2 = pickle.dumps(request)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((RUNNING_CONFIG["proxy_host_address"], RUNNING_CONFIG["back_front_request_to_intercept_port"]))
                s.sendall(serialized_request2)
        except Exception as e:
            lprint(f"\nError while sending request to scope tab: {e}")
    except Exception as e:
        lprint(f"\nError while serialization before sending to scope tab: {e}")


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
            lprint(f"======\nProcessing request to {request.host}\n======", i=True)
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
                lprint(f"Received telemetry request to mozilla.org.\n======\nResuming HTTP(S) flow.\n======", i=True)
                flow.request = Request.make(
                    method="GET",
                    url="https://google.com",
                    content="",
                    headers={"Accept": "*/*"}
                )
                flow.resume()
            elif not self.scope or request.host in self.scope or extract_domain(request.host) in self.scope:
                if not self.scope:
                    lprint("Request Interceptor's scope is currently empty.\n======", i=True)
                else:
                    lprint(f"Current Request Interceptor's scope: {self.scope}.\n======", i=True)
                lprint(f"Request to {request.host} has been intercepted.")
                send_request_to_intercept_tab(request)
                self.receive_data_from_frontend(flow)
            else:
                lprint(f"Request to {request.host} has been passed throught.\n======", i=True)
                if flow.intercepted:
                    flow.resume()
            send_flow_to_http_trafic_tab(flow)
        else:
            lprint(f"======\nPassing through request to {request.host}\n======")

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
                lprint(f"======\nReceived instruction to change Request Interceptor state.\n======", i=True)
                if data.decode('utf-8').lower() == 'false':
                    new_state = False
                else:
                    new_state = True
                self.intercept_state = new_state
                if not self.intercept_state and self.current_flow.intercepted:
                    self.current_flow.resume()
            lprint(f"Current Request Interceptor state: {self.intercept_state}\n======", i=True)
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
                lprint(f"======\nReceived instruction to update scope of Request Interceptor.\n======", i=True)
                operation, *hostnames = pickle.loads(data)
                if operation == "add":
                    for hostname in hostnames:
                        domain = hostname
                        self.scope.append(domain)
                        lprint(f"Host {domain} added to the scope.\n======", i=True)
                elif operation == "remove":
                    for hostname in hostnames:
                        domain = hostname
                        try:
                            self.scope.remove(domain)
                            lprint(f"Host {domain} removed from scope.\n======", i=True)
                        except ValueError:
                            lprint(f"Attempted to remove {domain} from scope, but could not be found there.\n======", i=True)
                elif operation == "clear":
                    self.scope.clear()
                    lprint("Scope cleared.\n======", i=True)
                lprint(f"Current scope: {self.scope}\n======", i=True)
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
                    lprint(f"======\nReceived data from the frontend.\n======", i=True)
                    if deserialized_data[0] == "forward":
                        lprint("Received instruction to forward the last intercepted request.\n======", i=True)
                        if isinstance(deserialized_data[1], Request):
                            lprint(f"Forwarding intercepted request:\n{flow.request.data}\n======", i=True)
                            flow.request.data = deserialized_data[1].data
                    elif deserialized_data[0] == "drop":
                        lprint("Received instruction to drop the last intercepted request.\n======", i=True)

                        target_url = "http://localhost:8080/en/dropped.html"

                        flow.request.method = "GET"
                        flow.request.url = target_url
                        flow.request.version = "HTTP/1.1"
                        flow.resume()

                        self.intercept_state = False

                    else:
                        lprint("Received unknown instruction.\n======\nResuming current flow.\n======", i=True)
                if flow.intercepted:
                    flow.resume()


addons = [
    WebRequestInterceptor()
]

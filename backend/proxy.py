import pickle
import mitmproxy.http
import socket
from mitmproxy.http import Request
import asyncio
import threading
import traceback
import sys
from pathlib import Path

root_directory = Path(__file__).resolve().parent.parent
sys.path.append(str(root_directory))

from config import RUNNING_CONFIG


def lprint(msg, h=False, i=False) -> None:
    """
    Logs a message to the console and to the log file if proxy_logging setting enabled.

    Parameters:
        msg: str, the message to be logged and displayed to the console / Proxy terminal.
        h: bool, optional. If True, saves an event to HTTP Traffic logs.
        i: bool, optional. If True, saves an event to Web Request Interceptor logs.
    """
    from pathlib import Path
    from datetime import datetime

    logs_location = RUNNING_CONFIG.get("logs_location", "")
    if not logs_location:
        app_dir = Path(__file__).resolve().parent.parent
        logs_location = app_dir / "logs"
    else:
        logs_location = Path(logs_location)

    logs_path = Path(logs_location)

    proxy_dir = logs_path / "proxy"
    interceptor_dir = logs_path / "web_interceptor"
    traffic_dir = logs_path / "http_traffic"

    proxy_dir.mkdir(parents=True, exist_ok=True)
    interceptor_dir.mkdir(parents=True, exist_ok=True)
    traffic_dir.mkdir(parents=True, exist_ok=True)

    date = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    lines = msg.split('\n')

    if h:
        log_file = traffic_dir / f"traffic-{date}.log"
        with log_file.open("a") as file:
            for line in lines:
                if "======" not in line and "******" not in line:
                    file.write(f"[{timestamp}] {line}\n")

    if i:
        log_file = interceptor_dir / f"interceptor-{date}.log"
        with log_file.open("a") as file:
            for line in lines:
                if "======" not in line and "******" not in line:
                    file.write(f"[{timestamp}] {line}\n")

    if RUNNING_CONFIG["proxy_logging"]:
        log_file = proxy_dir / f"proxy-{date}.log"

        with log_file.open("a") as file:
            for line in lines:
                if "======" not in line and "******" not in line:
                    file.write(f"[{timestamp}] {line}\n")
    print(msg)


def send_request_to_intercept_tab(flow: mitmproxy.http.HTTPFlow) -> None:
    """
    Serializes request and sends it to GUI scope tab.

    Parameters:
        flow: mitmproxy.http.HTTPFlow object.
    """

    try:
        lprint(f"======\n"
               f"[INFO] Adding intercepted request to GUI/Web Interceptor Tab:\n{flow.request.data}", i=True)
        serialized_request = pickle.dumps(flow.request.data)

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((RUNNING_CONFIG["proxy_host_address"],
                           RUNNING_CONFIG["back_front_request_to_intercept_port"]))
                s.sendall(serialized_request)

        except Exception as e:
            lprint(f"******\n[ERROR] Error occured while sending request to GUI/Web Interceptor Tab: {e}")
            traceback.print_exc()
            lprint("[INFO] Resuming HTTP(S) flow due to above error.", i=True)
            flow.resume()

    except Exception as e:
        lprint(f"******\n[ERROR] Error while serialization when adding it to GUI/Web Interceptor Tab: {e}")
        traceback.print_exc()
        lprint("[INFO] Resuming HTTP(S) flow due to above error.", i=True)
        flow.resume()


class WebRequestInterceptor:
    """
    A Web Request Interceptor backend logic.

    Acts as a bridge between mitmproxy and the rest of the program.
    """

    def __init__(self):
        """
        Initializes Web Request Interceptor class.
        """
        self.loop = asyncio.new_event_loop()
        self.start_async_servers()
        self.scope = []
        self.intercepting = False

    def request(self, flow: mitmproxy.http.HTTPFlow) -> None:
        """
        Method made for mitmproxy process, triggered when new HTTPFlow is created.
        It acts as a bridge between mitmproxy and the rest of the program.
        It checks if the Web Interceptor state is on to intercept the flow.

        Parameters:
            flow: mitmproxy.http.HTTPFlow object.
        """
        request = flow.request
        if self.intercepting:
            lprint(f"======\n[INFO] Processing request to {request.host}", i=True)
            flow.intercept()

            def extract_domain(full_string) -> str:
                """
                Extracts the domain from a string of the format `ads.google.com	`.
                It returns an empty string if the input is malformed.

                Parameters:
                    full_string (str): The full string containing subdomains and domain.

                Returns:
                    str: The extracted domain (e.g., `google.com`).
                """
                parts = full_string.split('.')
                if len(parts) >= 2:
                    domain = '.'.join(parts[-2:])
                    return domain
                return ""

            if "mozilla.org" in request.host or "lencr.org" in request.host:
                lprint(f"Flow recognized as a telemetry request to mozilla.org / lencr.org."
                       f"Resuming HTTP(S) flow.", i=True)
                flow.request = Request.make(
                    method="GET",
                    url="https://google.com",
                    content="",
                    headers={"Accept": "*/*"}
                )
                flow.resume()

            elif not self.scope or request.host in self.scope or extract_domain(request.host) in self.scope:
                if not self.scope:
                    lprint("[INFO] Web Request Interceptor's scope is currently empty.", i=True)
                else:
                    lprint(f"[INFO] Current Web Request Interceptor's scope: {self.scope}", i=True)
                lprint(f"[INFO] Request to {request.host} has been intercepted.")
                send_request_to_intercept_tab(flow)
                self.receive_data_from_frontend(flow)

            else:
                lprint(f"[INFO] Request to {request.host} is out of "
                       f"current Interceptor's scope: {self.scope}", i=True)
                lprint(f"[INFO] Passing request to {request.host} throught.", i=True)
                if flow.intercepted:
                    flow.resume()
        else:
            lprint(f"======\n[INFO] Passing through request to {request.host}")

    # noinspection PyMethodMayBeStatic
    def response(self, flow: mitmproxy.http.HTTPFlow) -> None:
        """
        Method made for mitmproxy process, triggered when new HTTPFlow is created.
        It acts as a bridge between mitmproxy and the rest of the program.
        This method serializes list of flow.reqeust and flow.response and add it to GUI/HTTP Traffic tab.

        Parameters:
            flow: mitmproxy.http.HTTPFlow object.
        """

        if flow.response is not None:
            flow_tab = [flow.request, flow.response]
            lprint(f"======\n[INFO] Adding request with response to GUI/HTTP Traffic Tab:\n{flow_tab}", h=True)
        else:
            flow_tab = flow.request
            lprint(f"======\n[INFO] Adding sole request to GUI/HTTP Traffic Tab:\n{flow_tab}", h=True)

        try:
            serialized_flow = pickle.dumps(flow_tab)

            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((RUNNING_CONFIG["proxy_host_address"],
                               RUNNING_CONFIG["back_front_request_to_traffic_port"]))
                    s.sendall(serialized_flow)

            except Exception as e:
                lprint(f"******\n[ERROR] Error while adding HTTP flow to GUI/HTTP Traffic Tab: {e}")
                traceback.print_exc()

        except Exception as e:
            lprint(f"\n[ERROR] Failure while serialization HTTP flow to add it to GUI/HTTP Traffic Tab: {e}")
            traceback.print_exc()

    def start_async_servers(self) -> None:
        """
        Starts the asyncio servers in a separate thread to asynchronously listen and handle instructions:
         - a Web Request Interceptor's state change 
         - a Web Request Interceptor's scope update
        """
        def run_servers():
            asyncio.set_event_loop(self.loop)
            tasks = [
                self.listen_for_intercept_button(),
                self.listen_for_scope_update()
            ]
            self.loop.run_until_complete(asyncio.gather(*tasks))

        threading.Thread(target=run_servers, daemon=True).start()

    async def listen_for_intercept_button(self) -> None:
        """
        Asynchronously listens to the Web Request Interceptor state changes from the frontend.
        """
        async def toggle_intercept(reader, writer) -> None:
            """
            Handles the Web Request Interceptor state changes received from the frontend.

            Parameters:
                reader: asyncio.StreamReader object.
                writer: asyncio.StreamWriter object.
            """
            data = await reader.read(4096)
            if data:
                lprint(f"======\n[INFO] Received instruction to change Request Interceptor state.", i=True)
                if data.decode('utf-8').lower() == 'false':
                    new_state = False
                else:
                    new_state = True
                self.intercepting = new_state
            lprint(f"[INFO] Current Request Interceptor state: {self.intercepting}", i=True)
            writer.close()
            await writer.wait_closed()

        server = await asyncio.start_server(
            toggle_intercept,
            RUNNING_CONFIG["proxy_host_address"],
            RUNNING_CONFIG["front_back_intercept_toggle_port"]
        )
        async with server:
            await server.serve_forever()

    async def listen_for_scope_update(self) -> None:
        """
        Asynchronously listens to Web Request Interceptor scope updates from the frontend.
        """
        async def scope_update(reader, writer) -> None:
            """
            Handles incoming scope updates received from the frontend.

            Parameters:
                reader: asyncio.StreamReader object.
                writer: asyncio.StreamWriter object.
            """
            data = await reader.read(4096)
            
            if data:
                lprint(f"======\n[INFO] Received instruction to update scope of Request Interceptor.", i=True)
                operation, *hostnames = pickle.loads(data)
                
                if operation == "add":
                    for hostname in hostnames:
                        domain = hostname
                        self.scope.append(domain)
                        lprint(f"[INFO] Host {domain} added to the scope.", i=True)
                        
                elif operation == "remove":
                    for hostname in hostnames:
                        domain = hostname
                        try:
                            self.scope.remove(domain)
                            lprint(f"[INFO] Host {domain} removed from scope.", i=True)
                            
                        except ValueError:
                            lprint(f"[INFO] Attempted to remove {domain} from scope, "
                                   f"but could not be found there.", i=True)
                            
                elif operation == "clear":
                    self.scope.clear()
                    lprint("[INFO]Scope cleared.", i=True)
                lprint(f"[INFO] Current Web Request Interceptor's scope: {self.scope}", i=True)
                
            writer.close()
            await writer.wait_closed()

        server = await asyncio.start_server(
            scope_update,
            RUNNING_CONFIG["proxy_host_address"],
            RUNNING_CONFIG["front_back_scope_update_port"]
        )
        async with server:
            await server.serve_forever()

    def receive_data_from_frontend(self, flow) -> None:
        """
        Receives request from GUI when forward button in scope is pressed.

        Parameters:
            flow: mitmproxy.http.HTTPFlow object.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((RUNNING_CONFIG["proxy_host_address"],
                    RUNNING_CONFIG["front_back_data_port"]))
            s.listen()
            conn, addr = s.accept()

            with conn:
                serialized_data = conn.recv(4096)

                if serialized_data:
                    deserialized_data = pickle.loads(serialized_data)
                    lprint(f"======\n[INFO] Received data from GUI.", i=True)

                    if deserialized_data[0] == "forward":
                        lprint("[INFO] Handling an instruction to forward the last intercepted request.", i=True)

                        if isinstance(deserialized_data[1], Request):
                            lprint(f"[INFO] Forwarding intercepted request:\n{flow.request.data}", i=True)
                            flow.request.data = deserialized_data[1].data

                        flow.resume()

                    elif deserialized_data[0] == "drop":
                        lprint("[INFO] Handling an instruction to drop the last intercepted request.", i=True)

                        target_url = "http://localhost:8080/en/dropped.html"

                        flow.request.host = "localhost"
                        flow.request.port = 8080
                        flow.request.method = "GET"
                        flow.request.url = target_url
                        flow.request.version = "HTTP/1.1"
                        flow.resume()

                        self.intercepting = False

                    elif deserialized_data[0] == "resume":
                        lprint("[INFO] Received resume instruction.\nResuming current flow.", i=True)
                        flow.resume()

                    else:
                        lprint("[ERROR] Received unknown instruction.\nResuming current flow.", i=True)


addons = [
    WebRequestInterceptor()
]

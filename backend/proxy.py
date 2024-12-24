import pickle
import mitmproxy.http
import socket
# noinspection PyUnresolvedReferences
from mitmproxy import ctx
# noinspection PyUnresolvedReferences
from mitmproxy.http import Request, Response, HTTPFlow
import asyncio
import threading
from utils.get_domain import extract_domain
from config import RUNNING_CONFIG


def send_flow_to_http_trafic_tab(flow):
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
            s.connect((RUNNING_CONFIG["proxy_host_address"], RUNNING_CONFIG["back_front_request_to_traffic_port"]))
            s.sendall(serialized_flow)
    except Exception as e:
        print(f"\nError while sending request to http tab: {e}")


def send_request_to_intercept_tab(request):
    """
    Serializes request and sends it to GUI scope tab.
    """
    try:
        print(f"----\nSending intercepted request to Frontend:\n{request.data}")
        serialized_request2 = pickle.dumps(request)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((RUNNING_CONFIG["proxy_host_address"], RUNNING_CONFIG["back_front_request_to_intercept_port"]))
                s.sendall(serialized_request2)
        except Exception as e:
            print(f"\nError while sending request to scope tab: {e}")
    except Exception as e:
        print(f"\nError while serialization before sending to scope tab: {e}")


def receive_forwarded_request(flow):
    """
    Receives request from GUI when forward button in scope is pressed.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((RUNNING_CONFIG["proxy_host_address"], RUNNING_CONFIG["front_back_forward_request_port"]))
        s.listen()

        conn, addr = s.accept()
        with conn:
            serialized_reqeust = conn.recv(4096)
            if serialized_reqeust:
                deserialized_request = pickle.loads(serialized_reqeust)
                flow.request.data = deserialized_request.data
                print(f"----\nForwarding intercepted request from Frontend:\n{flow.request.data}")
                if flow.intercepted:
                    flow.resume()


class WebRequestInterceptor:
    def __init__(self):
        """
        Initializes Web Request Interceptor backend logic.
        Acts as a bridge between mitmproxy and the rest of the program.
        """
        # TODO BACKEND: Resuming the flow (self.current_flow), while dropping the request or turning interception off on intercepted request doesn't work due to asynch logic.
        # TODO BACKEND: Filter with subdomains, not with domain only
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
        """
        request = flow.request
        self.current_flow = flow
        if self.intercept_state:
            print(f"*****\nINTERCEPTED REQUEST TO {request.host}")
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
            elif not self.scope:
                print(f"*****\nEMPTY SCOPE: REQUEST TO {request.host} INFO:"
                      f"\n  Hostname from the request: {extract_domain(request.host)}"
                      f"\n  Hostnames in the current scope: {self.scope}")
                send_request_to_intercept_tab(request)
                receive_forwarded_request(flow)
            elif extract_domain(request.host) not in self.scope:
                print(f"*****\nREQUEST NOT IN SCOPE: REQUEST TO {request.host} INFO:"
                      f"\n  Hostname from the request: {extract_domain(request.host)}"
                      f"\n  Hostnames in the current scope: {self.scope}")
                if flow.intercepted:
                    flow.resume()
            else:
                print(f"*****\nREQUEST IN SCOPE: REQUEST TO {request.host} INFO:"
                      f"\n  Hostname from the request: {extract_domain(request.host)}"
                      f"\n  Hostnames in the current scope: {self.scope}")
                send_request_to_intercept_tab(request)
                receive_forwarded_request(flow)
        else:
            print(f"*****\nPASSING REQUEST TO {request.host}")

    # noinspection PyMethodMayBeStatic
    def response(self, flow: mitmproxy.http.HTTPFlow):
        """
        Method made for mitmproxy process, triggered when new HTTPFlow is created.
        Acts as a bridge between mitmproxy and the rest of the program.
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
                self.listen_for_kill_flow(),
                self.listen_for_intercept_button(),
            ]
            self.loop.run_until_complete(asyncio.gather(*tasks))

        thread = threading.Thread(target=run_servers, daemon=True)
        thread.start()

    async def listen_for_intercept_button(self):
        """
        Asynchronously receives listens for Web Interceptor state changes from the frontend.
        """
        server = await asyncio.start_server(
            self.handle_toggle_intercept, RUNNING_CONFIG["proxy_host_address"], RUNNING_CONFIG["front_back_intercept_toggle_port"]
        )
        async with server:
            await server.serve_forever()

    async def handle_toggle_intercept(self, reader, writer):
        """
        Handles the Web Interceptor state changes from the frontend.
        """
        # TODO BACKEND: Fix resuming intercepted traffic if toggling the interception off
        data = await reader.read(4096)
        if data:
            new_state = data.decode('utf-8').lower() == 'true'
            self.intercept_state = new_state
            if not self.intercept_state:
                # self.backup = self.scope
                # self.scope = []
                if self.current_flow.intercepted:
                    self.current_flow.resume()
            else:
                pass
                # self.scope = self.backup.copy()
        print(f"Intercepting state: {self.intercept_state}")
        writer.close()
        await writer.wait_closed()

    async def listen_for_scope_update(self):
        """
        Asynchronously receives and adds hostname to scope.
        """
        server = await asyncio.start_server(
            self.handle_scope_update, RUNNING_CONFIG["proxy_host_address"], RUNNING_CONFIG["front_back_scope_update_port"]
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
                    domain = extract_domain(hostname)
                    self.scope.append(domain)
                    print(f"Host {domain} added to the scope.")
            elif operation == "remove":
                for hostname in hostnames:
                    domain = extract_domain(hostname)
                    try:
                        self.scope.remove(domain)
                        print(f"Host {domain} removed from scope.")
                    except ValueError:
                        print(f"Attempted to remove {domain} from scope, but could not be found there.")
            elif operation == "clear":
                self.scope.clear()
                print("Scope cleared.")
        print(f"Current scope: {self.scope}")
        writer.close()
        await writer.wait_closed()

    async def listen_for_kill_flow(self):
        """
        Asynchronously listens for flow kill requests.
        """
        server = await asyncio.start_server(
            self.handle_kill_request, RUNNING_CONFIG["proxy_host_address"], RUNNING_CONFIG["front_back_drop_request_port"]
        )
        async with server:
            await server.serve_forever()

    async def handle_kill_request(self, reader, writer):
        """
        Handles incoming requests to kill a flow.
        """
        data = await reader.read(4096)
        if data:
            # TODO BACKEND: Fix flow kill
            # bad_request = Request.make(
            #     method="GET",
            #     url="https://google.com",
            #     content="",
            #     headers={"Accept": "*/*"}
            # )
            self.current_flow.request.host = "google.com"
            self.current_flow.request.url = "https://google.com"
            self.current_flow.request.port = 443
            self.current_flow.request.scheme = "https"
            self.current_flow.resume()
            if not self.current_flow.intercepted:
                print(f"----\nReceived request to kill flow")
        writer.close()
        await writer.wait_closed()


addons = [
    WebRequestInterceptor()
]

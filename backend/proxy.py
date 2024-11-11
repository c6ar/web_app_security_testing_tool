import mitmproxy.http
import socket
from datetime import datetime


HOST = '127.0.0.1'  
PORT_SERVER = 65432    
PORT_GUI = 65433    

class Request:
    def __init__(self, time, type, direction, method, url, status_code, content):
        self.time = time
        self.type = type
        self.direction = direction
        self.method = method
        self.url = url
        self.status_code = status_code
        self.content = content

    def __str__(self):
        return (
            f"Request Information:\n"
            f"  Time: {self.time}\n"
            f"  Type: {self.type}\n"
            f"  Direction: {self.direction}\n"
            f"  Method: {self.method}\n"
            f"  URL: {self.url}\n"
            f"  Status Code: {self.status_code}\n"
            f"  Content: {self.content.decode('ascii', errors='replace')}"
        )

class WebRequestInterceptor:
    telemetry_domains = ["mozilla.org", "chrome.com", "telemetry"]
    def __init__(self):
        self.forward_flag = False
        self.drop_flag = False

    def request(self, flow: mitmproxy.http.HTTPFlow):
        request = flow.request
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        
        if any(domain in request.url for domain in self.telemetry_domains):
            return  
        
        req = Request(
            time=time,
            type=request.scheme.upper(),
            direction="outgoing",
            method=request.method,
            url=request.url,
            status_code=None,  
            content=request.content
        )
        print(req)

        
        self.send_request_to_gui(str(req))
        flow.intercept()
        self.forward_request(flow)

    def send_request_to_gui(self, request_info):
        """Wysyła żądanie do aplikacji GUI przez gniazdo"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, PORT_SERVER))
                s.sendall(request_info.encode('utf-8'))
        except Exception as e:
            print(f"Błąd przy wysyłaniu żądania do GUI: {e}")
    def forward_request(self, flow):
        """
        Funkcja do odbierania czy nacisnięcia przycisku Forward.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT_GUI))
            s.listen()

          
            conn, addr = s.accept()
            with conn:
                    # Odbieramy dane i interpretujemy je jako boolean (True/False)
                    data = conn.recv(1024).decode('utf-8')
                    self.forward_flag = (data == 'True')  # Sprawdzamy, czy dane to 'True'
                    self.handle_flow_state(flow)
                    self.forward_flag = False
                    
    def handle_flow_state(self,flow):
        if self.forward_flag:
            print(self.forward_flag)
            flow.resume()
        elif self.drop_flag:
            flow.kill()

addons = [
    WebRequestInterceptor()
]

import urllib.parse
import mitmproxy.http

import socket

from pyexpat.errors import messages

import dataParse as dp


HOST = '127.0.0.1'  
PORT_SERVER = 65432    
PORT_GUI = 65433    


class WebRequestInterceptor:
    def __init__(self):
        self.telemetry_domains = ["overthewire.org"]
        self.forward_flag = False

    def request(self, flow: mitmproxy.http.HTTPFlow):
        """
        Droga każdego requesta (filtr, drop/forward)
        """
        request = flow.request

#TODO proxy włączone cały czas, przycisk intercept wyłącza filtrowanie z telemetry domains
        if any(domain not in request.url for domain in self.telemetry_domains):
            return

        req = dp.convert_to_http_message(flow.request.data)

        self.send_request_to_gui(req)
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
                    data = conn.recv(1024).decode('utf-8')
                    self.forward_flag = (data.splitlines()[0] == "True")
                    if self.forward_flag:
                        raw_http_message = data.splitlines()[1:]
                        flow.request = dp.parse_http_message("\n".join(raw_http_message))#mitmproxy.http.Request.make(http_message, url)
                        flow.resume()
                    else:
#TODO zmiana request data na podstawioną stronę (request dropped)
                        flow.kill()
                    self.forward_flag = False

    def change_request_data(self, flow, request_data):
        flow.request.method = request_data['method']
        flow.request.http_version = request_data['http_version']
        flow.request.path = request_data['path']
        flow.request.headers.clear()
        for key, value in request_data['headers']:
            flow.request.headers[key] = value
        flow.request.text = request_data['content'].decode('utf-8')


addons = [
    WebRequestInterceptor()
]

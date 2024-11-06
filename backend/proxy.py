import mitmproxy.http
from datetime import datetime

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

    """
    Tymczasowe filtrowanie niechcianych domen
    """
    telemetry_domains = ["mozilla.org", "chrome.com", "telemetry", "firefox.com"]

    def request(self, flow: mitmproxy.http.HTTPFlow):
        request = flow.request
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Sprawdź, czy URL zawiera jeden z filtrów domen telemetrycznych
        if any(domain in request.url for domain in self.telemetry_domains):
            return  # Ignorujemy żądanie

        req = Request(
            time=time,
            type=request.scheme.upper(),
            direction="outgoing",
            method=request.method,
            url=request.url,
            status_code=None,  
            content=request.content
        )
        flow.intercept()
        print(req)
        
        confirmation = int(input(f"Chcesz wysłać żądanie na adres {request.url}? (1 - Tak, 0 - Nie): "))
        
        if confirmation == 1:
            edit_request = int(input("Czy chcesz edytować treść żądania? (1 - Tak, 0 - Nie): "))
            if edit_request:
                print("Obecna treść:", req.content.decode('ascii', errors='replace'))
                new_content = input("Wprowadź nową treść: \n")
                flow.request.text = new_content  # Zmiana treści żądania
            flow.resume()  # Wznowienie przepływu
        else:
            print("Anulowano żądanie")
            flow.kill()  # Przerwanie żądania

    def response(self, flow: mitmproxy.http.HTTPFlow):
        response = flow.response
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Sprawdź, czy URL żądania zawiera jeden z filtrów domen telemetrycznych
        if any(domain in flow.request.url for domain in self.telemetry_domains):
            return  # Ignorujemy odpowiedź

        req = Request(
            time=time,
            type=flow.request.scheme.upper(),
            direction="incoming",
            method=flow.request.method,
            url=flow.request.url,
            status_code=response.status_code,
            content=response.content
        )

        print(req)
        flow.intercept()

        # Poprawione: używamy `flow.request.url` zamiast `response.url`
        confirmation = int(input(f"Chcesz wysłać odpowiedź z adresu {flow.request.url}? (1 - Tak, 0 - Nie): "))
        if confirmation == 1:
            edit_response = int(input("Czy chcesz edytować treść odpowiedzi? (1 - Tak, 0 - Nie): "))
            if edit_response == 1:
                print("Obecna treść:", req.content.decode('ascii', errors='replace'))
                new_content = input("Wprowadź nową treść odpowiedzi: \n")
                flow.response.text = new_content  # Zmiana treści odpowiedzi
            flow.resume()  # Wznowienie przepływu
        else:
            print("Anulowano odpowiedź")
            flow.kill()  # Przerwanie odpowiedzi


addons = [
    WebRequestInterceptor()
]

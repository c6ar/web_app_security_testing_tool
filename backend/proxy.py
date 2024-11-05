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
    def request(self, flow: mitmproxy.http.HTTPFlow):
        request = flow.request
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        
        req = Request(
            time=time,
            type=request.scheme.upper(),
            direction="outgoing",
            method=request.method,
            url=request.url,
            status_code=None,  
            content = request.content
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


addons = [
    WebRequestInterceptor()
]
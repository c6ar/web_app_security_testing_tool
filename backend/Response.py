from mitmproxy.http import Response
import pickle

class Response2(Response):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    #def return_http_message
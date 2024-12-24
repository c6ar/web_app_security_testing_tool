# backend/tester.py
import requests


class ManualTester:
    def __init__(self):
        self.session = requests.Session()  # pozwala na utrzymanie sesji

    def send_request(self, method, url, headers=None, data=None):
        response = self.session.request(method=method, url=url, headers=headers, data=data)
        return response


class Fuzzer:
    def __init__(self, payload_list):
        self.payload_list = payload_list

    def fuzz(self, url, headers=None, param_name=None):
        results = []
        for payload in self.payload_list:
            data = {param_name: payload}
            response = requests.post(url, headers=headers, data=data)
            results.append((payload, response.status_code, response.text))
        return results

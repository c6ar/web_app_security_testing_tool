import urllib
import requests
from bs4 import BeautifulSoup
import re


def extract_key_value_pairs(data):
    """
    Extracts key-value pairs from a string formatted as key=value&key2=value2 and returns a dictionary.

    :param data: str, the input string to parse
    :return: dict, a dictionary containing the extracted key-value pairs
    """
    parsed_data = urllib.parse.parse_qs(data, keep_blank_values=True)
    return {key: values[0] if values else '' for key, values in parsed_data.items()}

def parse_http_message(http_message):
    """
    Parse an HTTP message into method, URL, and headers.
    :param http_message: str, the raw HTTP message
    :return: tuple (method, path, headers)
    """
    # TODO protection for bad input (eg. 'sdf')
    try:
        headers_body, body = http_message.split("\r\n\r\n")
    except Exception:
        headers_body = http_message
        body = ""

    lines = headers_body.splitlines()
    request_line = lines[0]
    header_lines = lines[1:]
    data = extract_key_value_pairs(body)
    method, path, http_version = request_line.split(" ")

    headers = {}
    for line in header_lines:
        if ": " in line:
            key, value = line.split(": ", 1)
            headers[key.strip()] = value.strip()

    return method, path, headers, data

def extract_base_url(http_message):
    """
    Extract the base URL from the HTTP message.
    :param http_message: str, the raw HTTP message
    :return: str, the base URL
    """
    lines = http_message.strip().split("\r\n")
    for line in lines:
        if line.lower().startswith("host: "):
            host = line.split(": ", 1)[1]
    # TODO http/https from http message? not necessary, would be nice
    # may not be needed if  all repeater tabs will have url from mitmproxy requests
            return f"http://{host}"  # Assume HTTPS by default
    raise ValueError("Host header not found in HTTP message.")

def send_http_message(http_message, real_url=None):
    """
    Send an HTTP request based on the provided HTTP message.
    :param http_message: str, the raw HTTP message
    :param url: str, url of a request
    :return: requests.Response, the response object
    """
    method, path, headers, data = parse_http_message(http_message)
    base_url = extract_base_url(http_message)

    # TODO backup url not working, may not be needed if  all repeater tabs will have url from mitmproxy requests
    if real_url is None:
        url = f"{base_url}{path}"
    else: url = real_url

    if method.upper() == "GET":
        response = requests.get(url, headers=headers)
    elif method.upper() == "POST":
        response = requests.post(url, headers=headers, data=data)
    else:
        raise ValueError(f"HTTP method {method} is not supported.")

    return response

def process_response(response):
    """
    Process the HTTP response using BeautifulSoup if it is HTML/XML.
    :param response: requests.Response
    :return: str, processed content or raw content
    """
    if response.ok:
        content_type = response.headers.get('Content-Type', '')
        if 'html' in content_type or 'xml' in content_type:
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup.prettify()  # Pretty-print the parsed HTML/XML
        return response.content  # Return raw content for non-HTML/XML
    return "Bad Request"

def replace_values(values, http_message=str):
    """
       Replaces placeholder variables in the HTTP message marked with §var_name§ with values from the `values` list.

       Args:
           values (list): List of strings to replace the placeholders.
           http_message (str): HTTP request message with placeholders.

       Returns:
           str: The modified HTTP message with placeholders replaced.
    """

    placeholders = re.findall(r'\§(.*?)\§', http_message)

    if len(placeholders) > len(values):
        raise ValueError("Not enough values provided to replace all placeholders.")

    for i, placeholder in enumerate(placeholders):
        if i < len(values):
            http_message = http_message.replace(f'\u00a7{placeholder}\u00a7', values[i], 1)

    return http_message
# Example usage
http_message_GET = """GET /Pe5gM9R0s-OCS2DfKecIG72P_fwfB8I2BSbC1obg0oM=.5716.jpg HTTP/2.0
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0
accept: image/avif,image/webp,image/png,image/svg+xml,image/*;q=0.8,*/*;q=0.5
accept-language: pl,en-US;q=0.7,en;q=0.3
accept-encoding: gzip, deflate, br, zstd
sec-fetch-dest: image
sec-fetch-mode: no-cors
sec-fetch-site: cross-site
if-modified-since: Thu, 17 Oct 2024 22:36:34 GMT
if-none-match: \"541289b611ccf85489757453b19496f5\"
priority: u=4, i
host: example.com"""
http_message_POST = """POST / HTTP/1.1
Host: natas6.natas.labs.overthewire.org
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: pl,en-US;q=0.7,en;q=0.3
Accept-Encoding: gzip, deflate
Content-Type: application/x-www-form-urlencoded
Content-Length: 36
Origin: http://natas6.natas.labs.overthewire.org
Authorization: Basic bmF0YXM2OjBSb0p3SGRTS1dGVFlSNVd1aUFld2F1U3VOYUJYbmVk
Connection: keep-alive
Referer: http://natas6.natas.labs.overthewire.org/
Upgrade-Insecure-Requests: 1
Priority: u=0, i
Content-Length: 36


secret=&submit=Wy%C5%9Blij+zapytanie"""

# response = send_http_message(http_message_POST)
#
# output = process_response(response)
# print(output)


print(replace_values(['jeden', 'dwa'], """POST / HTTP/1.1
Host: natas6.natas.labs.overthewire.org
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,/;q=0.8
Accept-Language: pl,en-US;q=0.7,en;q=0.3
Accept-Encoding: gzip, deflate
Content-Type: application/x-www-form-urlencoded
Content-Length: 36
Origin: http://natas6.natas.labs.overthewire.org/
Authorization: Basic bmF0YXM2OjBSb0p3SGRTS1dGVFlSNVd1aUFld2F1U3VOYUJYbmVk
Connection: keep-alive
Referer: http://natas6.natas.labs.overthewire.org/
Upgrade-Insecure-Requests: 1
Priority: u=0, i
Content-Length: 36


secret=§var0§&submit=§var0§"""))
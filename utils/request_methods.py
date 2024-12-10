import requests
from bs4 import BeautifulSoup
import string

def sanitize_header_value(value):
    # Allow only printable ASCII characters
    allowed_chars = string.printable
    return ''.join(c for c in value if c in allowed_chars)

def parse_http_message(http_message):
    """
    Parse an HTTP message into method, URL, and headers.
    :param http_message: str, the raw HTTP message
    :return: tuple (method, path, headers)
    """
    # Split headers and body
    parts = http_message.split("\n\n", 1)
    if len(parts) == 2:
        headers_body, body = parts
    else:
        headers_body = parts[0]
        body = ""

    # Split request line and headers
    lines = headers_body.splitlines()
    request_line = lines[0]
    header_lines = lines[1:]

    # Parse request line
    method, path, http_version = request_line.split(" ")

    # Parse headers
    headers = {}
    for line in header_lines:
        if ": " in line:
            key, value = line.split(": ", 1)
            headers[key.strip()] = value.strip()

    return method, path, headers


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
            return f"http://{host}"  # Assume HTTPS by default
    raise ValueError("Host header not found in HTTP message.")

def send_http_message(http_message):
    """
    Send an HTTP request based on the provided HTTP message.
    :param http_message: str, the raw HTTP message
    :return: requests.Response, the response object
    """
    # Parse the HTTP message
    method, path, headers = parse_http_message(http_message)
    # for key, value in headers.items():
    #     print(repr(value))
    # Extract the base URL
    base_url = extract_base_url(http_message)

    # Construct the full URL
    url = f"{base_url}{path}"

    # Send the HTTP request
    if method.upper() == "GET":
        response = requests.get(url, headers=headers)
    elif method.upper() == "POST":
        try:
            response = requests.post(url, headers=headers)
        except Exception as e:
            print(e)
    else:
        raise ValueError(f"HTTP method {method} is not supported.")

    return response

def sanitize_header_value(value):
    # Allow only printable ASCII characters
    allowed_chars = string.printable
    return ''.join(c for c in value if c in allowed_chars)

def process_response(response):
    """
    Process the HTTP response using BeautifulSoup if it is HTML/XML.
    :param response: requests.Response
    :return: str, processed content or raw content
    """
    content_type = response.headers.get('Content-Type', '')
    if 'html' in content_type or 'xml' in content_type:
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup.prettify()  # Pretty-print the parsed HTML/XML
    return response.content  # Return raw content for non-HTML/XML


# Example usage
http_message = """GET /Pe5gM9R0s-OCS2DfKecIG72P_fwfB8I2BSbC1obg0oM=.5716.jpg HTTP/2.0
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
host: example.com
"""

# response = send_http_message(http_message)
#
# # Process the response
# output = process_response(response)
# print(output)

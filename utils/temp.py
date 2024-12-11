# import re
#
# guiRequest = """GET /Pe5gM9R0s-OCS2DfKecIG72P_fwfB8I2BSbC1obg0oM=.5716.jpg HTTP/2.0
# user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0
# accept: image/avif,image/webp,image/png,image/svg+xml,image/*;q=0.8,*/*;q=0.5
# accept-language: pl,en-US;q=0.7,en;q=0.3
# accept-encoding: gzip, deflate, br, zstd
# sec-fetch-dest: image
# sec-fetch-mode: no-cors
# sec-fetch-site: cross-site
# if-modified-since: Thu, 17 Oct 2024 22:36:34 GMT
# if-none-match: "541289b611ccf85489757453b19496f5"
# priority: u=4, i
# te: trailers"""
#
#
# def reverse_convert_http_message(http_message):
#     # Split headers and content based on double newlines
#     if '\r\n\r\n' in http_message:
#         headers_part, content = http_message.split('\r\n\r\n', 1)
#     elif '\n\n' in http_message:
#         headers_part, content = http_message.split('\n\n', 1)
#     else:
#         headers_part, content = http_message, ''
#
#     # Split the HTTP message headers into lines
#     lines = headers_part.strip().split('\n')
#
#     # Extract the method, path, and HTTP version from the first line
#     method, path, version = lines[0].split()
#
#     # Initialize the headers dictionary
#     headers = []
#
#     # Parse the headers from the rest of the lines
#     for line in lines[1:]:
#         key, value = line.split(":", 1)
#         headers.append((key.strip().encode(), value.strip().encode()))
#
#     # Calculate the content length (use actual content length if Content-Length isn't explicitly given)
#     content_length = len(content)
#     content_bytes = content.encode()
#
#     # Update Content-Length header if it exists or add it if missing
#     content_length_set = False
#     for i, (key, value) in enumerate(headers):
#         if key.decode().lower() == 'content-length':
#             headers[i] = (key, str(content_length).encode())
#             content_length_set = True
#             break
#     if not content_length_set:
#         headers.append((b'Content-Length', str(content_length).encode()))
#
#     # Recreate the request data in the original format
#     request_data = (
#         f"RequestData(http_version=b'{version}', headers=Headers{headers}, "
#         f"content={content_bytes}, trailers=None, "
#         f"timestamp_start=0, timestamp_end=0, host='', port=0, method=b'{method}', "
#         f"scheme=b'http', authority=b'', path=b'{path}')"
#     )
#
#     return request_data
#
#
# print(guiRequest)
# print(80*'*')
# print(reverse_convert_http_message(guiRequest))
# print(80*'*')


#
# from mitmproxy import http
# import ast  # To safely evaluate string representations of Python objects
#
# class UpdateRequestContent:
#     def request(self, flow: http.HTTPFlow) -> None:
#         # The given RequestData string
#         request_data = """RequestData(
#             http_version=b'HTTP/2.0',
#             headers=Headers[
#                 (b'user-agent', b'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0'),
#                 (b'accept', b'image/avif,image/webp,image/png,image/svg+xml,image/*;q=0.8,*/*;q=0.5'),
#                 (b'accept-language', b'pl,en-US;q=0.7,en;q=0.3'),
#                 (b'accept-encoding', b'gzip, deflate, br, zstd'),
#                 (b'sec-fetch-dest', b'image'),
#                 (b'sec-fetch-mode', b'no-cors'),
#                 (b'sec-fetch-site', b'cross-site'),
#                 (b'if-modified-since', b'Thu, 17 Oct 2024 22:36:34 GMT'),
#                 (b'if-none-match', b'"541289b611ccf85489757453b19496f5"'),
#                 (b'priority', b'u=4, i'),
#                 (b'te', b'trailers'),
#                 (b'Content-Length', b'0')
#             ],
#             content=b'',
#             trailers=None,
#             timestamp_start=0,
#             timestamp_end=0,
#             host='',
#             port=0,
#             method=b'GET',
#             scheme=b'http',
#             authority=b'',
#             path=b'/Pe5gM9R0s-OCS2DfKecIG72P_fwfB8I2BSbC1obg0oM=.5716.jpg'
#         )"""
#
#         # Safely evaluate the string to a dictionary-like structure
#         request_data_dict = ast.literal_eval(
#             request_data.replace("RequestData", "").strip()
#         )
#
#         # Update the flow.request attributes
#         flow.request.method = request_data_dict.get("method", flow.request.method)
#         flow.request.scheme = request_data_dict.get("scheme", flow.request.scheme)
#         flow.request.http_version = request_data_dict.get("http_version", flow.request.http_version)
#         flow.request.host = request_data_dict.get("host", flow.request.host)
#         flow.request.port = request_data_dict.get("port", flow.request.port)
#         flow.request.path = request_data_dict.get("path", flow.request.path)
#
#         # Update headers
#         headers = request_data_dict.get("headers", [])
#         flow.request.headers.clear()  # Clear existing headers
#         for header in headers:
#             flow.request.headers[header[0].decode()] = header[1].decode()
#
#         # Update content
#         flow.request.content = request_data_dict.get("content", b"")
#
# addons = [UpdateRequestContent()]


import re
from collections import namedtuple

# # Define the required namedtuple for headers
# Headers = namedtuple('Headers', ['key', 'value'])
#
#
# def convert_to_request_data(input_str):
#     # Regular expressions for extracting relevant parts
#     method_pattern = re.compile(r'^(GET|POST|PUT|DELETE)\s')
#     version_pattern = re.compile(r'HTTP/\d\.\d')
#     host_pattern = re.compile(r'Host:\s([^\r\n]+)')
#     headers_pattern = re.compile(r'([A-Za-z\-]+):\s([^\r\n]+)')
#
#     # Extract method, HTTP version, and path from the request line
#     method_match = method_pattern.match(input_str)
#     version_match = version_pattern.search(input_str)
#     request_line_end = input_str.find('\r\n')  # end of the request line
#     path = input_str[method_match.end():request_line_end].strip().split(' ')[1] if method_match else ''
#
#     # Extract headers
#     headers = []
#     headers_matches = headers_pattern.findall(input_str)
#     for header, value in headers_matches:
#         headers.append(Headers(key=header.encode(), value=value.encode()))
#
#     # Extract Host header value
#     host_match = host_pattern.search(input_str)
#     host = host_match.group(1) if host_match else ''
#
#     # Assign default values to the other fields (these may vary based on real context)
#     timestamp_start = 1732646854.2753174  # Example timestamp
#     timestamp_end = 1732646854.2753174  # Example timestamp
#     content = b''  # Assuming no content for simplicity
#     trailers = None  # No trailers provided in this case
#     port = 80  # Default HTTP port
#     scheme = b'http'  # Default HTTP scheme
#     authority = b''  # Not provided in the input
#     path = path.encode()  # Path extracted from the request line
#
#     # Construct the output string in the desired format
#     headers_str = ', '.join([f"(b'{header.key.decode()}', b'{header.value.decode()}')" for header in headers])
#     return f"RequestData(http_version=b'{version_match.group(0)}', " \
#            f"headers=[{headers_str}], " \
#            f"content=b'{content.decode()}', trailers=None, " \
#            f"timestamp_start={timestamp_start}, timestamp_end={timestamp_end}, " \
#            f"host='{host}', port={port}, " \
#            f"method=b'{method_match.group(1)}', scheme=b'{scheme.decode()}', " \
#            f"authority=b'{authority.decode()}', path=b'{path.decode()}')"
#
#
# # Example usage:
# input_str = '''GET / HTTP/1.1
# Host: natas6.natas.labs.overthewire.org
# User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0
# Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
# Accept-Language: pl,en-US;q=0.7,en;q=0.3
# Accept-Encoding: gzip, deflate
# Connection: keep-alive
# Upgrade-Insecure-Requests: 1
# Priority: u=0, i'''
#
# result = convert_to_request_data(input_str)
# print(result)


def parse_http_message(http_message, flow):
    """
    Parses an HTTP message string and updates the flow.request object.
    """
    # Extract HTTP version, headers, content, method, path, and scheme
    version_match = re.search(r"http_version=b'(.*?)'", http_message)
    headers_match = re.search(r"headers=Headers\[(.*?)\]", http_message, re.DOTALL)
    content_match = re.search(r"content=b'(.*?)'", http_message)
    method_match = re.search(r"method=b'(.*?)'", http_message)
    path_match = re.search(r"path=b'(.*?)'", http_message)
    scheme_match = re.search(r"scheme=b'(.*?)'", http_message)
    authority_match = re.search(r"authority=b'(.*?)'", http_message)

    # Extract components
    http_version = version_match.group(1) if version_match else 'HTTP/1.1'
    raw_headers = headers_match.group(1) if headers_match else ''
    content = content_match.group(1).encode('utf-8') if content_match else b''
    method = method_match.group(1).decode('utf-8') if method_match else 'GET'
    path = path_match.group(1).decode('utf-8') if path_match else '/'
    scheme = scheme_match.group(1).decode('utf-8') if scheme_match else 'http'
    authority = authority_match.group(1).decode('utf-8') if authority_match else ''

    # Parse headers into a list of tuples
    headers = []
    for header_match in re.finditer(r"\(b'(.*?)', b'(.*?)'\)", raw_headers):
        headers.append((header_match.group(1), header_match.group(2)))

    # Update the flow.request object directly
    flow.request.method = method
    flow.request.scheme = scheme
    flow.request.host = authority
    flow.request.port = 80 if scheme == 'http' else 443
    flow.request.path = path
    flow.request.http_version = http_version
    flow.request.headers.clear()
    for key, value in headers:
        flow.request.headers[key] = value
    flow.request.content = content
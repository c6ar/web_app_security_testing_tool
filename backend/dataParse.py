import re

def convert_to_http_message(request_data):
    """
    backend/proxy -> frontend/proxy
    Converts RequestData object to an HTTP message string.
    """

    # Start with the request line
    method = request_data.method.decode('utf-8')
    path = request_data.path.decode('utf-8')
    version = request_data.http_version.decode('utf-8')
    http_message = f"{method} {path} {version}\r\n"

    # Add headers



    for key, value in request_data.headers.items():
        print(f"{key}: {value}")
    for key, value in request_data.headers.items():
        http_message += f"{key}: {value}\r\n"

    # Add content if present
    print(request_data)
    if request_data.content:
        content_length = len(request_data.content)
        http_message += f"Content-Length: {content_length}\r\n\r\n"
        http_message += request_data.content.decode('utf-8')
    else:
        http_message += "\r\n"  # End of headers

    return http_message

def parse_http_message(http_message, flow):
    """
    Parses an HTTP message string to reconstruct the RequestData object.
    """
    from collections import namedtuple

    # Define Headers and RequestData to mimic the input structure
    Headers = list  # Represent headers as a list of tuples
    RequestData = namedtuple(
        'RequestData',
        [
            'http_version', 'headers', 'content', 'trailers', 'timestamp_start',
            'timestamp_end', 'host', 'port', 'method', 'scheme', 'authority', 'path'
        ]
    )

    # Split HTTP message into lines and parse
    lines = http_message.split("\r\n")
    request_line = lines[0]
    method, path, version = re.match(r"(\S+) (\S+) (HTTP/\d\.\d)", request_line).groups()

    # Parse headers
    headers = []
    idx = 1
    while idx < len(lines) and lines[idx]:
        header_line = lines[idx]
        if ":" in header_line:
            key, value = re.match(r"(.*?):\s*(.*)", header_line).groups()
            headers.append((key.encode('utf-8'), value.encode('utf-8')))
        idx += 1

    # Parse content (if any)
    content = b""
    if idx + 1 < len(lines):
        content = "\r\n".join(lines[idx + 1:]).encode('utf-8')

    # Reconstruct the RequestData object (to flow.request.data)
    request_data = RequestData(
        http_version=version.encode('utf-8'),
        headers=headers,
        content=content,
        trailers=None,
        timestamp_start=0,  # Placeholder values
        timestamp_end=0,
        host='',  # This can be filled in from headers or explicitly passed
        port=80,  # Default port for HTTP
        method=method.encode('utf-8'),
        scheme=b'http',
        authority=b'',
        path=path.encode('utf-8')
    )

    return request_data
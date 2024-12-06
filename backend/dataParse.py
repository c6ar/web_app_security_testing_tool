from mitmproxy.http import Headers, Request
from urllib.parse import urlparse



def parse_http_message(raw_request):
    """
    Parse a raw HTTP request string into the components required for mitmproxy.http.Request.make().

    :param raw_request: str, the raw HTTP request as a string
    :return: mitmproxy.http.Request
    """
    # Split headers and body
    parts = raw_request.split("\n\n", 1)
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
    headers = Headers()
    for line in header_lines:
        if ": " in line:
            key, value = line.split(": ", 1)
            headers[key.strip()] = value.strip()

    # Add default values for 'authority', 'timestamp_start', and 'timestamp_end' if not present
    authority = headers.get("authority", "")
    timestamp_start = headers.get("timestamp_start", "")
    timestamp_end = headers.get("timestamp_end", "")

    # Build the full URL
    host = headers.get("Host", "")
    scheme = "http"
    full_url = f"{scheme}://{host}{path}"

    authority = authority
    timestamp_start = timestamp_start or 0.0
    timestamp_end = timestamp_end or 0.0

    # Create mitmproxy Request object
    parsed_url = urlparse(full_url)
    request = Request(
        method=method,
        scheme=parsed_url.scheme,
        host=parsed_url.hostname,
        port=80,
        path=parsed_url.path + ("?" + parsed_url.query if parsed_url.query else ""),
        http_version=http_version,
        headers=headers,
        content=body.encode("utf-8"),
        trailers=None,
        authority = authority,
        timestamp_start = timestamp_start,
        timestamp_end = timestamp_end
    )

    return request


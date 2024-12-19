from mitmproxy.http import Request
import pickle

class Request2(Request):
    def __init__(self, *args, **kwargs):
        """
        Initialize the Request2 object by passing arguments to the parent Request class (mitmproxy.http.Request).

        Args:
            *args: Positional arguments for the parent Request class.
            **kwargs: Keyword arguments for the parent Request class.
        """
        super().__init__(*args, **kwargs)

    def to_serializable(self):
        """
        Converts the object to a dictionary suitable for serialization.
        """
        return {
            'host': self.host,
            'port': self.port,
            'method': self.method,
            'scheme': self.scheme,
            'authority': self.authority,
            'path': self.path,
            'http_version': self.http_version,
            'headers': self.headers,
            'content': self.content,
            'trailers': self.trailers,
            'timestamp_start': self.timestamp_start,
            'timestamp_end': self.timestamp_end,
            'forward_flag': self.forward_flag
        }

    @classmethod
    def from_serializable(cls, data: dict):
        """
        Reconstructs the object from its dictionary representation.
        :return: Request2
        """
        obj = cls(
            host=data['host'],
            port=data['port'],
            method=data['method'],
            scheme=data['scheme'],
            authority=data['authority'],
            path=data['path'],
            http_version=data['http_version'],
            headers=data['headers'],
            content=data['content'],
            trailers=data['trailers'],
            timestamp_start=data['timestamp_start'],
            timestamp_end=data['timestamp_end']
        )
        obj.forward_flag = data['forward_flag']
        return obj

    def serialize(self):
        """
        Serializes the object to a string using pickle.
        :return: bytes, picle.dupmps
        """
        return pickle.dumps(self.to_serializable())

    @classmethod
    def deserialize(cls, serialized_data):
        """
        Deserializes the string back into a Request2 object.
        """
        data = pickle.loads(serialized_data)
        return cls.from_serializable(data)

    @classmethod
    def from_request(cls, existing_request):
        """
        Create a Request2 object from an existing Request object.

        Args:
            existing_request (Request): The existing Request object to copy.

        Returns:
            Request2: A new Request2 object initialized with the existing Request data.
        """
        return cls(
            method=existing_request.method,
            scheme=existing_request.scheme,
            host=existing_request.host,
            port=existing_request.port,
            path=existing_request.path,
            http_version=existing_request.http_version,
            headers=existing_request.headers,
            content=existing_request.content,
            authority=existing_request.authority,
            trailers=existing_request.trailers,
            timestamp_start=existing_request.timestamp_start,
            timestamp_end=existing_request.timestamp_end
        )

    def to_request(self):
        """
        Create a new Request object from the current Request2 object.

        Returns:
            Request: A new Request object initialized with data from this Request2 object.
        """
        return Request(
            method=self.method.encode(),
            scheme=self.scheme.encode(),
            host=self.host,
            port=self.port,
            path=self.path.encode(),
            http_version=self.http_version.encode(),
            headers=self.headers,
            content=self.content,
            authority=self.authority.encode(),
            trailers=self.trailers,
            timestamp_start=self.timestamp_start,
            timestamp_end=self.timestamp_end

        )

    @classmethod
    def from_http_message(cls, http_message: str):
        """
        Create a Request2 object from an HTTP message string.

        Args:
            http_message (str): The HTTP message in string format.

        Returns:
            Request2: A new Request2 object initialized with data from the HTTP message.
        """
        # Split headers and body
        header_body_split = http_message.split("\n\n", 1)
        headers_part = header_body_split[0]
        body = header_body_split[1] if len(header_body_split) > 1 else None

        # Split request line and headers
        lines = headers_part.split("\n")
        request_line = lines[0]
        headers = lines[1:]

        # Parse request line (e.g., "POST / HTTP/1.1")

        method, path, version= request_line.split(" ", 3)

        # Parse headers
        header_dict = {}
        for header in headers:
            key, value = header.split(":", 1)
            header_dict[key.strip().encode()] = value.strip().encode()

        # Convert body to bytes if present
        content = body.encode("utf-8") if body else ''.encode("utf-8")

        # Extract host and authority for the Request class
        host = header_dict.get(b"Host", b"")
        authority = ""  # na chwile host  # Using "Host" header as the authority

        # Create and return the Request2 object
        return cls(
            method=method.encode(),
            scheme=b"https" if version.startswith("HTTPS") else b"http",
            host=host.split(b":")[0],
            port=443 if version.startswith("HTTPS") else 80,
            path=path.encode(),
            http_version=version.encode(),
            headers=list(header_dict.items()),
            content=content,
            authority=authority,
            trailers=None,
            timestamp_start=0.0,
            timestamp_end=0.0
        )

    def return_http_message(self):
        """
        Returns HTTP message from Request2 data.
        :return: str, HTTP message
        """

        method = self.method
        path = self.path
        version = self.http_version
        http_message = f"{method} {path} {version}\r\n"

        for key, value in self.headers.items():
            http_message += f"{key}: {value}\r\n"

        if self.content:
            try:
                content_length = str(len(self.content))
                http_message += f"Content-Length: {content_length}\r\n\r\n"
                http_message += self.content.decode('utf-8')
            except Exception as e:
                print(f"Błąd w dekodowaniu: {e}, {self}")
        else:
            http_message += "\r\n"

        return str(http_message)


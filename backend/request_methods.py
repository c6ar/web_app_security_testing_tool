from urllib import parse
import requests
from bs4 import BeautifulSoup
import re


def extract_key_value_pairs(data):
    """
    Extracts key-value pairs from a string formatted as key=value&key2=value2 and returns a dictionary.

    :param data: str, the input string to parse
    :return: dict, a dictionary containing the extracted key-value pairs
    """
    parsed_data = parse.parse_qs(data, keep_blank_values=True)
    return {key: values[0] if values else '' for key, values in parsed_data.items()}


def parse_http_message(http_message):
    """
    Parse an HTTP message into method, URL, and headers.
    :param http_message: str, the raw HTTP message
    :return: tuple (method, path, headers)
    """
    try:
        headers_body, body = http_message.split("\r\n\r\n")
    except ValueError:
        headers_body = http_message
        body = ""

    lines = headers_body.splitlines()
    request_line = lines[0]
    header_lines = lines[1:]
    data = extract_key_value_pairs(body)
    try:
        method, path, http_version = request_line.split(" ")
    except ValueError as e:
        raise ValueError("Invalid request line format.\nExpected 'method path http_version'.") from e

    headers = {}
    if len(header_lines) > 0:
        for line in header_lines:
            if ": " in line:
                key, value = line.split(": ", 1)
                headers[key.strip()] = value.strip()

    return method, path, headers, data


def send_http_message(host, http_message):
    """
    Send an HTTP request based on the provided HTTP message.
    :param host: str, url of a request
    :param http_message: str, the raw HTTP message
    :return: requests.Response, the response object
    """
    method, path, headers, data = parse_http_message(http_message)

    if method.upper() == "GET":
        response = requests.get(host, headers=headers)
    elif method.upper() == "POST":
        response = requests.post(host, headers=headers, data=data)
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
            return soup.prettify()
        return response.content
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

    placeholders = re.findall(r'§(.*?)§', http_message)

    if len(placeholders) > len(values):
        raise ValueError("Not enough values provided to replace all placeholders.")

    for i, placeholder in enumerate(placeholders):
        if i < len(values):
            http_message = http_message.replace(f'\u00a7{placeholder}\u00a7', values[i], 1)

    return http_message

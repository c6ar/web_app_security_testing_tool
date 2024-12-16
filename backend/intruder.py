import re
from operator import index
from utils.request_methods import *

#{'var0': 's\nh\nf', 'stuff': 'sdf\nsdf\nsdf'}
# values = ['var0', 'var1', 'var2']
#linia.litera

import re

# Funkcja do zamiany wszystkich wystąpień tekstu pomiędzy znakami '§'
def replace_between_symbols(input_string, new_substring):
    pattern = re.compile(r'§.*?§')
    return re.sub(pattern, new_substring, input_string)


import re


# Funkcja do zamiany wszystkich wystąpień tekstu pomiędzy znakami '§'
def replace_all_between_symbols(input_string, new_substrings):
        pattern = re.compile(r'§.*?§')
        matches = pattern.findall(input_string)

        if len(matches) != len(new_substrings):
                raise ValueError("Liczba nowych podciągów musi odpowiadać liczbie wystąpień wzorca.")

        for match, new_substring in zip(matches, new_substrings):
                input_string = input_string.replace(match, new_substring, 1)

        return input_string



def sniper_attack(dict, request):
        first_key = next(iter(dict))
        first_value = dict[first_key]
        words = first_value.split('\n')
        for word in words:
                new_request = replace_between_symbols(request, word)
                response = send_http_message(new_request)
                response_text = process_response(response)
                print(response_text)


def ram_attack(dictionary, request):
        keys = list(dictionary.keys())
        values = [dictionary[key].split('\n') for key in keys]

        for value_set in zip(*values):
                new_request = replace_all_between_symbols(request, value_set)
                response = send_http_message(new_request)
                response_text = process_response(response)
                print(response_text)

# request = r"""POST / HTTP/1.1
# Host: natas6.natas.labs.overthewire.org
# User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0
# Accept: text/html,applicaten-US;q=0ion/xhtml+xml,application/xml;q=0.9,/;q=0.8
# Accept-Language: pl,.7,en;q=0.3
# Accept-Encoding: gzip, deflate
# Content-Type: application/x-www-form-urlencoded
# Content-Length: 36
# Origin: http://natas6.natas.labs.overthewire.org/
# Authorization: Basic bmF0YXM2OjBSb0p3SGRTS1dGVFlSNVd1aUFld2F1U3VOYUJYbmVk
# Connection: keep-alive
# Referer: http://natas6.natas.labs.overthewire.org/
# Upgrade-Insecure-Requests: 1
# Priority: u=0, i
# Content-Length: 36
#
# secret=§var0§&token=§custom1§
# """


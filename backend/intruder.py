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


def sniper_attack(dict_wrold_list, request, position):
        first_key = next(iter(dict_wrold_list))
        first_value = dict_wrold_list[first_key]
        words = first_value.split('\n')
        for word in words:
                


def ram_attack(dict_wrold_list, request):
        first_key = next(iter(dict_wrold_list))
        first_value = dict_wrold_list[first_key]
        words = first_value.split('\n')
        for word in words:
                new_request = replace_between_symbols(request, word)
                response = send_http_message(new_request)
                response_text = process_response(response)
                print(response_text)


# request = """POST / HTTP/1.1
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


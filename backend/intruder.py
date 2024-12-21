import threading
import time
from operator import index
from backend.global_setup import *
from utils.request_methods import *
import re


def replace_between_symbols(input_string, new_substring):
    pattern = re.compile(r'§.*?§')
    return re.sub(pattern, new_substring, input_string)

def replace_word(request, word, position):
    """
    Replaces characters between position parameters
    ('start_line.start_column:end_line.end_column) with word
    """
    lines = request.split('\n')
    start_line, start_col = map(int, position.split(':')[0].split('.'))
    end_line, end_col = map(int, position.split(':')[1].split('.'))

    start_line -= 1
    end_line -= 1

    if start_line == end_line:
        lines[start_line] = lines[start_line][:start_col] + word + lines[start_line][end_col:]
    else:
        lines[start_line] = lines[start_line][:start_col] + word + lines[end_line][end_col:]
        for i in range(start_line + 1, end_line):
            lines[i] = ''

    request = '\n'.join(lines)
    pattern = re.compile(r'§var\d§')
    request = re.sub(pattern, '', request)

    return request.replace('§','')


def sniper_attack(q, worldlist, request, positions):
    """
    Performs a Sniper attack with an interval of 1 seconds between requests.
    The results are sent sequentially to the GUI.
    """
    def attack():
        words = worldlist.split('\n')
        position_list = [f"{key}: {value}" for key, value in positions.items()]

        for word in words:
            for position in position_list:
                data = {}
                modified_request = replace_word(request, word, position)
                response = send_http_message(modified_request)
                data['position'] = str(position_list.index(position) + 1)
                data['payload'] = word
                data['status_code'] = response.status_code
                data['resp_rec'] = '0'
                data['error'] = 'False'
                data['timeout'] = 'False'
                data['req_con'] = modified_request
                data['res_con'] = process_response(response)
                q.put(data)
                time.sleep(1)

    attack_thread = threading.Thread(target=attack, daemon=True)
    attack_thread.start()


def ram_attack(q, worldlist, request):
    """
    Performs a Ram attack with an interval of 1 seconds between requests.
    The results are sent sequentially to the GUI.
    """
    def attack():
        words = worldlist.split('\n')
        for word in words:
            data = {}
            modified_request = replace_between_symbols(request, word)
            response = send_http_message(modified_request)

            data['position'] = 'all'
            data['payload'] = word
            data['status_code'] = response.status_code
            data['resp_rec'] = '0'
            data['error'] = 'False'
            data['timeout'] = 'False'
            data['req_con'] = modified_request
            data['res_con'] = process_response(response)
            q.put(data)
            time.sleep(1)

    attack_thread = threading.Thread(target=attack, daemon=True)
    attack_thread.start()


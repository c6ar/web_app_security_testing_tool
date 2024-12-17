import pickle
import re
import time
from operator import index
import socket
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

def sniper_attack(worldlist, request, positions):
    # TODO BACKEND: cooldown between requests
    flow ={}
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
            serialized_flow = pickle.dumps(data)
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((HOST, BACK_FRONT_INTRUDERRESPONSES))
                    s.sendall(serialized_flow)
            except Exception as e:
                print(f"\nError while sending request to IntruderResult tab: {e}")

def ram_attack(wrold_list, request):
    # TODO BACKEND: cooldown between requests
    words = wrold_list.split('\n')
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
        serialized_flow = pickle.dumps(data)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, BACK_FRONT_INTRUDERRESPONSES))
                s.sendall(serialized_flow)
        except Exception as e:
            print(f"\nError while sending request to IntruderResult tab: {e}")


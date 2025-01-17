import threading
import time
from backend.request_methods import *
import re
import queue


def replace_between_symbols(input_string: str, new_substring: str) -> str:
    """
    Replaces substing of input string between § symbols.
    """
    pattern = re.compile(r'§.*?§')
    return re.sub(pattern, new_substring, input_string)


def replace_word(request: str, word: str, position: str) -> str:
    """
    Replaces characters between position parameters
    (start_line.start_column:end_line.end_column) with word
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

    return request.replace('§', '')


def sniper_attack(
        q: queue.Queue,
        request: str,
        hostname: str,
        wordlist: str,
        positions: dict,
        control_flags: dict) -> None:
    """
    Performs a Sniper attack with an interval of 1 seconds between requests.
    The results are sent sequentially to the GUI.
    """
    def attack():
        words = wordlist.split('\n')
        position_list = [f"{key}: {value}" for key, value in positions.items()]

        for word in words:
            for position in position_list:
                if control_flags["abort"].is_set():
                    q.put({"status": "aborted"})
                    return
                while control_flags["pause"].is_set():
                    time.sleep(0.1)

                data = {}
                modified_request = replace_word(request, word, position)
                response = send_http_message(hostname, modified_request)
                data['position'] = str(position_list.index(position) + 1)
                data['payload'] = word
                data['status_code'] = response.status_code
                data['error'] = 'False'
                data['timeout'] = 'False'
                data['req_con'] = modified_request
                data['res_con'] = process_response(response)
                q.put(data)
                time.sleep(1)

        q.put({"status": "completed"})

    attack_thread = threading.Thread(target=attack, daemon=True)
    attack_thread.start()


def ram_attack(
        q: queue.Queue,
        request: str,
        hostname: str,
        wordlist: str,
        control_flags: dict) -> None:
    """
    Performs a Ram attack with an interval of 1 seconds between requests.
    The results are sent sequentially to the GUI.
    """
    def attack():
        words = wordlist.split('\n')
        for word in words:
            if control_flags["abort"].is_set():
                q.put({"status": "aborted"})
                return
            while control_flags["pause"].is_set():
                time.sleep(0.1)
            data = {}
            modified_request = replace_between_symbols(request, word)
            response = send_http_message(hostname, modified_request)

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

        q.put({"status": "completed"})

    attack_thread = threading.Thread(target=attack, daemon=True)
    attack_thread.start()


def pitchfork_attack(
        q: queue.Queue,
        request: str,
        hostname: str,
        wordlists: dict,
        positions: dict,
        control_flags: dict) -> None:
    """
    Performs a Pitchfork attack with an interval of 1 seconds between requests.
    The results are sent sequentially to the GUI.
    """
    def attack():
        payloads = {}
        for key, wordlist in wordlists.items():
            payloads[key] = wordlist.split('\n')
        shortest_wordlist = min(payloads.values(), key=len)
        for i in range(len(shortest_wordlist)):
            if control_flags["abort"].is_set():
                q.put({"status": "aborted"})
                return
            while control_flags["pause"].is_set():
                time.sleep(0.1)
            data = {}
            modified_request = request
            words = ""
            for var in wordlists.keys():
                position = f"{positions[var][0]}: {positions[var][1]}"
                modified_request = replace_word(modified_request, payloads[var][i], position)
                words = words + f"{payloads[var][i]} "
            response = send_http_message(hostname, modified_request)
            data['position'] = 'respective'
            data['payload'] = words
            data['status_code'] = response.status_code
            data['resp_rec'] = '0'
            data['error'] = 'False'
            data['timeout'] = 'False'
            data['req_con'] = modified_request
            data['res_con'] = process_response(response)
            q.put(data)
            time.sleep(1)

        q.put({"status": "completed"})

    attack_thread = threading.Thread(target=attack, daemon=True)
    attack_thread.start()

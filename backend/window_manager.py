import tkinter as tk
from threading import Thread
import queue
import time

from backend.intruder import sniper_attack, ram_attack
from frontend.intruder import IntruderResult


class AppWindow:
    def __init__(self, root, q, window_id):
        self.root = root
        self.queue = q
        self.window_id = window_id

        self.root.title(f"Okno {window_id}")
        self.label = tk.Label(root, text=f"To jest okno {window_id}")
        self.label.pack()

        self.root.after(100, self.check_queue)

    def check_queue(self):
        while not self.queue.empty():
            data = self.queue.get()
        self.root.after(100, self.check_queue)
        return data

def create_window(q, window_id):
    root = tk.Tk()
    app = AppWindow(root, q, window_id)
    root.mainloop()

def logic_thread(q, window_id):
    for i in range(10):
        time.sleep(1)
        q.put(f"Aktualizacja z okna {window_id}: {i}")

class WindowManager:
    def __init__(self):
        self.queues = []
        self.window_threads = []
        self.logic_threads = []
        self.window_counter = 0

    def add_window(self, intruder_result, attack_type, payloads, request_text, positions=None):
        q = queue.Queue()
        self.queues.append(q)

        if attack_type == 0:
            producer = Thread(
                target=sniper_attack(payloads, request_text, positions),
                args=(q, self.window_counter)
            )
        elif attack_type == 1:
            producer = Thread(
                target=ram_attack(payloads, request_text),
                args=(q, self.window_counter)
            )
        else:
            # TODO BACKEND: 3rd option of an attack
            pass

        consumer = Thread(target=IntruderResult(self, self.gui, self.hosturl, self.positions_textbox, self.payloads_textboxes, timestamp), args=(q, self.window_counter))

        self.window_threads.append(consumer)
        self.logic_threads.append(producer)

        consumer.start()
        producer.start()

        self.window_counter += 1

    def remove_window(self, index):
        if index < len(self.window_threads):
            self.window_threads[index].join(timeout=1)
            self.logic_threads[index].join(timeout=1)

            del self.queues[index]
            del self.window_threads[index]
            del self.logic_threads[index]




"""Dynamiczne dodawanie i usuwanie par wątków komunikujących się ze sobą w Pythonie wymaga elastycznego zarządzania wątkami oraz kolejkami. Możemy to osiągnąć za pomocą list do przechowywania referencji do wątków oraz kolejek, a także funkcji do dynamicznego tworzenia i usuwania tych elementów.

Oto przykład, który pokazuje, jak można to zrobić:
W tym kodzie:

WindowManager to klasa zarządzająca wątkami i oknami.

add_window tworzy nowe okno oraz jego odpowiedni wątek logiczny.

remove_window usuwa okno i jego wątek logiczny na podstawie indeksu.


"""
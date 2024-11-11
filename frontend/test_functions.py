import random


def test1():
    return f"Start of output\nTest function testing...\n\n\n{10 * '-'}\nEnd of output.\n\n"


def test2(n):
    return f"Output: {n}, {n ** 2}, {n ** 3}.\n"


def generate_random_reqeust():
    time = f"{random.randint(0, 23):02}:{random.randint(0, 59):02}"
    entry_type = random.choice(["Info", "Warning", "Error"])
    direction = random.choice(["Inbound", "Outbound"])
    method = random.choice(["GET", "POST", "PUT", "DELETE"])
    url = f"http://example.com/{random.randint(1000, 9999)}"
    return time, entry_type, direction, method, url

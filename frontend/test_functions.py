import random


def test1():
    return f"Start of output\nTest function testing...\n\n\n{10 * '-'}\nEnd of output.\n\n"


def test2(n):
    return f"Output: {n}, {n ** 2}, {n ** 3}.\n"


def generate_random_reqeust():
    url = f"http://{random.choice(['example', 'test', 'check', 'domain'])}.{random.choice(['org', 'com', 'pl', 'eu'])}/"
    path = f"/{random.choice(['entry', 'page', '', 'test', 'subpage'])}"
    method = random.choice(["GET", "POST", "PUT", "DELETE"])
    content = "Lorem\nipsum\nhere"
    return url, path, method, content

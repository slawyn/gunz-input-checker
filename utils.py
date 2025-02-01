import json
import time
import random


def load_json(filename):
    with open(filename, "r", encoding="utf8") as f:
        return json.load(f)


def get_timestamp_ms():
    return int(time.time() * 1000)


def get_random(start, end):
    return random.randint(start, end)

import time


def milli_time():
    return time.time_ns() // 1000000

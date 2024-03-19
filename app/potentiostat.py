import time


def get_measurements() -> tuple[float, float]:
    while True:
        current = 0.1
        voltage = 0.1
        yield current, voltage
        time.sleep(1)


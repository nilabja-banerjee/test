import time
import os

def log(message):
    print(f"[LOG] {message}")

def log_file(file_path):
    print(f"[SCAN] Processing: {file_path}")

def log_time(func):
    def wrapper(*args, **kwargs):
        file_arg = args[1] if len(args) > 1 else None
        if file_arg:
            log_file(file_arg)
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        if file_arg:
            print(f"[DONE] {file_arg} in {end - start:.2f} sec")
        return result
    return wrapper

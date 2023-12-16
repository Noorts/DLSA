import time


def log_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        if elapsed_time > 0.1:
            print(f"{func.__name__} took {elapsed_time:.2f} seconds to execute")
        return result

    return wrapper

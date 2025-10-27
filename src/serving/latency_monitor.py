import time
import logging
from functools import wraps

logger = logging.getLogger("latency")
logging.basicConfig(level=logging.INFO)

def monitor_latency(threshold_ms=200):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = (time.time() - start_time) * 1000  # ms

            if duration > threshold_ms:
                logger.warning(f"[Latency] Function '{func.__name__}' took {duration:.1f} ms (exceeds {threshold_ms} ms)")
            else:
                logger.info(f"[Latency] Function '{func.__name__}' took {duration:.1f} ms")
            return result
        return wrapper
    return decorator


# Example usage
def dummy_prediction():
    time.sleep(0.15)
    return "ok"

@monitor_latency(threshold_ms=100)
def slow_fn():
    time.sleep(0.2)

if __name__ == '__main__':
    dummy_prediction()
    slow_fn()

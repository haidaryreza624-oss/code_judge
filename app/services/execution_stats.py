import time
import tracemalloc


class ExecutionStats:

    def __init__(self):
        self.start_time = None

    def start(self):
        self.start_time = time.perf_counter()
        tracemalloc.start()

    def finish(self):
        elapsed_time = time.perf_counter() - self.start_time

        current_memory, peak_memory = tracemalloc.get_traced_memory()

        tracemalloc.stop()

        return {
            "execution_time": round(elapsed_time, 4),
            "memory_usage": round(peak_memory / 1024, 2)
        }

import subprocess
import threading
import time

import psutil


def monitor_memory(process, result):
    peak_memory = 0

    try:
        parent = psutil.Process(process.pid)

        while process.poll() is None:

            try:
                memory = parent.memory_info().rss

                for child in parent.children(recursive=True):
                    try:
                        memory += child.memory_info().rss
                    except psutil.NoSuchProcess:
                        pass

                peak_memory = max(peak_memory, memory)

            except psutil.NoSuchProcess:
                break

            time.sleep(0.01)

    except psutil.NoSuchProcess:
        pass

    result["memory_usage"] = round(peak_memory / 1024, 2)


import subprocess
import sys
import uuid
import time
import threading

from pathlib import Path

from app.services.memory_monitor import monitor_memory


TEMP_DIR = Path("temp")


def execute_python(source_code: str, stdin: str = "", time_limit: float = 2.0):

    execution_id = uuid.uuid4().hex
    TEMP_DIR.mkdir(exist_ok=True)

    source_file = TEMP_DIR / f"{execution_id}.py"

    try:
        source_file.write_text(source_code, encoding="utf-8")

        start_time = time.perf_counter()

        process = subprocess.Popen(
            [sys.executable, str(source_file)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False
        )

        memory_result = {"memory_usage": 0}

        monitor = threading.Thread(
            target=monitor_memory,
            args=(process, memory_result)
        )

        monitor.start()

        try:
            stdout, stderr = process.communicate(
                input=stdin,
                timeout=time_limit
            )

        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()

            monitor.join()

            return {
                "status": "Time Limit Exceeded",
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": None,
                "execution_time": round(time_limit, 4),
                "memory_usage": memory_result["memory_usage"]
            }

        execution_time = round(
            time.perf_counter() - start_time, 4
        )

        monitor.join()

        return {
            "status": "Finished",
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": process.returncode,
            "execution_time": execution_time,
            "memory_usage": memory_result["memory_usage"]
        }

    except Exception as error:
        return {
            "status": "Internal Error",
            "stdout": "",
            "stderr": str(error),
            "exit_code": None,
            "execution_time": None,
            "memory_usage": None
        }

    finally:
        if source_file.exists():
            source_file.unlink()

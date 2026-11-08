import subprocess
import sys
import uuid
import time
import threading
import os

from pathlib import Path

from app.services.memory_monitor import monitor_memory


TEMP_DIR = Path("temp")


def execute_python(
    source_code: str,
    stdin: str = "",
    time_limit: float = 2.0
):

    execution_id = uuid.uuid4().hex
    TEMP_DIR.mkdir(exist_ok=True)

    source_file = TEMP_DIR / f"{execution_id}.py"

    process = None
    monitor = None
    memory_result = {"memory_usage": 0}

    try:

        source_file.write_text(source_code, encoding="utf-8")

        start_time = time.perf_counter()

        creation_flags = (
            subprocess.CREATE_NEW_PROCESS_GROUP
            if os.name == "nt"
            else 0
        )

        process = subprocess.Popen(
            [sys.executable, str(source_file)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
            creationflags=creation_flags
        )

        monitor = threading.Thread(
            target=monitor_memory,
            args=(process, memory_result),
            daemon=True
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

            return {
                "status": "Time Limit Exceeded",
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": None,
                "execution_time": round(time_limit, 4),
                "memory_usage": memory_result["memory_usage"]
            }

        execution_time = round(
            time.perf_counter() - start_time,
            4
        )

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

        if process is not None and process.poll() is None:
            process.kill()
            process.wait()

        if monitor is not None:
            monitor.join(timeout=1)

        if source_file.exists():
            source_file.unlink()
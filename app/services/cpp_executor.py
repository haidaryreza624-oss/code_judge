
import subprocess
import uuid
import time
import threading

from pathlib import Path

from app.services.language_manager import get_language
from app.services.memory_monitor import monitor_memory


TEMP_DIR = Path("temp")


def compile_cpp(source_code: str):

    execution_id = uuid.uuid4().hex

    TEMP_DIR.mkdir(exist_ok=True)

    source_file = TEMP_DIR / f"{execution_id}.cpp"
    output_file = TEMP_DIR / f"{execution_id}.exe"

    config = get_language("cpp")

    try:
        source_file.write_text(source_code, encoding="utf-8")

        compile_args = [
            config.compiler,
            *[
                arg.replace("{source}", str(source_file))
                   .replace("{output}", str(output_file))
                for arg in config.compile_args
            ]
        ]

        result = subprocess.run(
            compile_args,
            capture_output=True,
            text=True,
            timeout=15,
            shell=False
        )

        return {
            "success": result.returncode == 0,
            "stderr": result.stderr,
            "source_file": source_file,
            "output_file": output_file
        }

    except Exception as error:
        return {
            "success": False,
            "stderr": str(error),
            "source_file": source_file,
            "output_file": output_file
        }


def run_cpp(executable: Path, stdin: str = "", time_limit: float = 2.0):

    start_time = time.perf_counter()

    try:
        process = subprocess.Popen(
            [str(executable)],
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


def cleanup(source_file, output_file):

    for file in [source_file, output_file]:

        if file and file.exists():
            file.unlink()

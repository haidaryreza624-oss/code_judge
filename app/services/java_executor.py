import subprocess
import uuid
import time
import threading
import shutil

from pathlib import Path

from app.services.language_manager import get_language
from app.services.memory_monitor import monitor_memory


TEMP_DIR = Path("temp")


def compile_java(source_code: str):

    execution_id = uuid.uuid4().hex

    build_dir = TEMP_DIR / execution_id
    build_dir.mkdir(parents=True, exist_ok=True)

    source_file = build_dir / "Main.java"

    config = get_language("java")

    try:
        source_file.write_text(source_code, encoding="utf-8")

        compile_args = [
            config.compiler,
            *[
                arg.replace("{source}", str(source_file))
                   .replace("{build_dir}", str(build_dir))
                   .replace("{class_name}", "Main")
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
            "build_dir": build_dir,
            "class_name": "Main"
        }

    except Exception as error:
        return {
            "success": False,
            "stderr": str(error),
            "source_file": source_file,
            "build_dir": build_dir,
            "class_name": "Main"
        }


def run_java(
    build_dir: Path,
    stdin: str = "",
    time_limit: float = 2.0,
    memory_limit: int = 128000
):

    start_time = time.perf_counter()

    config = get_language("java")

    heap_limit = max(16 * 1024, int(memory_limit * 0.4))

    run_args = [
        arg.replace("{build_dir}", str(build_dir))
           .replace("{class_name}", "Main")
        for arg in config.run_args
    ]

    command = [
        config.runtime,
        f"-Xms16m",
        f"-Xmx{heap_limit}k",
        *run_args
    ]

    try:
        process = subprocess.Popen(
            command,
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


def cleanup_java(build_dir):

    if build_dir and build_dir.exists():
        shutil.rmtree(build_dir, ignore_errors=True)
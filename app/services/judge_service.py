from app.services.language_manager import get_language

from app.services.python_executor import execute_python

from app.services.cpp_executor import (
    compile_cpp,
    run_cpp,
    cleanup
)

from app.services.java_executor import (
    compile_java,
    run_java,
    cleanup_java
)

from app.services.output_checker import compare_output


def judge_submission(
    language: str,
    source_code: str,
    test_cases: list,
    time_limit: float = 2.0,
    memory_limit: int = 128000
):

    language = language.lower()

    get_language(language)

    executable = None
    source_file = None
    build_dir = None

    if language == "cpp":

        compilation = compile_cpp(source_code)

        source_file = compilation.get("source_file")
        executable = compilation.get("output_file")

        if not compilation["success"]:

            cleanup(source_file, executable)

            return {
                "status": "Compilation Error",
                "stderr": compilation["stderr"],
                "passed_test_cases": 0,
                "total_test_cases": len(test_cases),
                "execution_time": 0.0,
                "test_results": []
            }

    elif language == "java":

        compilation = compile_java(source_code)

        build_dir = compilation.get("build_dir")

        if not compilation["success"]:

            cleanup_java(build_dir)

            return {
                "status": "Compilation Error",
                "stderr": compilation["stderr"],
                "passed_test_cases": 0,
                "total_test_cases": len(test_cases),
                "execution_time": 0.0,
                "test_results": []
            }

    test_results = []
    passed = 0
    total_execution_time = 0.0

    try:

        for index, test_case in enumerate(test_cases, start=1):

            if language == "python":

                result = execute_python(
                    source_code,
                    test_case.stdin,
                    time_limit
                )

            elif language == "cpp":

                result = run_cpp(
                    executable,
                    test_case.stdin,
                    time_limit
                )

            else:

                result = run_java(
                    build_dir,
                    test_case.stdin,
                    time_limit,
                    memory_limit
                )

            case_time = result.get("execution_time") or 0.0

            total_execution_time += case_time

            memory_usage = result.get("memory_usage")

            if result["status"] != "Finished":

                status = result["status"]

            elif memory_usage is not None and memory_usage > memory_limit:

                status = "Memory Limit Exceeded"

            elif result["exit_code"] != 0:

                status = "Runtime Error"

            elif compare_output(
                result["stdout"],
                test_case.expected_output
            ):

                status = "Accepted"
                passed += 1

            else:

                status = "Wrong Answer"

            test_results.append({
                "test_case": index,
                "status": status,
                "stdout": result["stdout"],
                "stderr": result["stderr"],
                "execution_time": case_time,
                "memory_usage": memory_usage
            })

            if status != "Accepted":

                return {
                    "status": status,
                    "passed_test_cases": passed,
                    "total_test_cases": len(test_cases),
                    "execution_time": round(total_execution_time, 4),
                    "test_results": test_results
                }

        return {
            "status": "Accepted",
            "passed_test_cases": passed,
            "total_test_cases": len(test_cases),
            "execution_time": round(total_execution_time, 4),
            "test_results": test_results
        }

    finally:

        if language == "cpp":

            cleanup(source_file, executable)

        elif language == "java":

            cleanup_java(build_dir)
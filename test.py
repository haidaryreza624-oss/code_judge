import argparse
import json
import sys
import time
import urllib.error
import urllib.request


def request_json(url, method="GET", payload=None, timeout=15):
    data = None
    headers = {"Accept": "application/json"}

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body else {}

    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {error.code}: {body}")

    except urllib.error.URLError as error:
        raise RuntimeError(
            f"Cannot connect to {url}. Is FastAPI running? Details: {error}"
        )


def wait_for_job(base_url, job_id, poll_interval, max_wait):
    url = f"{base_url}/api/v1/submissions/{job_id}"

    deadline = time.monotonic() + max_wait
    previous_status = None

    while time.monotonic() < deadline:

        _, response = request_json(url)

        status = response.get("job_status")

        if status != previous_status:
            print(f"    Job status: {status}")
            previous_status = status

        if status in ("Completed", "Failed"):
            return response

        time.sleep(poll_interval)

    raise TimeoutError(
        f"Job {job_id} did not finish within {max_wait} seconds."
    )


def run_test(base_url, test, poll_interval, max_wait):

    print(f"\n[{test['name']}]")

    payload = {
        "language": "python",
        "source_code": test["source_code"],
        "test_cases": test["test_cases"],
        "time_limit": test["time_limit"],
        "memory_limit": 128000,
    }

    _, submitted = request_json(
        f"{base_url}/api/v1/submissions/",
        method="POST",
        payload=payload,
    )

    job_id = submitted.get("job_id")

    if not job_id:
        raise RuntimeError(f"Invalid submission response: {submitted}")

    print(f"    Submitted: {job_id}")

    final_response = wait_for_job(
        base_url,
        job_id,
        poll_interval,
        max_wait
    )

    result = final_response.get("result") or {}

    actual_verdict = result.get("status", "No verdict")
    expected_verdict = test["expected_verdict"]

    passed = actual_verdict == expected_verdict

    print(f"    Expected verdict: {expected_verdict}")
    print(f"    Actual verdict:   {actual_verdict}")

    if "passed_test_cases" in result:
        print(
            f"    Test cases: {result.get('passed_test_cases')}/"
            f"{result.get('total_test_cases')}"
        )

    for case in result.get("test_results", []):
        if case.get("status") != "Accepted":
            print(f"    First failing case: {case.get('test_case')}")
            print(f"    stdout: {case.get('stdout', '')!r}")
            print(f"    stderr: {case.get('stderr', '')!r}")
            break

    print(f"    RESULT: {'PASS' if passed else 'FAIL'}")

    return passed


def build_tests():

    tests = [

        # 1. Basic Accepted test
        {
            "name": "1. Accepted - three basic test cases",

            "source_code": (
                "import sys\n"
                "n = int(sys.stdin.readline())\n"
                "print(n * n)\n"
            ),

            "test_cases": [
                {"stdin": "2\n", "expected_output": "4\n"},
                {"stdin": "5\n", "expected_output": "25\n"},
                {"stdin": "12\n", "expected_output": "144\n"},
            ],

            "time_limit": 2.0,
            "expected_verdict": "Accepted",
        },

        # 2. Wrong Answer
        {
            "name": "2. Wrong Answer detection",

            "source_code": (
                "import sys\n"
                "n = int(sys.stdin.readline())\n"
                "print(n + 1)\n"
            ),

            "test_cases": [
                {"stdin": "5\n", "expected_output": "25\n"},
            ],

            "time_limit": 2.0,
            "expected_verdict": "Wrong Answer",
        },

        # 3. Runtime Error
        {
            "name": "3. Runtime Error detection",

            "source_code": "print(1 / 0)\n",

            "test_cases": [
                {"stdin": "", "expected_output": "0\n"},
            ],

            "time_limit": 2.0,
            "expected_verdict": "Runtime Error",
        },

        # 4. Time Limit Exceeded
        {
            "name": "4. Time Limit Exceeded detection",

            "source_code": (
                "import time\n"
                "time.sleep(5)\n"
                "print('finished')\n"
            ),

            "test_cases": [
                {"stdin": "", "expected_output": "finished\n"},
            ],

            "time_limit": 0.5,
            "expected_verdict": "Time Limit Exceeded",
        },

        # 5. Two Sum - 20 test cases
        {
            "name": "5. Two Sum - 20 test cases",

            "source_code": (
                "import sys\n"
                "\n"
                "data = list(map(int, sys.stdin.read().split()))\n"
                "n, target = data[0], data[1]\n"
                "nums = data[2:2 + n]\n"
                "seen = {}\n"
                "\n"
                "for i, num in enumerate(nums):\n"
                "    complement = target - num\n"
                "    if complement in seen:\n"
                "        print(seen[complement], i)\n"
                "        break\n"
                "    seen[num] = i\n"
            ),

            "test_cases": [
                {"stdin": "2 9\n2 7\n", "expected_output": "0 1\n"},
                {"stdin": "3 5\n3 1 4\n", "expected_output": "1 2\n"},
                {"stdin": "4 14\n1 5 9 20\n", "expected_output": "1 2\n"},
                {"stdin": "5 17\n4 6 2 15 30\n", "expected_output": "2 3\n"},
                {"stdin": "4 4\n10 -3 7 22\n", "expected_output": "1 2\n"},
                {"stdin": "4 4\n-8 3 12 5\n", "expected_output": "0 2\n"},
                {"stdin": "4 75\n100 1 50 25\n", "expected_output": "2 3\n"},
                {"stdin": "4 19\n0 13 6 20\n", "expected_output": "1 2\n"},
                {"stdin": "5 3\n11 -5 8 30 2\n", "expected_output": "1 2\n"},
                {"stdin": "4 49\n7 14 22 35\n", "expected_output": "1 3\n"},
                {"stdin": "5 48\n2 9 17 31 40\n", "expected_output": "2 3\n"},
                {"stdin": "4 60\n5 16 23 44\n", "expected_output": "1 3\n"},
                {"stdin": "4 5\n-10 4 15 27\n", "expected_output": "0 2\n"},
                {"stdin": "4 17\n6 -2 19 40\n", "expected_output": "1 2\n"},
                {"stdin": "5 79\n3 18 29 50 70\n", "expected_output": "2 3\n"},
                {"stdin": "4 7\n0 -7 14 33\n", "expected_output": "1 2\n"},
                {"stdin": "4 53\n12 25 41 60\n", "expected_output": "0 2\n"},
                {"stdin": "5 26\n8 19 -4 30 45\n", "expected_output": "2 3\n"},
                {"stdin": "4 50\n101 -1 51 200\n", "expected_output": "1 2\n"},
                {"stdin": "4 93\n13 27 38 55\n", "expected_output": "2 3\n"},
            ],

            "time_limit": 2.0,
            "expected_verdict": "Accepted",
        },
    ]

    return tests


def main():

    parser = argparse.ArgumentParser(
        description="Test the CodeArena FastAPI Judge."
    )

    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000"
    )

    parser.add_argument(
        "--poll-interval",
        type=float,
        default=0.5
    )

    parser.add_argument(
        "--max-wait",
        type=float,
        default=30
    )

    args = parser.parse_args()

    base_url = args.url.rstrip("/")

    print("=" * 60)
    print("CodeArena Judge Engine - Test Suite")
    print(f"Server: {base_url}")
    print("=" * 60)

    # Health check
    try:
        _, health = request_json(f"{base_url}/health")
        print(f"Health check: {health}")

    except Exception as error:
        print(f"\nSERVER CHECK FAILED:\n{error}")
        return 2

    outcomes = []

    for test in build_tests():

        try:
            passed = run_test(
                base_url,
                test,
                args.poll_interval,
                args.max_wait
            )

        except Exception as error:
            print(f"    TEST ERROR: {error}")
            passed = False

        outcomes.append((test["name"], passed))

    # Final summary
    passed_count = sum(
        1 for _, passed in outcomes if passed
    )

    print("\n" + "=" * 60)
    print(
        f"SUMMARY: {passed_count}/{len(outcomes)} tests passed"
    )

    for name, passed in outcomes:
        print(
            f"  {'PASS' if passed else 'FAIL'} - {name}"
        )

    print("=" * 60)

    return 0 if passed_count == len(outcomes) else 1


if __name__ == "__main__":
    sys.exit(main())
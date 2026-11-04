from app.services.judge_service import judge_submission
from app.schemas.submission import TestCase


def test_python_accepted():

    result = judge_submission(
        language="python",
        source_code="a, b = map(int, input().split())\nprint(a + b)",
        test_cases=[
            TestCase(stdin="2 3\n", expected_output="5\n"),
            TestCase(stdin="10 20\n", expected_output="30\n")
        ]
    )

    assert result["status"] == "Accepted"
    assert result["passed_test_cases"] == 2


def test_python_wrong_answer():

    result = judge_submission(
        language="python",
        source_code="print(10)",
        test_cases=[
            TestCase(stdin="", expected_output="20")
        ]
    )

    assert result["status"] == "Wrong Answer"


def test_python_runtime_error():

    result = judge_submission(
        language="python",
        source_code="print(1 / 0)",
        test_cases=[
            TestCase(stdin="", expected_output="0")
        ]
    )

    assert result["status"] == "Runtime Error"


def test_python_time_limit():

    result = judge_submission(
        language="python",
        source_code="while True:\n    pass",
        test_cases=[
            TestCase(stdin="", expected_output="")
        ],
        time_limit=1
    )

    assert result["status"] == "Time Limit Exceeded"
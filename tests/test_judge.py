
from app.schemas.submission import TestCase
from app.services.judge_service import judge_submission


def assert_verdict(result, expected):
    assert result["status"] == expected, (
        f"\nExpected: {expected}"
        f"\nActual: {result['status']}"
        f"\nComplete result: {result}"
    )


def create_arrays():
    arrays = [
        [5, 1, 9, 2, 6],
        [-3, 7, 7, 0, 2, 10],
        [4],
        [-8, -2, -5, -1],
        [100, 50, 25, 75, 0, 125, 25],
        [1, 2],
        [2, 2, 2, 2, 2],
        [-100, -50, -25, -75],
        [0, 0, 0, 0],
        [999999, -999999, 500000, -500000],
        list(range(1, 101)),
        list(range(100, 0, -1)),
        [i * -3 for i in range(1, 101)],
        [i % 7 for i in range(200)],
        [(-1) ** i * i for i in range(1, 301)],
        [42] * 500,
        [i - 1000 for i in range(2000)],
        [10000 - i for i in range(3000)],
        [((i * 7919) % 200001) - 100000 for i in range(5000)],
        [((i * 104729) % 1000001) - 500000 for i in range(10000)],
    ]

    return arrays


def create_test_cases():
    test_cases = []

    for arr in create_arrays():
        sorted_arr = sorted(arr)

        expected = (
            sum(arr),
            min(arr),
            max(arr),
            sorted_arr[(len(arr) - 1) // 2],
            sum(1 for x in arr if x % 2 == 0)
        )

        test_cases.append(
            TestCase(
                stdin=" ".join(map(str, arr)),
                expected_output=" ".join(map(str, expected))
            )
        )

    return test_cases


PYTHON_ACCEPTED = """
import sys

numbers = list(map(int, sys.stdin.read().split()))

numbers.sort()

total = sum(numbers)
minimum = numbers[0]
maximum = numbers[-1]
median = numbers[(len(numbers) - 1) // 2]
even_count = sum(1 for x in numbers if x % 2 == 0)

print(total, minimum, maximum, median, even_count)
"""


CPP_ACCEPTED = """
#include <iostream>
#include <vector>
#include <algorithm>
using namespace std;

int main() {
    vector<long long> numbers;
    long long x;

    while (cin >> x) {
        numbers.push_back(x);
    }

    if (numbers.empty()) return 1;

    sort(numbers.begin(), numbers.end());

    long long total = 0;
    int even_count = 0;

    for (long long n : numbers) {
        total += n;

        if (n % 2 == 0) {
            even_count++;
        }
    }

    long long minimum = numbers.front();
    long long maximum = numbers.back();
    long long median = numbers[(numbers.size() - 1) / 2];

    cout << total << " "
         << minimum << " "
         << maximum << " "
         << median << " "
         << even_count << endl;

    return 0;
}
"""


JAVA_ACCEPTED = """
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);

        ArrayList<Long> numbers = new ArrayList<>();

        while (scanner.hasNextLong()) {
            numbers.add(scanner.nextLong());
        }

        if (numbers.isEmpty()) {
            System.exit(1);
        }

        Collections.sort(numbers);

        long total = 0;
        int evenCount = 0;

        for (long n : numbers) {
            total += n;

            if (n % 2 == 0) {
                evenCount++;
            }
        }

        long minimum = numbers.get(0);
        long maximum = numbers.get(numbers.size() - 1);
        long median = numbers.get((numbers.size() - 1) / 2);

        System.out.println(
            total + " " +
            minimum + " " +
            maximum + " " +
            median + " " +
            evenCount
        );
    }
}
"""


# ==========================================
# PYTHON TESTS
# ==========================================

def test_python_accepted():
    result = judge_submission(
        language="python",
        source_code=PYTHON_ACCEPTED,
        test_cases=create_test_cases(),
        time_limit=5,
        memory_limit=256000
    )

    assert_verdict(result, "Accepted")
    assert result["passed_test_cases"] == 20
    assert result["total_test_cases"] == 20


def test_python_wrong_answer():
    result = judge_submission(
        language="python",
        source_code="print(999999)",
        test_cases=[
            TestCase(stdin="1 2 3", expected_output="6 1 3 2 1")
        ]
    )

    assert_verdict(result, "Wrong Answer")


def test_python_runtime_error():
    result = judge_submission(
        language="python",
        source_code="raise RuntimeError('Intentional failure')",
        test_cases=[
            TestCase(stdin="", expected_output="0")
        ]
    )

    assert_verdict(result, "Runtime Error")


def test_python_time_limit():
    result = judge_submission(
        language="python",
        source_code="""
while True:
    pass
""",
        test_cases=[
            TestCase(stdin="", expected_output="")
        ],
        time_limit=1
    )

    assert_verdict(result, "Time Limit Exceeded")


# ==========================================
# C++ TESTS
# ==========================================

def test_cpp_accepted():
    result = judge_submission(
        language="cpp",
        source_code=CPP_ACCEPTED,
        test_cases=create_test_cases(),
        time_limit=5,
        memory_limit=256000
    )

    assert_verdict(result, "Accepted")
    assert result["passed_test_cases"] == 20
    assert result["total_test_cases"] == 20


def test_cpp_wrong_answer():
    result = judge_submission(
        language="cpp",
        source_code="""
#include <iostream>
int main() {
    std::cout << 999999;
    return 0;
}
""",
        test_cases=[
            TestCase(stdin="1 2 3", expected_output="6 1 3 2 1")
        ]
    )

    assert_verdict(result, "Wrong Answer")


def test_cpp_runtime_error():
    result = judge_submission(
        language="cpp",
        source_code="""
#include <iostream>

int main() {
    std::cerr << "Intentional runtime failure";
    return 1;
}
""",
        test_cases=[
            TestCase(stdin="", expected_output="0")
        ]
    )

    assert_verdict(result, "Runtime Error")


def test_cpp_time_limit():
    result = judge_submission(
        language="cpp",
        source_code="""
int main() {
    volatile unsigned long long x = 0;

    while (true) {
        x++;
    }

    return 0;
}
""",
        test_cases=[
            TestCase(stdin="", expected_output="")
        ],
        time_limit=1
    )

    assert_verdict(result, "Time Limit Exceeded")


def test_cpp_compilation_error():
    result = judge_submission(
        language="cpp",
        source_code="""
#include <iostream>

int main() {
    this is invalid cpp code;
    return 0;
}
""",
        test_cases=[
            TestCase(stdin="", expected_output="")
        ]
    )

    assert_verdict(result, "Compilation Error")


# ==========================================
# JAVA TESTS
# ==========================================

def test_java_accepted():
    result = judge_submission(
        language="java",
        source_code=JAVA_ACCEPTED,
        test_cases=create_test_cases(),
        time_limit=5,
        memory_limit=256000
    )

    assert_verdict(result, "Accepted")
    assert result["passed_test_cases"] == 20
    assert result["total_test_cases"] == 20


def test_java_wrong_answer():
    result = judge_submission(
        language="java",
        source_code="""
public class Main {
    public static void main(String[] args) {
        System.out.println(999999);
    }
}
""",
        test_cases=[
            TestCase(stdin="1 2 3", expected_output="6 1 3 2 1")
        ]
    )

    assert_verdict(result, "Wrong Answer")


def test_java_runtime_error():
    result = judge_submission(
        language="java",
        source_code="""
public class Main {
    public static void main(String[] args) {
        throw new RuntimeException("Intentional failure");
    }
}
""",
        test_cases=[
            TestCase(stdin="", expected_output="0")
        ]
    )

    assert_verdict(result, "Runtime Error")


def test_java_time_limit():
    result = judge_submission(
        language="java",
        source_code="""
public class Main {
    public static void main(String[] args) {
        long x = 0;

        while (true) {
            x++;
        }
    }
}
""",
        test_cases=[
            TestCase(stdin="", expected_output="")
        ],
        time_limit=1
    )

    assert_verdict(result, "Time Limit Exceeded")


def test_java_compilation_error():
    result = judge_submission(
        language="java",
        source_code="""
public class Main {
    public static void main(String[] args) {
        this is invalid java code;
    }
}
""",
        test_cases=[
            TestCase(stdin="", expected_output="")
        ]
    )

    assert_verdict(result, "Compilation Error")

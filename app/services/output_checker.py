def normalize_output(output: str) -> str:
    return "\n".join(
        line.rstrip()
        for line in output.strip().splitlines()
    )


def compare_output(actual: str, expected: str) -> bool:
    return normalize_output(actual) == normalize_output(expected)
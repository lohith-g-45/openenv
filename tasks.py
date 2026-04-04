from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class Task:
    id: str
    difficulty: str
    problem: str
    code: str
    test_cases: List[Dict[str, str]]
    expected_outputs: Dict[str, str]
    expected_approach: str


TASKS: List[Task] = [
    Task(
        id="easy-1",
        difficulty="easy",
        problem="Fix add(a, b) so it returns the sum.",
        code="def add(a, b):\n    return a - b\n",
        test_cases=[
            {"name": "t1", "input": "add(1, 2)", "expected": "3"},
            {"name": "t2", "input": "add(-1, 1)", "expected": "0"},
        ],
        expected_outputs={"t1": "3", "t2": "0"},
        expected_approach="direct-fix",
    ),
    Task(
        id="medium-1",
        difficulty="medium",
        problem="Fix reverse_string(s) to return reversed text.",
        code="def reverse_string(s):\n    return ''.join(sorted(s))\n",
        test_cases=[
            {"name": "t1", "input": "reverse_string('abc')", "expected": "cba"},
            {"name": "t2", "input": "reverse_string('aab')", "expected": "baa"},
        ],
        expected_outputs={"t1": "cba", "t2": "baa"},
        expected_approach="string-manipulation",
    ),
    Task(
        id="hard-1",
        difficulty="hard",
        problem="Fix two_sum(nums, target) to return indices of two numbers summing to target.",
        code=(
            "def two_sum(nums, target):\n"
            "    for i in range(len(nums)):\n"
            "        for j in range(i + 1, len(nums)):\n"
            "            if nums[i] + nums[j] == target + 1:\n"
            "                return [i, j]\n"
            "    return []\n"
        ),
        test_cases=[
            {
                "name": "t1",
                "input": "two_sum([2, 7, 11, 15], 9)",
                "expected": "[0, 1]",
            },
            {
                "name": "t2",
                "input": "two_sum([3, 2, 4], 6)",
                "expected": "[1, 2]",
            },
        ],
        expected_outputs={"t1": "[0, 1]", "t2": "[1, 2]"},
        expected_approach="hash-map-lookup",
    ),
]


def get_tasks() -> List[Task]:
    return TASKS

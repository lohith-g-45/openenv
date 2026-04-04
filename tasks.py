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
        problem="Two Sum: Find indices of two numbers that sum to target.",
        code="def two_sum(nums, target):\n    # Write your solution here\n    pass\n",
        test_cases=[
            {"name": "t1", "input": "two_sum([2, 7, 11, 15], 9)", "expected": "[0, 1]"},
            {"name": "t2", "input": "two_sum([3, 2, 4], 6)", "expected": "[1, 2]"},
            {"name": "t3", "input": "two_sum([3, 3], 6)", "expected": "[0, 1]"},
            {"name": "t4", "input": "two_sum([1, 5, 3, 7], 8)", "expected": "[1, 2]"},
        ],
        expected_outputs={"t1": "[0, 1]", "t2": "[1, 2]", "t3": "[0, 1]", "t4": "[1, 2]"},
        expected_approach="hash-map-lookup",
    ),
    Task(
        id="medium-1",
        difficulty="medium",
        problem="Longest Substring Without Repeating Characters: Return length of longest unique substring.",
        code="def length_of_longest_substring(s):\n    # Write your solution here\n    pass\n",
        test_cases=[
            {"name": "t1", "input": "length_of_longest_substring('abcabcbb')", "expected": "3"},
            {"name": "t2", "input": "length_of_longest_substring('bbbbb')", "expected": "1"},
            {"name": "t3", "input": "length_of_longest_substring('pwwkew')", "expected": "3"},
            {"name": "t4", "input": "length_of_longest_substring('')", "expected": "0"},
        ],
        expected_outputs={"t1": "3", "t2": "1", "t3": "3", "t4": "0"},
        expected_approach="sliding-window",
    ),
    Task(
        id="hard-1",
        difficulty="hard",
        problem="Trapping Rain Water: Given elevation heights, compute trapped water.",
        code="def trap(height):\n    # Write your solution here\n    pass\n",
        test_cases=[
            {"name": "t1", "input": "trap([0,1,0,2,1,0,1,3,2,1,2,1])", "expected": "6"},
            {"name": "t2", "input": "trap([4,2,0,3,2,5])", "expected": "9"},
            {"name": "t3", "input": "trap([1,0,1])", "expected": "1"},
            {"name": "t4", "input": "trap([3,0,2,0,4])", "expected": "7"},
        ],
        expected_outputs={"t1": "6", "t2": "9", "t3": "1", "t4": "7"},
        expected_approach="two-pointers",
    ),
]


def get_tasks() -> List[Task]:
    return TASKS

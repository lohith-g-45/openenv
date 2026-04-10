from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List


def default_task_grader(state: Dict[str, Any]) -> float:
    """Per-task callable grader used by inference and validator checks.

    Kept self-contained so validation environments with different import
    semantics still evaluate grader scores deterministically.
    """
    eps = 1e-6
    if not isinstance(state, dict):
        return 0.5

    # 0.3: bug detection signal
    err = str(state.get("error_type", "")).strip().lower()
    bug_score = 1.0 if err and err not in {"none", "unknown", ""} else 0.0

    # 0.3: analysis signal
    analysis = state.get("analysis", {})
    analysis_score = 1.0 if isinstance(analysis, dict) and len(analysis) > 0 else 0.0

    # 0.4: code signal
    code = state.get("code", "")
    code_score = 1.0 if isinstance(code, str) and len(code.strip()) > 0 else 0.0

    score = float(0.3 * bug_score + 0.3 * analysis_score + 0.4 * code_score)
    if score <= 0.0:
        return eps
    if score >= 1.0:
        return 1.0 - eps
    return score


@dataclass(frozen=True)
class Task:
    id: str
    difficulty: str
    problem: str
    code: str
    test_cases: List[Dict[str, str]]
    expected_outputs: Dict[str, str]
    expected_approach: str
    grader: Callable[[Dict[str, Any]], float] = default_task_grader
    grader_name: str = "EvaluationGrader"
    hidden_test_cases: List[Dict[str, str]] = field(default_factory=list)
    starter_code: Dict[str, str] = field(default_factory=dict)


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
        hidden_test_cases=[
            {"name": "h1", "input": "two_sum([2, 7, 11, 15], 9)", "expected": "[0, 1]"},
            {"name": "h2", "input": "two_sum([3, 2, 4], 6)", "expected": "[1, 2]"},
            {"name": "h3", "input": "two_sum([3, 3], 6)", "expected": "[0, 1]"},
            {"name": "h4", "input": "two_sum([0, 4, 3, 0], 0)", "expected": "[0, 3]"},
            {"name": "h5", "input": "two_sum([-1, -2, -3, -4, -5], -8)", "expected": "[2, 4]"},
            {"name": "h6", "input": "two_sum([1, 2, 3, 4, 5], 9)", "expected": "[3, 4]"},
            {"name": "h7", "input": "two_sum([5, 75, 25], 100)", "expected": "[1, 2]"},
            {"name": "h8", "input": "two_sum([1, 5, 1, 5], 10)", "expected": "[1, 3]"},
        ],
        expected_outputs={"t1": "[0, 1]", "t2": "[1, 2]", "t3": "[0, 1]", "t4": "[1, 2]"},
        expected_approach="hash-map-lookup",
        grader=default_task_grader,
        grader_name="EvaluationGrader",
        starter_code={
            "python": "def two_sum(nums, target):\n    # Write your solution here\n    pass\n",
            "c": (
                "#include <stdlib.h>\n\n"
                "int* two_sum(int* nums, int numsSize, int target, int* returnSize) {\n"
                "    // Write your solution here\n"
                "    *returnSize = 0;\n"
                "    return NULL;\n"
                "}\n"
            ),
            "java": (
                "import java.util.*;\n\n"
                "class Solution {\n"
                "    public static int[] two_sum(int[] nums, int target) {\n"
                "        // Write your solution here\n"
                "        return new int[]{};\n"
                "    }\n"
                "}\n"
            ),
        },
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
        hidden_test_cases=[
            {"name": "h1", "input": "length_of_longest_substring('abcabcbb')", "expected": "3"},
            {"name": "h2", "input": "length_of_longest_substring('bbbbb')", "expected": "1"},
            {"name": "h3", "input": "length_of_longest_substring('pwwkew')", "expected": "3"},
            {"name": "h4", "input": "length_of_longest_substring('')", "expected": "0"},
            {"name": "h5", "input": "length_of_longest_substring('dvdf')", "expected": "3"},
            {"name": "h6", "input": "length_of_longest_substring('abba')", "expected": "2"},
            {"name": "h7", "input": "length_of_longest_substring('tmmzuxt')", "expected": "5"},
            {"name": "h8", "input": "length_of_longest_substring('anviaj')", "expected": "5"},
        ],
        expected_outputs={"t1": "3", "t2": "1", "t3": "3", "t4": "0"},
        expected_approach="sliding-window",
        grader=default_task_grader,
        grader_name="EvaluationGrader",
        starter_code={
            "python": "def length_of_longest_substring(s):\n    # Write your solution here\n    pass\n",
            "c": (
                "#include <string.h>\n\n"
                "int length_of_longest_substring(char* s) {\n"
                "    // Write your solution here\n"
                "    return 0;\n"
                "}\n"
            ),
            "java": (
                "import java.util.*;\n\n"
                "class Solution {\n"
                "    public static int length_of_longest_substring(String s) {\n"
                "        // Write your solution here\n"
                "        return 0;\n"
                "    }\n"
                "}\n"
            ),
        },
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
        hidden_test_cases=[
            {"name": "h1", "input": "trap([0,1,0,2,1,0,1,3,2,1,2,1])", "expected": "6"},
            {"name": "h2", "input": "trap([4,2,0,3,2,5])", "expected": "9"},
            {"name": "h3", "input": "trap([1,0,1])", "expected": "1"},
            {"name": "h4", "input": "trap([3,0,2,0,4])", "expected": "7"},
            {"name": "h5", "input": "trap([])", "expected": "0"},
            {"name": "h6", "input": "trap([2,0,2])", "expected": "2"},
            {"name": "h7", "input": "trap([2,1,0,1,2])", "expected": "4"},
            {"name": "h8", "input": "trap([5,4,1,2])", "expected": "1"},
        ],
        expected_outputs={"t1": "6", "t2": "9", "t3": "1", "t4": "7"},
        expected_approach="two-pointers",
        grader=default_task_grader,
        grader_name="EvaluationGrader",
        starter_code={
            "python": "def trap(height):\n    # Write your solution here\n    pass\n",
            "c": (
                "int trap(int* height, int heightSize) {\n"
                "    // Write your solution here\n"
                "    return 0;\n"
                "}\n"
            ),
            "java": (
                "import java.util.*;\n\n"
                "class Solution {\n"
                "    public static int trap(int[] height) {\n"
                "        // Write your solution here\n"
                "        return 0;\n"
                "    }\n"
                "}\n"
            ),
        },
    ),
]


def get_tasks() -> List[Task]:
    return TASKS


def get_starter_code(task: Task, language: str) -> str:
    if task.starter_code and language in task.starter_code:
        return task.starter_code[language]
    return task.code

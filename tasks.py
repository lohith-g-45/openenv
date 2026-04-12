from dataclasses import dataclass, field
from typing import Any, Dict, List

# Import graders through server compatibility path.
from server.graders import EasyGrader, MediumGrader, HardGrader


@dataclass(frozen=True)
class Task:
    id: str
    difficulty: str
    problem: str
    code: str
    test_cases: List[Dict[str, str]]
    expected_outputs: Dict[str, str]
    expected_approach: str
    grader: Any = field(default_factory=EasyGrader)
    grader_name: str = "EasyGrader"
    hidden_test_cases: List[Dict[str, str]] = field(default_factory=list)
    starter_code: Dict[str, str] = field(default_factory=dict)


# --- NEW TASKS: Each easy task has a medium and hard variant ---
TASKS: List[Task] = [
    # Easy 1: Palindrome Check (basic)
    Task(
        id="easy-1",
        difficulty="easy",
        problem="Check if a string is a palindrome (case-insensitive, ignore spaces).",
        code="def is_palindrome(s):\n    # Write your solution here\n    pass\n",
        test_cases=[
            {"name": "t1", "input": "is_palindrome('racecar')", "expected": "True"},
            {"name": "t2", "input": "is_palindrome('A man a plan a canal Panama')", "expected": "True"},
            {"name": "t3", "input": "is_palindrome('hello')", "expected": "False"},
        ],
        hidden_test_cases=[
            {"name": "h1", "input": "is_palindrome('No lemon no melon')", "expected": "True"},
            {"name": "h2", "input": "is_palindrome('Python')", "expected": "False"},
        ],
        expected_outputs={"t1": "True", "t2": "True", "t3": "False"},
        expected_approach="two-pointer",
        grader=EasyGrader(),
        grader_name="EasyGrader",
        starter_code={"python": "def is_palindrome(s):\n    # Write your solution here\n    pass\n"},
    ),
    # Medium 1: Palindrome Check (with punctuation)
    Task(
        id="medium-1",
        difficulty="medium",
        problem="Check if a string is a palindrome (ignore case, spaces, and punctuation).",
        code="def is_palindrome(s):\n    # Write your solution here\n    pass\n",
        test_cases=[
            {"name": "t1", "input": "is_palindrome('Eva, can I see bees in a cave?')", "expected": "True"},
            {"name": "t2", "input": "is_palindrome('Was it a car or a cat I saw?')", "expected": "True"},
            {"name": "t3", "input": "is_palindrome('OpenAI')", "expected": "False"},
        ],
        hidden_test_cases=[
            {"name": "h1", "input": "is_palindrome('Red roses run no risk, sir, on Nurse’s order.')", "expected": "True"},
            {"name": "h2", "input": "is_palindrome('Not a palindrome!')", "expected": "False"},
        ],
        expected_outputs={"t1": "True", "t2": "True", "t3": "False"},
        expected_approach="filter-non-alphanumeric",
        grader=MediumGrader(),
        grader_name="MediumGrader",
        starter_code={"python": "def is_palindrome(s):\n    # Write your solution here\n    pass\n"},
    ),
    # Hard 1: Palindrome Partitioning
    Task(
        id="hard-1",
        difficulty="hard",
        problem="Given a string, partition it into the minimum number of palindromic substrings.",
        code="def min_palindrome_partitions(s):\n    # Write your solution here\n    pass\n",
        test_cases=[
            {"name": "t1", "input": "min_palindrome_partitions('aab')", "expected": "1"},
            {"name": "t2", "input": "min_palindrome_partitions('racecar')", "expected": "0"},
            {"name": "t3", "input": "min_palindrome_partitions('banana')", "expected": "1"},
        ],
        hidden_test_cases=[
            {"name": "h1", "input": "min_palindrome_partitions('noonabbad')", "expected": "2"},
            {"name": "h2", "input": "min_palindrome_partitions('abc')", "expected": "2"},
        ],
        expected_outputs={"t1": "1", "t2": "0", "t3": "1"},
        expected_approach="dynamic-programming",
        grader=HardGrader(),
        grader_name="HardGrader",
        starter_code={"python": "def min_palindrome_partitions(s):\n    # Write your solution here\n    pass\n"},
    ),
    # Easy 2: Fibonacci (basic)
    Task(
        id="easy-2",
        difficulty="easy",
        problem="Return the nth Fibonacci number (n >= 0, n <= 20).",
        code="def fibonacci(n):\n    # Write your solution here\n    pass\n",
        test_cases=[
            {"name": "t1", "input": "fibonacci(0)", "expected": "0"},
            {"name": "t2", "input": "fibonacci(1)", "expected": "1"},
            {"name": "t3", "input": "fibonacci(5)", "expected": "5"},
        ],
        hidden_test_cases=[
            {"name": "h1", "input": "fibonacci(10)", "expected": "55"},
            {"name": "h2", "input": "fibonacci(15)", "expected": "610"},
        ],
        expected_outputs={"t1": "0", "t2": "1", "t3": "5"},
        expected_approach="recursion-or-iteration",
        grader=EasyGrader(),
        grader_name="EasyGrader",
        starter_code={"python": "def fibonacci(n):\n    # Write your solution here\n    pass\n"},
    ),
    # Medium 2: Fibonacci (large n, optimize)
    Task(
        id="medium-2",
        difficulty="medium",
        problem="Return the nth Fibonacci number (n >= 0, n <= 1000) efficiently.",
        code="def fibonacci(n):\n    # Write your solution here\n    pass\n",
        test_cases=[
            {"name": "t1", "input": "fibonacci(20)", "expected": "6765"},
            {"name": "t2", "input": "fibonacci(50)", "expected": "12586269025"},
            {"name": "t3", "input": "fibonacci(100)", "expected": "354224848179261915075"},
        ],
        hidden_test_cases=[
            {"name": "h1", "input": "fibonacci(500)", "expected": "13942322456169788013904571641450669..."},
        ],
        expected_outputs={"t1": "6765", "t2": "12586269025", "t3": "354224848179261915075"},
        expected_approach="dynamic-programming-or-matrix-exponentiation",
        grader=MediumGrader(),
        grader_name="MediumGrader",
        starter_code={"python": "def fibonacci(n):\n    # Write your solution here\n    pass\n"},
    ),
    # Hard 2: Fibonacci Modulo
    Task(
        id="hard-2",
        difficulty="hard",
        problem="Return the nth Fibonacci number modulo 10^9+7 (n >= 0, n <= 10^6).",
        code="def fibonacci(n):\n    # Write your solution here\n    pass\n",
        test_cases=[
            {"name": "t1", "input": "fibonacci(1000000)", "expected": "517691607"},
            {"name": "t2", "input": "fibonacci(999999)", "expected": "1066340417491710595814572169..."},
        ],
        hidden_test_cases=[
            {"name": "h1", "input": "fibonacci(123456)", "expected": "..."},
        ],
        expected_outputs={"t1": "517691607", "t2": "1066340417491710595814572169..."},
        expected_approach="matrix-exponentiation-or-fast-doubling",
        grader=HardGrader(),
        grader_name="HardGrader",
        starter_code={"python": "def fibonacci(n):\n    # Write your solution here\n    pass\n"},
    ),
]


def get_tasks() -> List[Task]:
    return TASKS


def get_starter_code(task: Task, language: str) -> str:
    if task.starter_code and language in task.starter_code:
        return task.starter_code[language]
    return task.code

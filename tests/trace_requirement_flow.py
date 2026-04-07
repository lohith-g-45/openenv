import argparse
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api import app  # noqa: E402


def print_section(title: str) -> None:
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


DEFAULT_BROKEN_CODE = """
def two_sum(nums, target)
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return [seen[target - n], i]
        seen[n] = i
    return []
"""


DEFAULT_CORRECTED_CODE = """
def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
"""


DEFAULT_OPTIMIZED_CODE = """
def two_sum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return [seen[target - n], i]
        seen[n] = i
    return []
"""


def _read_multiline_from_prompt(label: str) -> str:
    print(f"\nEnter {label}. Finish with a single line containing only: EOF")
    lines = []
    while True:
        line = input()
        if line.strip() == "EOF":
            break
        lines.append(line)
    return "\n".join(lines) + "\n"


def _resolve_code(
    label: str,
    provided_code: str | None,
    file_path: str | None,
    default_code: str,
    interactive: bool,
) -> str:
    if provided_code:
        return provided_code

    if file_path:
        return Path(file_path).read_text(encoding="utf-8")

    if interactive:
        return _read_multiline_from_prompt(label)

    return default_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Trace the run->submit workflow with user-provided code snippets."
    )
    parser.add_argument("--difficulty", default="easy", choices=["easy", "medium", "hard"])
    parser.add_argument("--language", default="python", choices=["python", "c", "java"])
    parser.add_argument("--interactive", action="store_true", help="Prompt for code input.")

    parser.add_argument("--broken-code", help="Broken code as inline text.")
    parser.add_argument("--corrected-code", help="Corrected code as inline text.")
    parser.add_argument("--optimized-code", help="Optional optimized code as inline text.")

    parser.add_argument("--broken-file", help="Path to broken code file.")
    parser.add_argument("--corrected-file", help="Path to corrected code file.")
    parser.add_argument("--optimized-file", help="Path to optimized code file.")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    client = TestClient(app)

    broken_code = _resolve_code(
        "BROKEN code",
        args.broken_code,
        args.broken_file,
        DEFAULT_BROKEN_CODE,
        args.interactive,
    )
    corrected_code = _resolve_code(
        "CORRECTED code",
        args.corrected_code,
        args.corrected_file,
        DEFAULT_CORRECTED_CODE,
        args.interactive,
    )
    optimized_code = _resolve_code(
        "OPTIMIZED code",
        args.optimized_code,
        args.optimized_file,
        DEFAULT_OPTIMIZED_CODE,
        args.interactive,
    )

    print_section("1) RESET ENVIRONMENT")
    reset = client.post("/reset", json={"difficulty": args.difficulty, "language": args.language})
    print("status:", reset.status_code)
    print("task_id:", reset.json().get("task_id"))
    print("difficulty:", args.difficulty)
    print("language:", args.language)

    print_section("2) RUN WITH HALF/BROKEN CODE -> MUST DETECT ERROR + EXPLAIN")
    run_broken = client.post(
        "/run",
        json={
            "code": broken_code,
            "language": args.language,
            "attempt_number": 1,
            "want_full_explanation": True,
        },
    )
    rb = run_broken.json()["result"]
    print("status:", run_broken.status_code)
    print("syntax_valid:", rb.get("syntax_valid"))
    print("diagnostics_count:", len(rb.get("diagnostics", [])))
    if rb.get("diagnostics"):
        print("first_diagnostic:", rb["diagnostics"][0])
    print("has_bug_explanation:", bool(rb.get("bug_explanation")))

    print_section("3) RUN WITH CORRECT (BUT BRUTE-FORCE) CODE -> TOP 5 TESTS")
    run_correct = client.post(
        "/run",
        json={
            "code": corrected_code,
            "language": args.language,
            "attempt_number": 2,
            "want_full_explanation": False,
        },
    )
    rc = run_correct.json()["result"]
    summary = rc.get("run_test_summary", {})
    print("status:", run_correct.status_code)
    print("top_tests_executed:", summary.get("total"))
    print("passed:", summary.get("passed"), "failed:", summary.get("failed"))

    print_section("4) SUBMIT SAME CODE -> APPROACH/COMPLEXITY/OPTIMIZATION TRACE")
    submit = client.post(
        "/submit",
        json={
            "code": corrected_code,
            "language": args.language,
            "attempt_number": 2,
            "want_full_explanation": True,
        },
    )
    sr = submit.json()["result"]
    print("status:", submit.status_code)
    print("accepted:", sr.get("accepted"))
    print("approach_comparison:", sr.get("approach_comparison"))
    print("complexity_comparison:", sr.get("complexity_comparison"))
    print("optimization_needed:", sr.get("optimization_needed"))

    best = (sr.get("optimization") or {}).get("best")
    print("optimized_present:", bool(best))
    if best:
        print("optimized_approach:", best.get("approach"))
        snippet = (best.get("optimized_code") or "").strip().splitlines()[:6]
        print("optimized_code_snippet:")
        for line in snippet:
            print(line)

    print("has_dynamic_explanation:", bool(sr.get("dynamic_explanation")))

    print_section("5) OPTIONAL CHECK: ALREADY OPTIMIZED CODE")
    submit_opt = client.post(
        "/submit",
        json={
            "code": optimized_code,
            "language": args.language,
            "attempt_number": 1,
            "want_full_explanation": False,
        },
    )
    so = submit_opt.json()["result"]
    print("status:", submit_opt.status_code)
    print("accepted:", so.get("accepted"))
    print("approach_comparison:", so.get("approach_comparison"))
    print("complexity_comparison:", so.get("complexity_comparison"))
    print("optimization_needed:", so.get("optimization_needed"))

    print_section("TRACE COMPLETE")


if __name__ == "__main__":
    main()

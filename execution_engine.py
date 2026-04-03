"""
execution_engine.py
===================
Member 2: Analysis & Optimization Engineer
Intelligent Code Evaluation and Optimization Environment

Responsibilities:
  - Safe sandboxed code execution
  - Run predefined test cases
  - Capture pass/fail status and runtime errors
  - Deterministic, reproducible results
"""

import ast
import sys
import io
import time
import traceback
import signal
import threading
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EXECUTION_TIMEOUT_SECONDS = 5   # max time per test case
FORBIDDEN_MODULES = {
    "os", "sys", "subprocess", "shutil", "socket", "requests",
    "urllib", "http", "ftplib", "smtplib", "importlib", "eval",
    "exec", "open", "compile", "__import__",
}

SAFE_BUILTINS = {
    "abs", "all", "any", "bin", "bool", "bytes", "callable", "chr",
    "dict", "divmod", "enumerate", "filter", "float", "format",
    "frozenset", "getattr", "hasattr", "hash", "hex", "int", "isinstance",
    "issubclass", "iter", "len", "list", "map", "max", "min", "next",
    "oct", "ord", "pow", "print", "range", "repr", "reversed", "round",
    "set", "slice", "sorted", "str", "sum", "tuple", "type", "zip",
    "True", "False", "None", "NotImplemented", "Ellipsis",
    "ValueError", "TypeError", "IndexError", "KeyError", "AttributeError",
    "ZeroDivisionError", "RuntimeError", "StopIteration", "Exception",
    "OverflowError", "MemoryError", "RecursionError",
}


# ---------------------------------------------------------------------------
# Security: AST-based forbidden import checker
# ---------------------------------------------------------------------------

class ForbiddenImportVisitor(ast.NodeVisitor):
    """Walk the AST and flag any forbidden imports or dangerous builtins."""

    def __init__(self):
        self.violations: List[str] = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            root = alias.name.split(".")[0]
            if root in FORBIDDEN_MODULES:
                self.violations.append(f"Forbidden import: '{alias.name}' (line {node.lineno})")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            root = node.module.split(".")[0]
            if root in FORBIDDEN_MODULES:
                self.violations.append(
                    f"Forbidden import from: '{node.module}' (line {node.lineno})"
                )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Flag direct calls to eval / exec / __import__
        if isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec", "__import__"}:
            self.violations.append(
                f"Forbidden call: '{node.func.id}()' (line {node.lineno})"
            )
        self.generic_visit(node)


def _security_check(code: str) -> List[str]:
    """Return list of security violations found in code."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []   # syntax issues handled separately
    visitor = ForbiddenImportVisitor()
    visitor.visit(tree)
    return visitor.violations


# ---------------------------------------------------------------------------
# Timeout helper (cross-platform via threading)
# ---------------------------------------------------------------------------

class _TimeoutResult:
    def __init__(self):
        self.result = None
        self.error: Optional[str] = None
        self.timed_out = False


def _run_with_timeout(fn, timeout: float) -> _TimeoutResult:
    """Run *fn* in a daemon thread with a hard timeout."""
    outcome = _TimeoutResult()

    def _target():
        try:
            outcome.result = fn()
        except Exception as e:
            outcome.error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"

    t = threading.Thread(target=_target, daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        outcome.timed_out = True
    return outcome


# ---------------------------------------------------------------------------
# Safe Execution Core
# ---------------------------------------------------------------------------

def _build_safe_globals() -> Dict[str, Any]:
    """Build a restricted globals dict for exec."""
    builtins_dict = {name: __builtins__[name] if isinstance(__builtins__, dict)
                     else getattr(__builtins__, name, None)
                     for name in SAFE_BUILTINS
                     if (isinstance(__builtins__, dict) and name in __builtins__)
                        or hasattr(__builtins__, name)}
    return {"__builtins__": builtins_dict}


def run_code_string(
    code: str,
    input_data: Any = None,
    timeout: float = EXECUTION_TIMEOUT_SECONDS,
) -> Dict[str, Any]:
    """
    Execute *code* string safely and return a result dict.

    Returns
    -------
    {
        "success": bool,
        "output": str,          # stdout captured
        "error": str | None,    # exception message if any
        "runtime_ms": float,
        "security_violations": list[str],
        "timed_out": bool,
    }
    """
    result = {
        "success": False,
        "output": "",
        "error": None,
        "runtime_ms": 0.0,
        "security_violations": [],
        "timed_out": False,
    }

    # 1. Security scan
    violations = _security_check(code)
    if violations:
        result["error"] = "Security violations detected:\n" + "\n".join(violations)
        result["security_violations"] = violations
        return result

    # 2. Syntax check
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        result["error"] = f"SyntaxError: {e.msg} (line {e.lineno})"
        return result

    # 3. Execute inside thread with timeout
    captured_stdout = io.StringIO()
    safe_globals = _build_safe_globals()

    # Inject input data as a variable 'INPUT' for the submitted function to use
    if input_data is not None:
        safe_globals["INPUT"] = input_data

    def _exec_fn():
        old_stdout = sys.stdout
        sys.stdout = captured_stdout
        try:
            exec(compile(tree, "<solution>", "exec"), safe_globals)  # noqa: S102
        finally:
            sys.stdout = old_stdout

    start = time.perf_counter()
    outcome = _run_with_timeout(_exec_fn, timeout)
    elapsed_ms = (time.perf_counter() - start) * 1000

    result["runtime_ms"] = round(elapsed_ms, 3)
    result["output"] = captured_stdout.getvalue()
    result["timed_out"] = outcome.timed_out

    if outcome.timed_out:
        result["error"] = f"Execution timed out after {timeout}s"
    elif outcome.error:
        result["error"] = outcome.error
    else:
        result["success"] = True

    return result


# ---------------------------------------------------------------------------
# Test-Case Runner
# ---------------------------------------------------------------------------

def run_test_cases(
    solution_code: str,
    function_name: str,
    test_cases: List[Dict[str, Any]],
    timeout: float = EXECUTION_TIMEOUT_SECONDS,
) -> Dict[str, Any]:
    """
    Run *solution_code* against a list of test cases.

    Each test case dict must have:
        "inputs"   : positional args as a list  e.g. [[1,2,3], 6]
        "expected" : the expected return value

    Returns
    -------
    {
        "total": int,
        "passed": int,
        "failed": int,
        "results": [
            {
                "test_id": int,
                "inputs": ...,
                "expected": ...,
                "actual": ...,
                "passed": bool,
                "error": str | None,
                "runtime_ms": float,
                "timed_out": bool,
            }
        ]
    }
    """
    summary = {
        "total": len(test_cases),
        "passed": 0,
        "failed": 0,
        "results": [],
    }

    # Security & syntax gate
    violations = _security_check(solution_code)
    if violations:
        summary["error"] = "Security violations:\n" + "\n".join(violations)
        return summary

    try:
        tree = ast.parse(solution_code)
    except SyntaxError as e:
        summary["error"] = f"SyntaxError: {e.msg} (line {e.lineno})"
        return summary

    compiled = compile(tree, "<solution>", "exec")

    for idx, tc in enumerate(test_cases):
        inputs = tc.get("inputs", [])
        expected = tc.get("expected")

        tc_result = {
            "test_id": idx + 1,
            "inputs": inputs,
            "expected": expected,
            "actual": None,
            "passed": False,
            "error": None,
            "runtime_ms": 0.0,
            "timed_out": False,
        }

        safe_globals = _build_safe_globals()
        actual_holder = [None]
        error_holder = [None]

        def _exec_fn(
            _compiled=compiled,
            _globals=safe_globals,
            _fn=function_name,
            _args=inputs,
            _actual=actual_holder,
            _err=error_holder,
        ):
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            try:
                exec(_compiled, _globals)  # noqa: S102
                fn = _globals.get(_fn)
                if fn is None:
                    _err[0] = f"Function '{_fn}' not found in solution"
                    return
                _actual[0] = fn(*_args) if isinstance(_args, list) else fn(_args)
            except Exception as e:
                _err[0] = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
            finally:
                sys.stdout = old_stdout

        start = time.perf_counter()
        outcome = _run_with_timeout(_exec_fn, timeout)
        elapsed_ms = (time.perf_counter() - start) * 1000

        tc_result["runtime_ms"] = round(elapsed_ms, 3)
        tc_result["timed_out"] = outcome.timed_out

        if outcome.timed_out:
            tc_result["error"] = f"Timed out after {timeout}s"
        elif outcome.error:
            tc_result["error"] = outcome.error
        elif error_holder[0]:
            tc_result["error"] = error_holder[0]
        else:
            tc_result["actual"] = actual_holder[0]
            tc_result["passed"] = (actual_holder[0] == expected)

        if tc_result["passed"]:
            summary["passed"] += 1
        else:
            summary["failed"] += 1

        summary["results"].append(tc_result)

    return summary


# ---------------------------------------------------------------------------
# Phase 2 — Empirical Complexity Estimator
# ---------------------------------------------------------------------------

import math
import random

def empirical_complexity(
    code: str,
    function_name: str,
    input_generator,
    sizes: Optional[List[int]] = None,
    trials: int = 3,
    timeout: float = 2.0,
) -> Dict[str, Any]:
    """
    Estimate time complexity empirically by timing f(n) at increasing input sizes.

    Parameters
    ----------
    code             : str  — solution source
    function_name    : str  — name of function to benchmark
    input_generator  : callable(n) -> args list — generates input of size n
    sizes            : list of n values to test (default: [50, 200, 500, 2000])
    trials           : number of runs to average per size
    timeout          : per-run timeout in seconds

    Returns
    -------
    {
        "empirical_time":    str,   # "O(1)" | "O(log n)" | "O(n)" | "O(n log n)" | "O(n^2)" | "O(2^n)"
        "measured_ms":       dict,  # {size: avg_ms}
        "growth_ratios":     list,  # ratio of t(n*k) / t(n)
        "confidence":        str,   # "high" | "medium" | "low"
        "explanation":       str,
    }
    """
    if sizes is None:
        sizes = [50, 200, 500, 2000]

    # Security gate
    violations = _security_check(code)
    if violations:
        return {"empirical_time": "Unknown", "error": "Security violation"}

    try:
        tree     = ast.parse(code)
        compiled = compile(tree, "<empirical>", "exec")
    except SyntaxError as e:
        return {"empirical_time": "Unknown", "error": f"SyntaxError: {e.msg}"}

    measured: Dict[int, float] = {}

    for n in sizes:
        times = []
        for _ in range(trials):
            safe_globals   = _build_safe_globals()
            actual_holder  = [None]
            error_holder   = [None]
            args           = input_generator(n)

            def _fn(
                _cmp=compiled, _gl=safe_globals, _fn_name=function_name,
                _args=args, _ah=actual_holder, _eh=error_holder,
            ):
                import sys, io
                old_out = sys.stdout
                sys.stdout = io.StringIO()
                try:
                    exec(_cmp, _gl)  # noqa: S102
                    fn = _gl.get(_fn_name)
                    if fn:
                        _ah[0] = fn(*_args) if isinstance(_args, list) else fn(_args)
                except Exception as e:
                    _eh[0] = str(e)
                finally:
                    sys.stdout = old_out

            start   = time.perf_counter()
            outcome = _run_with_timeout(_fn, timeout)
            elapsed = (time.perf_counter() - start) * 1000

            if outcome.timed_out:
                measured[n] = timeout * 1000
                break
            if error_holder[0]:
                break
            times.append(elapsed)

        if times:
            measured[n] = round(sum(times) / len(times), 4)

    if len(measured) < 2:
        return {
            "empirical_time": "Unknown",
            "measured_ms": measured,
            "growth_ratios": [],
            "confidence": "low",
            "explanation": "Insufficient data points for curve fitting",
        }

    # Growth ratio analysis
    size_list = sorted(measured.keys())
    ratios    = []
    for i in range(1, len(size_list)):
        n0, n1 = size_list[i - 1], size_list[i]
        t0, t1 = measured[n0], measured[n1]
        scale  = n1 / n0
        if t0 > 0:
            ratios.append(round(t1 / t0, 3))

    # Classify by average growth ratio vs size ratio
    if not ratios:
        return {
            "empirical_time": "Unknown",
            "measured_ms": measured,
            "growth_ratios": [],
            "confidence": "low",
            "explanation": "Could not compute growth ratios",
        }

    avg_ratio = sum(ratios) / len(ratios)
    # Expected ratios for n scaling by 4x (50->200->4x)
    # O(1):       ratio ~1.0
    # O(log n):   ratio ~log(4)/log(1) ~ 1.4
    # O(n):       ratio ~4.0
    # O(n log n): ratio ~5.5
    # O(n^2):     ratio ~16
    # O(2^n):     ratio >> 100

    # Use the actual scale factor from first pair
    n0, n1 = size_list[0], size_list[1]
    scale   = n1 / n0    # typically 4x

    if avg_ratio < 1.3:
        complexity  = "O(1)"
        explanation = f"Runtime barely changes across sizes (ratio={avg_ratio:.2f}) — constant time"
        conf        = "high"
    elif avg_ratio < scale * 0.4:
        complexity  = "O(log n)"
        explanation = f"Runtime grows sub-linearly (ratio={avg_ratio:.2f} vs scale={scale:.1f}x) — logarithmic"
        conf        = "medium"
    elif avg_ratio < scale * 1.5:
        complexity  = "O(n)"
        explanation = f"Runtime scales linearly with input (ratio={avg_ratio:.2f} ~= scale {scale:.1f}x) — O(n)"
        conf        = "high"
    elif avg_ratio < scale * 2.5:
        complexity  = "O(n log n)"
        explanation = f"Runtime grows slightly super-linear (ratio={avg_ratio:.2f}) — O(n log n)"
        conf        = "medium"
    elif avg_ratio < scale ** 2 * 1.5:
        complexity  = "O(n^2)"
        explanation = f"Runtime grows quadratically (ratio={avg_ratio:.2f} ~= {scale:.1f}^2={scale**2:.0f}) — O(n^2)"
        conf        = "high"
    else:
        complexity  = "O(2^n) or worse"
        explanation = f"Runtime explodes exponentially (ratio={avg_ratio:.2f}) — avoid without memoization"
        conf        = "high"

    return {
        "empirical_time":  complexity,
        "measured_ms":     {str(k): v for k, v in measured.items()},
        "growth_ratios":   ratios,
        "confidence":      conf,
        "explanation":     explanation,
    }


# ---------------------------------------------------------------------------
# RL Environment Integration
# ---------------------------------------------------------------------------

def execute_action(action: Dict[str, Any]) -> Dict[str, Any]:
    """
    Unified entry point for the RL environment.

    Accepts an action dict with keys:
        "type"             : "run_code" | "run_tests" | "empirical"
        "code"             : str  — the solution source
        "function_name"    : str  — required for "run_tests" / "empirical"
        "test_cases"       : list — required for "run_tests"
        "input_generator"  : callable(n)->args — required for "empirical"
        "timeout"          : float (optional, default 5s)

    Returns a structured result dict the RL env can consume.
    """
    action_type = action.get("type", "run_code")
    code        = action.get("code", "")
    timeout     = float(action.get("timeout", EXECUTION_TIMEOUT_SECONDS))

    if action_type == "run_tests":
        return run_test_cases(
            solution_code=code,
            function_name=action.get("function_name", "solution"),
            test_cases=action.get("test_cases", []),
            timeout=timeout,
        )
    elif action_type == "empirical":
        return empirical_complexity(
            code=code,
            function_name=action.get("function_name", "solution"),
            input_generator=action.get("input_generator", lambda n: ([list(range(n))],)),
            sizes=action.get("sizes", [50, 200, 500, 2000]),
            trials=action.get("trials", 3),
            timeout=timeout,
        )
    else:
        return run_code_string(code, input_data=action.get("input_data"), timeout=timeout)


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Execution Engine Self-Test ===\n")

    sample = """
def solution(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return [seen[target - n], i]
        seen[n] = i
    return []
"""
    cases = [
        {"inputs": [[2, 7, 11, 15], 9], "expected": [0, 1]},
        {"inputs": [[3, 2, 4], 6],       "expected": [1, 2]},
        {"inputs": [[3, 3], 6],          "expected": [0, 1]},
        {"inputs": [[], 1],              "expected": []},
    ]

    result = run_test_cases(sample, "solution", cases)
    print(f"Total: {result['total']}  Passed: {result['passed']}  Failed: {result['failed']}")
    for r in result["results"]:
        status = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f"  Test {r['test_id']}: {status}  | actual={r['actual']}  | {r['runtime_ms']}ms")

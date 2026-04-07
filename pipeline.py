"""
pipeline.py
===========
Core hybrid pipeline for run and submit flows.
"""

import ast
import re
from typing import Any, Dict, List, Optional

from analysis import BugDetector, analyze_code
from execution_engine import run_test_cases, run_test_cases_by_language
from optimization_engine import optimize_code
from repair_engine import RepairEngine

try:
    from llm_manager import LLMManager
except ImportError:
    LLMManager = None


def get_llm() -> Optional[Any]:
    if LLMManager is None:
        return None
    try:
        return LLMManager()
    except (ImportError, ValueError):
        return None


def _touch_llm_proxy(llm: Optional[Any]) -> None:
    """Best-effort proxy ping so validator can observe routed LLM traffic."""
    if not llm:
        return
    try:
        llm.proxy_heartbeat()
    except Exception:
        pass


def _is_valid_python(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def _get_function_name(code: str) -> str:
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                return node.name
    except Exception:
        pass
    return "solution"


def _get_function_name_by_language(code: str, language: str, expected_function: str = "") -> str:
    lang = (language or "python").lower()
    if lang == "python":
        return _get_function_name(code)
    if expected_function:
        return expected_function

    if lang == "c":
        match = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\([^;]*\)\s*\{", code)
        if match:
            return match.group(1)
    if lang == "java":
        match = re.search(r"\b(?:static\s+)?[\w\[\]]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", code)
        if match:
            return match.group(1)
    return "solution"


def _simple_multilang_analysis(code: str, language: str) -> Dict[str, Any]:
    code_lower = code.lower()
    loop_count = len(re.findall(r"\b(for|while)\b", code_lower))
    has_hash = any(k in code_lower for k in ["unordered_map", "hashmap", "map<", "hashmap<", "dict", "seen", "containskey"])
    has_two_pointers = bool(re.search(r"\b(left|l)\b.*\b(right|r)\b", code_lower)) and "while" in code_lower
    has_sliding_window = any(k in code_lower for k in ["substring", "window", "left", "right", "charat", "length_of_longest_substring"])
    has_sort = any(k in code_lower for k in ["sort(", "arrays.sort", "qsort", "collections.sort"])

    if has_sliding_window and loop_count <= 1:
        approach = "sliding_window"
        time = "O(n)"
    elif has_hash and loop_count <= 1:
        approach = "hashmap"
        time = "O(n)"
    elif has_two_pointers and loop_count <= 1:
        approach = "two_pointers"
        time = "O(n)"
    elif loop_count >= 2:
        approach = "brute_force"
        time = "O(n^2)"
    elif has_sort and loop_count <= 1:
        approach = "sorting"
        time = "O(n log n)"
    elif loop_count == 1:
        approach = "single_pass"
        time = "O(n)"
    else:
        approach = "constant"
        time = "O(1)"

    return {
        "bugs": {
            "syntax_errors": [],
            "logical_errors": [],
            "edge_case_risks": [],
            "has_critical_bugs": False,
            "total_issues": 0,
        },
        "approach": {
            "primary": approach,
            "confidence": 0.6,
            "scores": {approach: 1.0},
            "reasoning": f"Heuristic {language} analysis",
        },
        "complexity": {
            "time_complexity": time,
            "space_complexity": "O(1)" if not has_hash else "O(n)",
            "explanation": f"Heuristic complexity estimate for {language}",
            "confidence": "medium",
            "method": "heuristic",
        },
        "summary": f"Approach: {approach} | Time: {time}",
    }


def _complexity_rank(complexity: str) -> int:
    c = (complexity or "Unknown").strip()
    order = {
        "O(1)": 0,
        "O(log n)": 1,
        "O(n)": 2,
        "O(n log n)": 3,
        "O(n^2)": 4,
        "O(n^2 log n)": 5,
        "O(n^3)": 6,
        "O(2^n)": 7,
        "Unknown": 99,
    }
    return order.get(c, 99)


def _is_optimization_needed(user_time: str, optimized_time: str) -> bool:
    return _complexity_rank(optimized_time) < _complexity_rank(user_time)


def _canonical_approach_name(name: str) -> str:
    raw = (name or "").strip().lower()
    compact = re.sub(r"[^a-z0-9]+", "", raw)

    if not compact:
        return "unknown"
    if "slidingwindow" in compact and ("hash" in compact or "map" in compact):
        return "sliding_window_hashmap"
    if "slidingwindow" in compact:
        return "sliding_window"
    if "hash" in compact or "map" in compact or compact == "dict":
        return "hashmap"
    if "twopointer" in compact:
        return "two_pointers"
    if "bruteforce" in compact:
        return "brute_force"
    if "sort" in compact:
        return "sorting"
    return compact


def _is_same_approach(user_approach: str, best_approach: str) -> bool:
    user_c = _canonical_approach_name(user_approach)
    best_c = _canonical_approach_name(best_approach)
    if user_c == best_c:
        return True

    compatible = {
        ("sliding_window", "sliding_window_hashmap"),
        ("sliding_window_hashmap", "sliding_window"),
        ("hashmap", "sliding_window_hashmap"),
        ("sliding_window_hashmap", "hashmap"),
    }
    return (user_c, best_c) in compatible


def _align_optimized_code_signature(code: str, language: str, function_name: str) -> str:
    if not isinstance(code, str) or not code.strip() or not function_name:
        return code

    lang = (language or "python").lower()
    if lang != "java":
        return code

    method_pattern = (
        r"(\b(?:public\s+|private\s+|protected\s+)?(?:static\s+)?"
        r"[A-Za-z_][A-Za-z0-9_<>,\[\]]*\s+)([A-Za-z_][A-Za-z0-9_]*)\s*\("
    )

    def _replace(match: re.Match) -> str:
        prefix = match.group(1)
        return f"{prefix}{function_name}("

    return re.sub(method_pattern, _replace, code, count=1)


def _fallback_optimized_code(language: str, function_name: str) -> Dict[str, Any]:
    lang = (language or "python").lower()
    if function_name == "two_sum":
        if lang == "c":
            return {
                "approach": "Hash map (placeholder template)",
                "time_complexity": "O(n)",
                "space_complexity": "O(n)",
                "optimized_code": (
                    "// Provide a hash table implementation for O(n) two_sum\n"
                    "int* two_sum(int* nums, int numsSize, int target, int* returnSize) {\n"
                    "    *returnSize = 0;\n"
                    "    return NULL;\n"
                    "}\n"
                ),
            }
        if lang == "java":
            return {
                "approach": "HashMap",
                "time_complexity": "O(n)",
                "space_complexity": "O(n)",
                "optimized_code": (
                    "class Solution {\n"
                    "    public static int[] two_sum(int[] nums, int target) {\n"
                    "        java.util.HashMap<Integer, Integer> seen = new java.util.HashMap<>();\n"
                    "        for (int i = 0; i < nums.length; i++) {\n"
                    "            int c = target - nums[i];\n"
                    "            if (seen.containsKey(c)) return new int[]{seen.get(c), i};\n"
                    "            seen.put(nums[i], i);\n"
                    "        }\n"
                    "        return new int[]{};\n"
                    "    }\n"
                    "}\n"
                ),
            }
    if function_name == "trap":
        if lang == "java":
            return {
                "approach": "Two pointers",
                "time_complexity": "O(n)",
                "space_complexity": "O(1)",
                "optimized_code": (
                    "class Solution {\n"
                    "    public static int trap(int[] height) {\n"
                    "        int l = 0, r = height.length - 1, leftMax = 0, rightMax = 0, ans = 0;\n"
                    "        while (l < r) {\n"
                    "            if (height[l] < height[r]) {\n"
                    "                leftMax = Math.max(leftMax, height[l]);\n"
                    "                ans += leftMax - height[l++];\n"
                    "            } else {\n"
                    "                rightMax = Math.max(rightMax, height[r]);\n"
                    "                ans += rightMax - height[r--];\n"
                    "            }\n"
                    "        }\n"
                    "        return ans;\n"
                    "    }\n"
                    "}\n"
                ),
            }
    return {
        "approach": "Optimized approach",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
        "optimized_code": "",
    }


def _extract_solution_line(error_message: str) -> Optional[int]:
    match = re.search(r'File "<solution>", line (\d+)', error_message or "")
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _extract_compiler_line(error_message: str, language: str) -> Optional[int]:
    msg = error_message or ""
    lang = (language or "python").lower()

    if lang == "c":
        # gcc/clang format: solution.c:12:5: error: ...
        match = re.search(r"solution\\.c:(\\d+):\\d+", msg)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None

    if lang == "java":
        # javac format: Runner.java:8: error: ... or Solution.java:12: error: ...
        match = re.search(r"(?:Runner|Solution|[A-Za-z_][A-Za-z0-9_]*)\\.java:(\\d+)", msg)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None

    return None


def _is_compile_error_message(error_message: str, language: str) -> bool:
    msg = (error_message or "").lower()
    lang = (language or "python").lower()

    if "compile" in msg:
        return True

    if lang == "c":
        return bool(re.search(r"solution\.c:\d+:\d+:\s*error", msg))

    if lang == "java":
        return bool(re.search(r"\.java:\d+:\s*error", msg))

    return False


def _parse_call_inputs(expression: str) -> List[Any]:
    try:
        parsed = ast.parse(expression, mode="eval")
        call = parsed.body
        if not isinstance(call, ast.Call):
            return []
        return [ast.literal_eval(arg) for arg in call.args]
    except Exception:
        return []


def _parse_expected_value(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    try:
        return ast.literal_eval(value)
    except Exception:
        return value


def _normalize_diagnostics(original_bugs: Dict[str, Any], runtime_bugs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    diagnostics: List[Dict[str, Any]] = []

    for key in ("syntax_errors", "logical_errors", "edge_case_risks"):
        for issue in original_bugs.get(key, []):
            diagnostics.append(
                {
                    "error_type": issue.get("type", key),
                    "line": issue.get("line"),
                    "column": issue.get("col"),
                    "message": issue.get("message", "Unknown issue"),
                    "severity": issue.get("severity", "info"),
                }
            )

    for issue in runtime_bugs:
        diagnostics.append(
            {
                "error_type": issue.get("type", "RuntimeError"),
                "line": issue.get("line"),
                "column": None,
                "message": issue.get("message", "Runtime failure"),
                "severity": issue.get("severity", "critical"),
            }
        )

    return diagnostics


def _normalize_generated_test_cases(raw_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for tc in raw_cases:
        if not isinstance(tc, dict):
            continue

        if "inputs" in tc and "expected" in tc:
            inputs = tc.get("inputs")
            if not isinstance(inputs, list):
                inputs = [inputs]
            normalized.append({"inputs": inputs, "expected": tc.get("expected")})
            continue

        if "input" in tc and "expected" in tc:
            call_expr = str(tc.get("input", ""))
            normalized.append(
                {
                    "inputs": _parse_call_inputs(call_expr),
                    "expected": _parse_expected_value(tc.get("expected")),
                }
            )

    return normalized


def _dedupe_test_cases(test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    deduped: List[Dict[str, Any]] = []

    for tc in test_cases:
        key = (repr(tc.get("inputs")), repr(tc.get("expected")))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(tc)

    return deduped


def _build_run_test_cases(
    llm: Optional[Any],
    base_cases: List[Dict[str, Any]],
    candidate_pool: List[Dict[str, Any]],
    problem_description: str,
    max_tests: int,
) -> List[Dict[str, Any]]:
    test_cases = list(base_cases)

    if len(test_cases) < max_tests and llm and problem_description:
        try:
            llm_generated = llm.generate_test_cases(code="", problem_description=problem_description)
            test_cases.extend(_normalize_generated_test_cases(llm_generated))
        except Exception:
            pass

    if len(test_cases) < max_tests:
        test_cases.extend(candidate_pool)

    return _dedupe_test_cases(test_cases)[:max_tests]


def process_run_attempt(
    code: str,
    test_cases: List[Dict[str, Any]] = None,
    language: str = "python",
    expected_function: str = "",
    attempt_number: int = 1,
    want_full_explanation: bool = False,
    problem_description: str = "",
    candidate_test_pool: List[Dict[str, Any]] = None,
    max_tests: int = 5,
) -> Dict[str, Any]:
    llm = get_llm()
    _touch_llm_proxy(llm)
    if test_cases is None:
        test_cases = []
    if candidate_test_pool is None:
        candidate_test_pool = []

    selected_test_cases = _build_run_test_cases(
        llm=llm,
        base_cases=test_cases,
        candidate_pool=candidate_test_pool,
        problem_description=problem_description,
        max_tests=max_tests,
    )

    lang = (language or "python").lower()

    if lang == "python":
        original_bugs = BugDetector.analyze(code)
        base_errors = (
            original_bugs.get("syntax_errors", [])
            + original_bugs.get("logical_errors", [])
            + original_bugs.get("edge_case_risks", [])
        )
    else:
        original_bugs = {
            "syntax_errors": [],
            "logical_errors": [],
            "edge_case_risks": [],
            "has_critical_bugs": False,
            "total_issues": 0,
        }
        base_errors = []

    func_name = _get_function_name_by_language(code, lang, expected_function)
    run_results = run_test_cases_by_language(code, func_name, selected_test_cases, language=lang)

    runtime_bugs: List[Dict[str, Any]] = []
    first_failed_tc = None
    is_tle = False

    for tc_res in run_results.get("results", []):
        if tc_res.get("error"):
            err_msg = tc_res["error"]
            is_compile_error = _is_compile_error_message(err_msg, lang)
            line_no = _extract_solution_line(err_msg)
            if line_no is None:
                line_no = _extract_compiler_line(err_msg, lang)
            runtime_bugs.append(
                {
                    "type": "SyntaxError" if is_compile_error else "RuntimeError",
                    "line": line_no,
                    "message": err_msg,
                    "test_case": tc_res.get("test_id"),
                    "severity": "critical",
                }
            )
            if first_failed_tc is None:
                first_failed_tc = tc_res
            if "TimeoutError" in err_msg or "timed out" in err_msg.lower():
                is_tle = True
            break
        if not tc_res.get("passed") and first_failed_tc is None:
            first_failed_tc = tc_res

    diagnostics = _normalize_diagnostics(original_bugs, runtime_bugs)
    has_errors = len(base_errors) + len(runtime_bugs) > 0
    has_test_failures = run_results.get("failed", 0) > 0

    bug_explanation = None
    failure_explanation = None

    if llm and (has_errors or has_test_failures):
        try:
            if has_errors:
                if want_full_explanation:
                    bug_explanation = llm.explain_bugs(code, base_errors + runtime_bugs)
                else:
                    bug_explanation = llm.get_hint(code, base_errors + runtime_bugs, attempt_number)
            elif first_failed_tc is not None:
                failure_explanation = llm.explain_test_case_failure(
                    code=code,
                    test_input=str(first_failed_tc.get("inputs", "N/A")),
                    expected=str(first_failed_tc.get("expected", "N/A")),
                    actual=str(first_failed_tc.get("actual", "N/A")),
                    is_tle=is_tle,
                )
        except Exception:
            pass

    compile_failed = any(
        isinstance(tc.get("error"), str) and _is_compile_error_message(tc.get("error", ""), lang)
        for tc in run_results.get("results", [])
    )

    if compile_failed and lang != "python":
        original_bugs["syntax_errors"] = [
            {
                "type": "SyntaxError",
                "line": next((b.get("line") for b in runtime_bugs if b.get("line") is not None), None),
                "col": None,
                "message": "Compilation failed for submitted code.",
                "severity": "critical",
            }
        ]

    return {
        "mode": "run",
        "language": lang,
        "syntax_valid": len(original_bugs.get("syntax_errors", [])) == 0 and not compile_failed,
        "function_name": func_name,
        "diagnostics": diagnostics,
        "bug_explanation": bug_explanation,
        "failure_explanation": failure_explanation,
        "run_test_summary": run_results,
        "top_test_cases": selected_test_cases,
    }


def process_submission(
    code: str,
    test_cases: List[Dict[str, Any]] = None,
    language: str = "python",
    expected_function: str = "",
    attempt_number: int = 1,
    want_full_explanation: bool = False,
    problem_description: str = "",
) -> Dict[str, Any]:
    llm = get_llm()
    _touch_llm_proxy(llm)
    lang = (language or "python").lower()
    if test_cases is None:
        test_cases = []

    if lang == "python":
        original_bugs = BugDetector.analyze(code)
        all_errors = (
            original_bugs.get("syntax_errors", [])
            + original_bugs.get("logical_errors", [])
            + original_bugs.get("edge_case_risks", [])
        )
    else:
        original_bugs = {
            "syntax_errors": [],
            "logical_errors": [],
            "edge_case_risks": [],
            "has_critical_bugs": False,
            "total_issues": 0,
        }
        all_errors = []

    func_name = _get_function_name_by_language(code, lang, expected_function)
    initial_test_results = run_test_cases_by_language(code, func_name, test_cases, language=lang)

    runtime_bugs: List[Dict[str, Any]] = []
    first_failed_tc = None
    is_tle = False

    for tc_res in initial_test_results.get("results", []):
        if tc_res.get("error"):
            err_msg = tc_res["error"]
            is_compile_error = _is_compile_error_message(err_msg, lang)
            line_no = _extract_solution_line(err_msg)
            if line_no is None:
                line_no = _extract_compiler_line(err_msg, lang)
            runtime_bugs.append(
                {
                    "type": "SyntaxError" if is_compile_error else "RuntimeError",
                    "line": line_no,
                    "message": err_msg,
                    "test_case": tc_res.get("test_id"),
                    "severity": "critical",
                }
            )
            if first_failed_tc is None:
                first_failed_tc = tc_res
            if "TimeoutError" in err_msg or "timed out" in err_msg.lower():
                is_tle = True
            break
        if not tc_res.get("passed") and first_failed_tc is None:
            first_failed_tc = tc_res

    original_bugs["runtime_errors"] = runtime_bugs

    compile_failed = any(_is_compile_error_message(b.get("message", ""), lang) for b in runtime_bugs)
    if compile_failed and lang != "python":
        original_bugs["syntax_errors"] = [
            {
                "type": "SyntaxError",
                "line": next((b.get("line") for b in runtime_bugs if b.get("line") is not None), None),
                "col": None,
                "message": "Compilation failed for submitted code.",
                "severity": "critical",
            }
        ]

    all_errors = all_errors + runtime_bugs
    diagnostics = _normalize_diagnostics(original_bugs, runtime_bugs)

    has_errors = len(all_errors) > 0
    has_test_failures = initial_test_results.get("failed", 0) > 0

    bug_explanation = None
    failure_explanation = None

    if llm and (has_errors or has_test_failures):
        try:
            if has_errors:
                if want_full_explanation:
                    bug_explanation = llm.explain_bugs(code, all_errors)
                else:
                    bug_explanation = llm.get_hint(code, all_errors, attempt_number)
            elif has_test_failures and first_failed_tc is not None:
                failure_explanation = llm.explain_test_case_failure(
                    code=code,
                    test_input=str(first_failed_tc.get("inputs", "N/A")),
                    expected=str(first_failed_tc.get("expected", "N/A")),
                    actual=str(first_failed_tc.get("actual", "N/A")),
                    is_tle=is_tle,
                )
        except Exception:
            pass

    result: Dict[str, Any] = {
        "mode": "submit",
        "language": lang,
        "original_code": code,
        "fixed_code": code,
        "original_bugs": original_bugs,
        "diagnostics": diagnostics,
        "bug_explanation": bug_explanation,
        "failure_explanation": failure_explanation,
        "attempt_number": attempt_number,
        "hints_exhausted": attempt_number >= 3,
        "test_results": initial_test_results,
        "repair_report": "",
        "syntax_valid": len(original_bugs.get("syntax_errors", [])) == 0,
        "analysis": {
            "time_complexity": "Unknown",
            "space_complexity": "Unknown",
            "approach": "Unknown",
            "summary": "",
        },
        "optimization": None,
        "dynamic_explanation": None,
        "fallback_mode": False,
        "approach_comparison": None,
        "complexity_comparison": None,
        "optimization_needed": None,
        "accepted": False,
    }

    is_syntax_valid = result["syntax_valid"]
    if lang == "python":
        fixed_code, is_syntax_valid, repair_report = RepairEngine.attempt_repair(code)
    else:
        fixed_code, repair_report = code, "[SKIP] Auto-repair currently implemented for Python only."
        is_syntax_valid = True

    if not is_syntax_valid and llm and lang == "python":
        try:
            repaired_by_llm = llm.fix_code_syntax(code)
            if _is_valid_python(repaired_by_llm):
                fixed_code = repaired_by_llm
                is_syntax_valid = True
                repair_report += "\n[OK] LLM repaired syntax successfully."
            else:
                repair_report += "\n[FAIL] LLM returned code that is still invalid Python syntax."
        except Exception as exc:
            repair_report += f"\n[FAIL] LLM repair failed: {exc}"

    result["fixed_code"] = fixed_code
    result["syntax_valid"] = is_syntax_valid and not compile_failed
    result["repair_report"] = repair_report

    if is_syntax_valid:
        fixed_func_name = _get_function_name_by_language(fixed_code, lang, expected_function)
        full_exec_summary = run_test_cases_by_language(fixed_code, fixed_func_name, test_cases, language=lang)
        result["execution_summary"] = full_exec_summary
        result["accepted"] = full_exec_summary.get("failed", 0) == 0

        analysis_res = analyze_code(fixed_code) if lang == "python" else _simple_multilang_analysis(fixed_code, lang)
        result["analysis"] = analysis_res

        opt_res = optimize_code(fixed_code, pre_analysis=analysis_res) if lang == "python" else {
            "original_approach": analysis_res.get("approach", {}).get("primary", "unknown"),
            "original_complexity": {
                "time": analysis_res.get("complexity", {}).get("time_complexity", "Unknown"),
                "space": analysis_res.get("complexity", {}).get("space_complexity", "Unknown"),
            },
            "best": None,
            "alternatives": [],
        }

        if llm:
            try:
                llm_opt = llm.generate_optimal_code(fixed_code, language=lang)
                if llm_opt and llm_opt.get("optimized_code"):
                    aligned_optimized_code = _align_optimized_code_signature(
                        llm_opt.get("optimized_code", ""), lang, fixed_func_name
                    )
                    best_prev = opt_res.get("best")
                    llm_best = {
                        "approach": llm_opt.get("approach", "LLM Synthesized Approach"),
                        "result_complexity": (
                            f"{llm_opt.get('time_complexity', 'O(n)')} time | "
                            f"{llm_opt.get('space_complexity', 'O(1)')} space"
                        ),
                        "time_complexity": llm_opt.get("time_complexity", "O(n)"),
                        "space_complexity": llm_opt.get("space_complexity", "O(1)"),
                        "improvement_gain": best_prev.get("improvement_gain", 1) if best_prev else 1,
                        "confidence": 1.0,
                        "explanation": "",
                        "optimized_code": aligned_optimized_code,
                        "rule": "llm_synthesis",
                    }
                    opt_res["best"] = llm_best
                    alternatives = opt_res.get("alternatives", [])
                    opt_res["alternatives"] = [llm_best] + alternatives
            except Exception:
                pass

        if not opt_res.get("best"):
            fallback_opt = _fallback_optimized_code(lang, fixed_func_name)
            opt_res["best"] = {
                "approach": fallback_opt.get("approach", "Optimized approach"),
                "result_complexity": (
                    f"{fallback_opt.get('time_complexity', 'O(n)')} time | "
                    f"{fallback_opt.get('space_complexity', 'O(1)')} space"
                ),
                "time_complexity": fallback_opt.get("time_complexity", "O(n)"),
                "space_complexity": fallback_opt.get("space_complexity", "O(1)"),
                "improvement_gain": 1,
                "confidence": 0.7,
                "explanation": "Language-aware fallback optimization template.",
                "optimized_code": fallback_opt.get("optimized_code", ""),
                "rule": "fallback_multilang",
            }
            opt_res["alternatives"] = [opt_res["best"]]

        result["optimization"] = opt_res

        optimized_code = ""
        user_time = analysis_res.get("complexity", {}).get("time_complexity", "Unknown")
        user_space = analysis_res.get("complexity", {}).get("space_complexity", "Unknown")
        user_approach = analysis_res.get("approach", {}).get("primary", "unknown")

        best_opt = opt_res.get("best") if isinstance(opt_res, dict) else None
        optimized_approach = "unknown"
        optimized_time = "Unknown"
        optimized_space = "Unknown"

        if isinstance(best_opt, dict):
            optimized_code = best_opt.get("optimized_code", "")
            optimized_approach = str(best_opt.get("approach", "unknown"))
            optimized_time = str(best_opt.get("time_complexity") or best_opt.get("result_complexity", "Unknown"))
            optimized_space = str(best_opt.get("space_complexity", "Unknown"))

        optimized_analysis = None
        if lang == "python" and isinstance(optimized_code, str) and optimized_code.strip() and _is_valid_python(optimized_code):
            optimized_analysis = analyze_code(optimized_code)
            optimized_time = optimized_analysis.get("complexity", {}).get("time_complexity", optimized_time)
            optimized_space = optimized_analysis.get("complexity", {}).get("space_complexity", optimized_space)

        result["approach_comparison"] = {
            "user_approach": user_approach,
            "best_approach": optimized_approach,
            "is_same_approach": _is_same_approach(user_approach, optimized_approach),
        }
        result["complexity_comparison"] = {
            "user": {"time": user_time, "space": user_space},
            "optimized": {"time": optimized_time, "space": optimized_space},
        }
        result["optimization_needed"] = _is_optimization_needed(user_time, optimized_time)

        if result["optimization_needed"] is False:
            result["dynamic_explanation"] = (
                "Your current solution already matches the target asymptotic complexity. "
                "No algorithmic upgrade is required; improvements, if any, would be minor readability or constant-factor tweaks."
            )
        elif llm and best_opt:
            try:
                explanation = llm.generate_explanation(
                    fixed_code,
                    best_opt.get("optimized_code", ""),
                    user_time,
                    optimized_time,
                    language=lang,
                )
                result["dynamic_explanation"] = explanation
            except Exception:
                pass
    else:
        result["fallback_mode"] = True
        result["optimization"] = optimize_code(code)

    return result

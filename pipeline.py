"""
pipeline.py
===========
Member 2: Analysis & Optimization Engineer
Intelligent Code Evaluation and Optimization Environment

Master Pipeline:
1. Try fixing Syntax & Logic Bugs
2. Re-Analyze fixed code
3. Optimize fixed code
4. (Fallback): If unfixable, use string heuristics to guess approach and provide solutions
"""

import ast
from typing import List, Dict, Any, Optional

from analysis import BugDetector, analyze_code
from repair_engine import RepairEngine
from optimization_engine import optimize_code
from execution_engine import run_test_cases

# Try to load LLM Manager
try:
    from llm_manager import LLMManager
    # Do not instantiate yet so we don't crash on import if key is missing
except ImportError:
    LLMManager = None

def get_llm() -> Optional[Any]:
    if LLMManager is None:
        return None
    try:
        return LLMManager()
    except (ImportError, ValueError):
        return None


def _is_valid_python(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False

from analysis import BugDetector, analyze_code

# ... existing code ...

def _get_function_name(code: str) -> str:
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                return node.name
    except:
        pass
    return "solution"

def process_submission(code: str, test_cases: List[Dict[str, Any]] = None,
                       attempt_number: int = 1, want_full_explanation: bool = False) -> Dict[str, Any]:
    """
    Runs the HYBRID end-to-end evaluation pipeline with AI Tutor v2 progressive hints.
    """
    llm = get_llm()
    if test_cases is None:
        test_cases = []
    
    # 1. Static Analysis
    original_bugs = BugDetector.analyze(code)
    all_errors = (original_bugs.get("syntax_errors", []) +
                  original_bugs.get("logical_errors", []) +
                  original_bugs.get("edge_case_risks", []))

    # 2. Run Tests on Original Code to find runtime errors
    func_name = _get_function_name(code)
    initial_test_results = run_test_cases(code, func_name, test_cases)
    
    # 3. Capture Runtime Tracebacks/Crashes
    runtime_bugs = []
    first_failed_tc = None
    is_tle = False

    for tc_res in initial_test_results.get("results", []):
        if tc_res.get("error"):
            err_msg = tc_res["error"]
            runtime_bugs.append({
                "type": "RuntimeError",
                "message": err_msg,
                "test_case": tc_res.get("test_id"),
                "severity": "critical"
            })
            if first_failed_tc is None:
                first_failed_tc = tc_res
            # Detect TLE by checking error message
            if "TimeoutError" in err_msg or "timed out" in err_msg.lower():
                is_tle = True
            break 
        elif not tc_res.get("passed") and first_failed_tc is None:
            first_failed_tc = tc_res

    original_bugs["runtime_errors"] = runtime_bugs
    all_errors = all_errors + runtime_bugs

    has_errors = len(all_errors) > 0
    has_test_failures = initial_test_results.get("failed", 0) > 0

    # 4. AI Tutor — Progressive Hint System
    #    Two distinct modes: (A) Error mode,  (B) Test-failure mode
    bug_explanation = None
    failure_explanation = None

    if llm and (has_errors or has_test_failures):
        try:
            # MODE A: Code has error (syntax / logic / runtime crash)
            if has_errors:
                if want_full_explanation:
                    bug_explanation = llm.explain_bugs(code, all_errors)
                else:
                    bug_explanation = llm.get_hint(code, all_errors, attempt_number)

            # MODE B: No code error, but a test case produced wrong output or TLE
            elif has_test_failures and first_failed_tc is not None:
                actual_output = str(first_failed_tc.get("actual", "N/A"))
                expected_output = str(first_failed_tc.get("expected", "N/A"))
                test_input = str(first_failed_tc.get("input", "N/A"))
                failure_explanation = llm.explain_test_case_failure(
                    code=code,
                    test_input=test_input,
                    expected=expected_output,
                    actual=actual_output,
                    is_tle=is_tle
                )
        except Exception as e:
            print(f"WARNING: LLM tutor failed: {e}")

    # 5. Initialize result with the initial findings
    result = {
        "original_code": code,
        "fixed_code": code,
        "original_bugs": original_bugs,
        "bug_explanation": bug_explanation,         # Error hints (progressive)
        "failure_explanation": failure_explanation,  # Test case failure reason
        "attempt_number": attempt_number,
        "hints_exhausted": attempt_number >= 3,
        "test_results": initial_test_results,
        "repair_report": "",
        "syntax_valid": len(original_bugs.get("syntax_errors", [])) == 0,
        "test_cases": initial_test_results.get("results") or [],
        "execution_summary": {
            "passed": initial_test_results.get("passed", 0),
            "total": initial_test_results.get("total", 0)
        },
        "analysis": {
            "time_complexity": "Unknown",
            "space_complexity": "Unknown",
            "approach": "Unknown",
            "summary": ""
        },
        "optimization": None,
        "dynamic_explanation": None,
        "fallback_mode": False
    }

    # 6. ATTEMPT REPAIR & OPTIMIZATION (ONLY if it was worth repairing)
    is_syntax_valid = result["syntax_valid"]
    fixed_code, is_syntax_valid, repair_report = RepairEngine.attempt_repair(code)
    
    if not is_syntax_valid and llm:
        try:
            fixed_code = llm.fix_code_syntax(code)
            if _is_valid_python(fixed_code):
                is_syntax_valid = True
                repair_report += "\n[OK] LLM repaired syntax successfully."
            else:
                is_syntax_valid = False
                repair_report += "\n[FAIL] LLM returned code that is still invalid Python syntax."
        except Exception as e:
            repair_report += f"\n[FAIL] LLM repair failed: {str(e)}"
            
    result["fixed_code"] = fixed_code
    result["syntax_valid"] = is_syntax_valid
    result["repair_report"] = repair_report

    if is_syntax_valid:
        # 2. GENERATE TEST CASES (LLM Oracle)
        if llm:
            try:
                test_cases = llm.generate_test_cases(fixed_code)
                result["test_cases"] = test_cases
            except Exception as e:
                print(f"LLM Test Gen Error: {e}")
        
        # 3. EXECUTE CODE (Deterministic Sandbox - safe from infinite loops)
        # We need the function name. A simple ast parse helps:
        func_name = "solution"
        try:
            for n in ast.walk(ast.parse(fixed_code)):
                if isinstance(n, ast.FunctionDef):
                    func_name = n.name
                    break
        except SyntaxError:
            pass
            
        if result["test_cases"]:
            exec_summary = run_test_cases(fixed_code, func_name, result["test_cases"])
            result["execution_summary"] = exec_summary

        # 4. BIG-O ANALYSIS & OPTIMIZATION (Deterministic Math + LLM Fusion)
        analysis_res = analyze_code(fixed_code)
        result["analysis"] = analysis_res
        
        # Primary Optimization Search (Deterministic Rules First)
        # We still run these to populate 'alternatives', but the 'best' will be LLM-driven if available.
        opt_res = optimize_code(fixed_code, pre_analysis=analysis_res)
        
        # 4.5 MANDATORY LLM SYNTHESIS
        # Now we ALWAYS utilize Groq for synthesizing the absolute best code approach.
        if llm:
            print("Utilizing Llama-3.3-70B for absolute-optimal code synthesis...")
            try:
                llm_opt = llm.generate_optimal_code(fixed_code)
                if llm_opt:
                    # The LLM's custom code now becomes our primary recommendation
                    opt_res["best"] = {
                        "approach": llm_opt.get("approach", "LLM Synthesized Approach"),
                        "result_complexity": f"{llm_opt.get('time_complexity', 'O(n)')} time | {llm_opt.get('space_complexity', 'O(1)')} space",
                        "improvement_gain": opt_res["best"]["improvement_gain"] if opt_res["best"] else 1, # math score
                        "confidence": 1.0, # Complete AI confidence
                        "explanation": "", # Will be filled by dynamic explainer below
                        "optimized_code": llm_opt.get("optimized_code", ""),
                        "rule": "llm_synthesis"
                    }
                    # Ensure it is at the front of the list
                    opt_res["alternatives"].insert(0, opt_res["best"])
            except Exception as e:
                print(f"LLM Synthesis Error: {e}")

        result["optimization"] = opt_res
        
        # 5. DYNAMIC EXPLANATION (LLM Tutoring)
        if llm and opt_res["best"]:
            try:
                orig_time = analysis_res["complexity"]["time_complexity"]
                opt_time = opt_res["best"]["result_complexity"]
                opt_code_str = opt_res["best"]["optimized_code"]
                explanation = llm.generate_explanation(fixed_code, opt_code_str, orig_time, opt_time)
                result["dynamic_explanation"] = explanation
            except Exception as e:
                print(f"LLM Explanation Error: {e}")

    else:
        # FALLBACK INFERENCE (Text-based guessing if syntax is hopelessly broken and LLM unavailable)
        result["fallback_mode"] = True
        result["optimization"] = optimize_code(code)

    return result

if __name__ == "__main__":
    print("="*70)
    print("  OPENENV HYBRID PIPELINE TEST")
    print("="*70)
    
    fixable_code = """
def max_subarray(nums)
    max_len = 0
    for i in range(len(nums))
        for j in range(i, len(nums))
            if sum(nums[i:j+1]) > 0
                max_len = max(max_len, j - i + 1)
    return max_len
"""
    r1 = process_submission(fixable_code)
    print(r1["repair_report"])
    print("Identified Approach:", r1["optimization"]["original_approach"])
    if r1["optimization"]["best"]:
        print("Best Optimization:", r1["optimization"]["best"]["approach"])
        
        
    print("\n" + "="*60)
    print("SCENARIO 2: TOTALLY UNFIXABLE GIBBERISH (FALLBACK INFERENCE)")
    print("="*60)
    
    unfixable_code = """
idk what to do man
im trying to find the two sum target complement pair difference
return 
{ [ [[ }
"""
    r2 = process_submission(unfixable_code)
    print(r2["repair_report"])
    print("Fallback Mode:", r2["fallback_mode"])
    print("Identified Approach:", r2["optimization"]["original_approach"])
    if r2["optimization"]["best"]:
        print("Deduced Best Optimization:", r2["optimization"]["best"]["approach"])
        print("Other Options:", len(r2["optimization"]["alternatives"]))

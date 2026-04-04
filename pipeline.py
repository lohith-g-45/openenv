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
from typing import Dict, Any, Optional

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

def process_submission(code: str) -> Dict[str, Any]:
    """
    Runs the HYBRID end-to-end evaluation pipeline.
    LLM Handles: Test Cases, Complex Syntax Repair, Dynamic Explanations.
    Deterministic Engine Handles: Safe Sandbox Execution, Big-O Analysis, Optimization Templates.
    """
    llm = get_llm()
    result = {
        "original_code": code,
        "fixed_code": code,
        "repair_report": "",
        "syntax_valid": False,
        "test_cases": [],
        "execution_summary": None,
        "analysis": None,
        "optimization": None,
        "dynamic_explanation": None,
        "fallback_mode": False
    }

    # 1. ATTEMPT REPAIR (Deterministic First, LLM Second)
    fixed_code, is_syntax_valid, repair_report = RepairEngine.attempt_repair(code)
    
    if not is_syntax_valid and llm:
        repair_report += "\n[LLM] Attempting structural syntax repair..."
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

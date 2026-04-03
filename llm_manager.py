"""
llm_manager.py
==============
Member 2: Analysis & Optimization Engineer
Intelligent Code Evaluation and Optimization Environment

Groq LLM wrapper for tasks that deterministic algorithms struggle with:
1. Complex Syntax Repair
2. Deductive Test Case Generation (Oracle)
3. Personalized Tutoring Explanations

Requires: `pip install groq` and `GROQ_API_KEY` in environment variables.
"""

import os
import json
from typing import Dict, Any, List

try:
    from groq import Groq
except ImportError:
    Groq = None

# Try to load python-dotenv to read .env file automatically
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class LLMManager:
    # Use Llama-3.3-70B-Versatile for maximum coding intelligence and accuracy.
    DEFAULT_MODEL = "llama-3.3-70b-versatile"

    def __init__(self):
        if Groq is None:
            raise ImportError("The 'groq' package is not installed. Please try 'pip install groq'.")
        
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY environment variable is missing. "
                "Please export GROQ_API_KEY='your_key' before running the pipeline."
            )
        self.client = Groq(api_key=self.api_key)

    def _call_llm(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        """Helper to call Groq API"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response_format = {"type": "json_object"} if json_mode else None
        
        response = self.client.chat.completions.create(
            model=self.DEFAULT_MODEL,
            messages=messages,
            response_format=response_format,
            temperature=0.0, # We want deterministic-ish, straight answers
        )
        return response.choices[0].message.content

    def fix_code_syntax(self, code: str) -> str:
        """
        Takes structurally broken code and uses LLaMa to apply minimal syntax fixes 
        while preserving the user's intended approach.
        """
        sys_prompt = (
            "You are a strict code repair assistant. The user will provide broken Python code. "
            "Your ONLY job is to fix syntax errors (missing colons, bad indentation, typos) "
            "so that the code is compilable. Do NOT fully rewrite the algorithm or "
            "change their variable names. "
            "Return ONLY the fixed raw Python code with no markdown formatting, no backticks, "
            "and no explanations. Just code."
        )
        
        fixed_code = self._call_llm(sys_prompt, code)
        
        # Cleanup potential markdown wrappers just in case LLaMa misbehaves
        fixed_code = fixed_code.replace("```python", "").replace("```", "").strip()
        return fixed_code

    def generate_test_cases(self, code: str) -> List[Dict[str, Any]]:
        """
        Reads unknown code, deduces the problem, and generates LeetCode-style test cases.
        Returns strict JSON list: [{"inputs": [...], "expected": ...}]
        """
        sys_prompt = (
            "You are an algorithm testing oracle. Read the user's Python function. "
            "Deduce what Leetcode-style problem they are trying to solve. "
            "Generate exactly 4 edge-case test cases for this function. "
            "You MUST output valid JSON only. The JSON must be an object with a 'test_cases' key "
            "containing a list. Each item in the list must have 'inputs' (a list of arguments) "
            "and 'expected' (the expected return value). "
            "Example format: {\"test_cases\": [{\"inputs\": [[2,7,11,15], 9], \"expected\": [0,1]}]}"
        )
        
        response = self._call_llm(sys_prompt, f"Code:\n{code}", json_mode=True)
        try:
            data = json.loads(response)
            return data.get("test_cases", [])
        except json.JSONDecodeError:
            print("WARNING: LLM failed to return valid JSON test cases.")
            return []

    def generate_explanation(self, buggy_code: str, optimized_code: str, original_time: str, opt_time: str) -> str:
        """
        Generates a personalized, highly-detailed tutoring explanation comparing their code to the optimized version.
        """
        sys_prompt = (
            "You are an expert, world-class algorithm professor. The user wrote a slow/buggy solution, "
            "and our system has identified a highly optimized approach. "
            "Your task is to provide a MASSIVE, deeply educational response: "
            "1. Briefly explain WHY their original code is slow (referring to their specific variables). "
            "2. Provide an IN-DEPTH, highly theoretical explanation of the new Optimised Approach. "
            "   Explain EXACTLY how this data structure or algorithm works under the hood, step-by-step. "
            "   Explain specifically WHY this is the absolute best approach for this specific problem compared to alternatives. "
            "3. Output the complete, beautifully formatted Optimised Code. "
            "Do not just talk about Big-O; explain the deep logic and mechanics of the approach."
        )
        
        user_prompt = f"Original Code ({original_time}):\n{buggy_code}\n\nOur Optimized Template ({opt_time}):\n{optimized_code}"
        
        explanation = self._call_llm(sys_prompt, user_prompt)
        return explanation


    def generate_optimal_code(self, code: str) -> Dict[str, Any]:
        """
        Synthesizes the optimal approach organically from LLaMa-3 instead of using a hardcoded template.
        Returns a strict JSON Dict: {
            "approach": "Name of approach",
            "time_complexity": "O(...)",
            "space_complexity": "O(...)",
            "optimized_code": "raw code string"
        }
        """
        sys_prompt = (
            "You are a world-class senior algorithm engineer at a top-tier tech company. "
            "Your task is to rewrite the following Python code to be as efficient as possible. "
            "You must handle all edge cases (empty lists, single elements, etc.) correctly. "
            "Return ONLY a strictly valid JSON object with these exact keys: "
            "'approach' (Clear name of the optimization pattern used), "
            "'time_complexity' (Mathematically correct Big-O, e.g., O(n)), "
            "'space_complexity' (Mathematically correct Big-O, e.g., O(1)), "
            "'optimized_code' (Clean, production-grade Python code without comments unless necessary). "
            "Ensure the code is a complete, runnable function with the same name as the original. "
        )
        
        response = self._call_llm(sys_prompt, f"Code:\n{code}", json_mode=True)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            print("WARNING: LLM failed to return valid JSON optimal code.")
            return {}

# --- Self Test ---
if __name__ == "__main__":
    # Note: Requires GROQ_API_KEY
    llm = LLMManager()
    
    broken_code = "def two_sum(nums, t)\nfor i in range(len(n)):\n if nums[i] == t: return i\nreturn -1"
    print("Testing Repair...")
    fixed = llm.fix_code_syntax(broken_code)
    print(fixed)
    
    print("\nTesting Test Case Gen...")
    tests = llm.generate_test_cases(fixed)
    print(json.dumps(tests, indent=2))

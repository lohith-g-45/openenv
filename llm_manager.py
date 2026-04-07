"""
llm_manager.py
==============
Member 2: Analysis & Optimization Engineer
Intelligent Code Evaluation and Optimization Environment

Proxy-routed OpenAI wrapper for tasks that deterministic algorithms struggle with:
1. Complex Syntax Repair
2. Deductive Test Case Generation (Oracle)
3. Personalized Tutoring Explanations
"""

import os
import json
from typing import Dict, Any, List

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# Try to load python-dotenv to read .env file automatically
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class LLMManager:
    """
    LLM Manager using standard OpenAI client through injected LiteLLM proxy.
    Required env: API_BASE_URL, API_KEY. Optional: MODEL_NAME.
    """

    def __init__(self):
        if OpenAI is None:
            raise ImportError("The 'openai' package is not installed. Please try 'pip install openai'.")
        
        # Phase-2 compliance: all LLM traffic must go through injected proxy.
        self.base_url = os.getenv("API_BASE_URL")
        self.api_key = os.getenv("API_KEY")
        self.model_name = os.getenv("MODEL_NAME", "gpt-4o-mini")

        if not self.base_url or not self.api_key:
            raise ValueError(
                "Compliance Error: Missing required environment variables. "
                "Ensure API_BASE_URL and API_KEY are set."
            )

        # Initialize standard OpenAI client
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def _call_llm(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        """Helper to call completion API using standard OpenAI format"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response_format = {"type": "json_object"} if json_mode else None
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            response_format=response_format,
            temperature=0.0,
        )
        return response.choices[0].message.content

    def proxy_heartbeat(self) -> bool:
        """Best-effort no-op call to verify proxy path is reachable."""
        try:
            self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
                temperature=0.0,
            )
            return True
        except Exception:
            return False

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

    def generate_test_cases(self, code: str, problem_description: str = "") -> List[Dict[str, Any]]:
        """
        Reads the problem description (and optionally code) and generates LeetCode-style test cases.
        Returns strict JSON list: [{"input": "func_call(...)", "expected": "result"}]
        """
        context = problem_description if problem_description else f"Code:\n{code}"
        sys_prompt = (
            "You are an algorithm testing oracle. Read the problem below. "
            "Generate exactly 4 diverse test cases including edge cases. "
            "Return ONLY valid JSON with a 'test_cases' key. "
            "Each item must have 'input' (a string: the exact function call, e.g. \"two_sum([2,7,11,15], 9)\") "
            "and 'expected' (string representation of expected return value, e.g. \"[0, 1]\"). "
            "Example: {\"test_cases\": [{\"input\": \"two_sum([2,7,11,15], 9)\", \"expected\": \"[0, 1]\"}]}"
        )
        response = self._call_llm(sys_prompt, context, json_mode=True)
        try:
            data = json.loads(response)
            return data.get("test_cases", [])
        except json.JSONDecodeError:
            print("WARNING: LLM failed to return valid JSON test cases.")
            return []

    def generate_explanation(self, buggy_code: str, optimized_code: str, original_time: str, opt_time: str, language: str = "python") -> str:
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
        
        user_prompt = (
            f"Language: {language}\n"
            f"Original Code ({original_time}):\n{buggy_code}\n\n"
            f"Our Optimized Template ({opt_time}):\n{optimized_code}"
        )
        
        explanation = self._call_llm(sys_prompt, user_prompt)
        return explanation

    def get_hint(self, code: str, bugs: List[Dict[str, Any]], attempt_number: int) -> str:
        """
        Returns a PROGRESSIVE hint based on how many attempts the student has made.
        - Attempt 1: Very short, directional hint only
        - Attempt 2: Slightly more specific hint
        - Attempt 3+: Full line-by-line diagnosis
        """
        if attempt_number == 1:
            sys_prompt = (
                "You are a strict but supportive coding tutor. The student just ran their code and it failed.\n"
                "Give them ONE short sentence hint ONLY. Do NOT explain the full error.\n"
                "Rules:\n"
                "- If there is a syntax error: say something like 'Check your syntax carefully — look at line ~X'\n"
                "- If there is a logic error: say 'Your logic seems off — re-read your return condition'\n"
                "- If there is a runtime crash: say 'Your code crashed at runtime — check the operation on line ~X'\n"
                "- If tests failed (wrong output): say 'Your output is incorrect — trace through your code with the first test case'\n"
                "DO NOT reveal the fix. One sentence only. Be encouraging."
            )
        elif attempt_number == 2:
            sys_prompt = (
                "You are a coding tutor. The student has tried twice and still fails.\n"
                "Give them a slightly more specific hint (2-3 sentences max). Still DO NOT reveal the fix.\n"
                "Rules:\n"
                "- Point to the general area of the problem (e.g., 'Your loop logic', 'The return statement', 'How you handle the edge case')\n"
                "- If syntax error: mention the type of syntax issue (e.g., 'Missing colon', 'Wrong indentation')\n"
                "- If logic error: describe the logical issue conceptually\n"
                "- If runtime crash: describe what type of error and generally why it happens\n"
                "Still do NOT give the exact fix or corrected code."
            )
        else:
            sys_prompt = (
                "You are a coding tutor. The student has used all 3 hints and still hasn't fixed the code.\n"
                "Now give a COMPLETE line-by-line diagnosis of the error.\n"
                "Rules:\n"
                "1. Reference specific line numbers in the student's code\n"
                "2. Explain exactly what is wrong and why\n"
                "3. If there is a runtime crash (like ZeroDivisionError), explain that specific line\n"
                "4. Still DO NOT write the full corrected function — give corrected snippets only\n"
                "Format with ### 🔍 Full Diagnosis and ### 💡 Correction Hints sections in Markdown."
            )

        user_prompt = f"Student Code:\n{code}\n\nDetected Issues:\n{json.dumps(bugs, indent=2)}"
        return self._call_llm(sys_prompt, user_prompt)

    def explain_test_case_failure(self, code: str, test_input: str, expected: str,
                                   actual: str, is_tle: bool = False) -> str:
        """
        Explains WHY a specific test case failed — either wrong output or time limit exceeded.
        This is SEPARATE from syntax/logic error explanation.
        """
        if is_tle:
            sys_prompt = (
                "You are a performance coaching tutor. The student's code timed out (exceeded time limit).\n"
                "Explain why their approach is too slow and give a conceptual hint for a faster approach.\n"
                "Rules:\n"
                "1. Identify the likely complexity (e.g., O(n²)) from their code\n"
                "2. Explain why that complexity causes TLE\n"
                "3. Give a 1-sentence direction hint (e.g., 'Consider using a hash map for O(1) lookups')\n"
                "Do NOT write the optimized code. Keep the response under 6 lines."
            )
            user_prompt = f"Student Code (TLE):\n{code}"
        else:
            sys_prompt = (
                "You are a debugging tutor. A test case failed — the student's code produced wrong output.\n"
                "Explain WHY the test case failed based on their code logic.\n"
                "Rules:\n"
                "1. Show the test: input, expected output, and actual wrong output\n"
                "2. Trace through their code with that specific input to explain where it goes wrong\n"
                "3. Give a hint about what logic change is needed — NOT the full fix\n"
                "Keep it concise (under 8 lines). Use Markdown."
            )
            user_prompt = (
                f"Student Code:\n{code}\n\n"
                f"Test Input: {test_input}\n"
                f"Expected Output: {expected}\n"
                f"Actual Output (wrong): {actual}"
            )
        return self._call_llm(sys_prompt, user_prompt)

    def explain_bugs(self, code: str, bugs: List[Dict[str, Any]]) -> str:
        """Legacy full-detail explanation (used when user explicitly requests it after 3 hints)."""
        sys_prompt = (
            "You are a coding tutor giving a FINAL full-detail diagnosis.\n"
            "The student requested full details after exhausting their hints.\n"
            "Give a complete line-by-line breakdown:\n"
            "1. Reference each specific line number\n"
            "2. Explain what is wrong and why (syntax, logic, runtime)\n"
            "3. Give corrected code snippets (NOT the full function)\n"
            "Format with ### 🔍 Diagnosis, ### 📍 Line-by-Line, ### 💡 Fix Hints in Markdown."
        )
        user_prompt = f"Student Code:\n{code}\n\nDetected Issues:\n{json.dumps(bugs, indent=2)}"
        return self._call_llm(sys_prompt, user_prompt)


    def generate_optimal_code(self, code: str, language: str = "python") -> Dict[str, Any]:
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
            f"Your task is to rewrite the following {language} code to be as efficient as possible. "
            "You must handle all edge cases (empty lists, single elements, etc.) correctly. "
            "Return ONLY a strictly valid JSON object with these exact keys: "
            "'approach' (Clear name of the optimization pattern used), "
            "'time_complexity' (Mathematically correct Big-O, e.g., O(n)), "
            "'space_complexity' (Mathematically correct Big-O, e.g., O(1)), "
            f"'optimized_code' (Clean, production-grade {language} code without comments unless necessary). "
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
    # Requires API_BASE_URL and API_KEY.
    llm = LLMManager()
    
    broken_code = "def two_sum(nums, t)\nfor i in range(len(n)):\n if nums[i] == t: return i\nreturn -1"
    print("Testing Repair...")
    fixed = llm.fix_code_syntax(broken_code)
    print(fixed)
    
    print("\nTesting Test Case Gen...")
    tests = llm.generate_test_cases(fixed)
    print(json.dumps(tests, indent=2))

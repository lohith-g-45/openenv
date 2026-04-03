"""
repair_engine.py
================
Member 2: Analysis & Optimization Engineer
Intelligent Code Evaluation and Optimization Environment

Heuristic code repair pipeline. Attempts to fix Syntax Errors via Regex/String
manipulation, and Logical/Edge Cases via AST manipulation.
"""

import ast
import re
from typing import Dict, Any, Tuple

from analysis import BugDetector


class RepairEngine:

    @staticmethod
    def _fix_syntax(code: str) -> str:
        """Regex-based fixes for common beginner syntax errors."""
        lines = code.splitlines()
        fixed_lines = []
        
        for line in lines:
            stripped = line.rstrip()
            if not stripped:
                fixed_lines.append(line)
                continue
            
            # Missing colons on block statements
            # e.g., "if x == 5", "def foo()", "for i in range(10)", "while True"
            block_starts = ["if ", "elif ", "else", "for ", "while ", "def ", "class "]
            is_block = any(stripped.lstrip().startswith(b) for b in block_starts)
            
            if is_block and not stripped.endswith(":"):
                # Make sure it doesn't end with \ continuation or something weird
                if not stripped.endswith("\\"):
                    stripped += ":"
            
            # Basic unbalanced parenthesis per-line (simplistic heuristic)
            # Add closing brackets if opened but never closed on the same line
            # (Note: breaks multi-line statements, but good for single-line beginners)
            open_parens = stripped.count("(") - stripped.count(")")
            open_bracks = stripped.count("[") - stripped.count("]")
            
            if open_parens > 0 and not stripped.endswith("\\"):
                stripped += ")" * open_parens
            if open_bracks > 0 and not stripped.endswith("\\"):
                stripped += "]" * open_bracks
                
            # If we appended a colon, but now added brackets, order is bad.
            # Fix order if we did both:
            if stripped.endswith(")::") or stripped.endswith("]:"):
                stripped = stripped.replace("::", ":").replace("]:", "]:").replace("):", "):")
            if (open_parens > 0 or open_bracks > 0) and is_block and stripped.endswith(":"):
                # ensure colon is at the very end
                stripped = stripped.rstrip(":") + ":"

            fixed_lines.append(line[:len(line) - len(line.lstrip())] + stripped.lstrip())

        return "\n".join(fixed_lines)

    @staticmethod
    def _fix_logic(code: str, bugs: Dict[str, Any]) -> str:
        """AST/String-based fixes for logical/edge cases found by BugDetector."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return code # Still syntax errors, can't fix logic

        lines = code.splitlines()
        
        # We process bugs in reverse line order so line numbers don't shift as we insert
        edge_bugs = sorted(bugs.get("edge_case_risks", []), key=lambda x: x.get("line") or 0, reverse=True)
        
        for bug in edge_bugs:
            # Fix missing list guards: e.g. "Function 'solution' takes list arg ['nums'] but has no empty-list guard"
            if "no empty-list guard" in bug.get("message", ""):
                lineno = bug["line"]
                # lineno is the 'def' line. 
                # Find indentation of the def body (look at next non-empty line)
                indent = "    "
                for i in range(lineno, len(lines)):
                    if lines[i].strip():
                        stripped_len = len(lines[i].lstrip())
                        indent = " " * (len(lines[i]) - stripped_len)
                        break
                
                # Extract the arg name from the message
                match = re.search(r"\['(.*?)'\]", bug["message"])
                arg_name = match.group(1) if match else "nums"
                
                guard_code = f"{indent}if not {arg_name}:\n{indent}    return 0  # Auto-injected empty guard"
                lines.insert(lineno, guard_code)

        return "\n".join(lines)


    @classmethod
    def attempt_repair(cls, code: str) -> Tuple[str, bool, str]:
        """
        Attempts to fix syntax and logic.
        Returns: (fixed_code, is_syntax_fixed, repair_report)
        """
        original_bugs = BugDetector.analyze(code)
        syntax_broken_initially = any(i["type"] in ("SyntaxError", "ParseError") for i in original_bugs.get("syntax_errors", []))
        
        current_code = code
        report = []

        if syntax_broken_initially:
            current_code = cls._fix_syntax(current_code)
            verify_bugs = BugDetector.analyze(current_code)
            syntax_broken_after = any(i["type"] in ("SyntaxError", "ParseError") for i in verify_bugs.get("syntax_errors", []))
            
            if not syntax_broken_after:
                report.append("✅ Auto-fixed syntax errors (e.g. missing colons or parentheses).")
            else:
                report.append("❌ Could not fully repair syntax. Code is structurally broken.")
                # We return here, because if syntax is broken, logic fixing won't work
                return current_code, False, "\n".join(report)

        # Re-analyze for logic bugs with working syntax
        current_bugs = BugDetector.analyze(current_code)
        if current_bugs.get("edge_case_risks"):
            current_code = cls._fix_logic(current_code, current_bugs)
            report.append("✅ Auto-injected edge case guards (e.g. empty list checks).")

        if not report:
            report.append("ℹ️ No auto-repairs needed. Code structure is valid.")

        return current_code, True, "\n".join(report)

if __name__ == "__main__":
    broken = """
def two_sum(nums, target)
    for i in range(len(nums))
        if nums[i] == target
            return [i]
    return []
"""
    print("ORIGINAL:")
    print(broken)
    
    fixed, success, rep = RepairEngine.attempt_repair(broken)
    print("\nREPORT:")
    print(rep)
    print("\nFIXED:")
    print(fixed)

"""
optimization_engine.py  [v3.0 — Multi-Candidate Ranking]
=========================================================
Member 2: Analysis & Optimization Engineer
Intelligent Code Evaluation and Optimization Environment

KEY REDESIGN (v3.0):
  OLD: "First matching rule wins"  -> single suggestion, often incomplete
  NEW: "Evaluate ALL rules, rank by achievement, return best + all alternatives"

  For any given code, the engine now:
    1. Runs ALL rules and checks applicability
    2. Each rule scores itself (confidence 0-1) and declares its result complexity
    3. All applicable rules are ranked: better complexity = higher rank
    4. Returns:
         - best_suggestion   : the single best optimization (most improvement)
         - all_alternatives  : every other valid option, ranked
         - not_applicable    : rules that were considered but don't fit + why

Rules (result complexity, best to worst):
  LinearSearchToBinarySearch     O(log n)
  HashmapLookup                  O(n)
  SlidingWindow                  O(n)
  TwoPointers                    O(n) / O(n log n) after sort
  PrefixSum                      O(n + q)
  MonotonicStack                 O(n)
  MemoizationViaLRUCache         O(n)
  BottomUpDP                     O(n)

Deterministic: same code => same ranking, no randomness, no external APIs.
"""

import ast
import textwrap
import math
from typing import Any, Dict, List, Optional, Tuple

from analysis import ApproachClassifier, ComplexityAnalyzer, analyze_code


# ===========================================================================
# COMPLEXITY RANKING — lower rank = better complexity
# ===========================================================================

COMPLEXITY_RANK: Dict[str, int] = {
    "O(1)":           0,
    "O(log n)":       1,
    "O(n)":           2,
    "O(n log n)":     3,
    "O(n^2)":         4,
    "O(n^2 log n)":   5,
    "O(n^3)":         6,
    "O(2^n)":         7,
    "O(2^n) or worse": 8,
    "Unknown":        9,
}

def _complexity_rank(c: str) -> int:
    # Handle O(n^k) for arbitrary k
    if c in COMPLEXITY_RANK:
        return COMPLEXITY_RANK[c]
    if c.startswith("O(n^"):
        try:
            exp = float(c[4:-1])
            return int(30 + exp)   # n^3=33, n^4=34 ... all worse than O(2^n)
        except ValueError:
            pass
    return 9


# ===========================================================================
# BASE RULE
# ===========================================================================

class OptimizationRule:
    """
    Base class. Each rule must declare:
      - name              : str
      - description       : str
      - result_complexity : str  — what this rule achieves in the BEST case

    And implement:
      - evaluate(code, analysis) -> EvaluationResult
    """

    name:               str = ""
    description:        str = ""
    result_complexity:  str = "O(n)"   # best-case result of applying this rule

    def evaluate(self, code: str, analysis: Dict) -> "EvaluationResult":
        raise NotImplementedError

    @staticmethod
    def _get_func_info(code: str) -> Tuple[str, str]:
        """Return (func_name, param_str) from first function definition."""
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    return node.name, ", ".join(a.arg for a in node.args.args)
        except SyntaxError:
            pass
        return "solution", "nums, target"

    @staticmethod
    def _has_syntax_error(code: str) -> bool:
        try:
            ast.parse(code)
            return False
        except SyntaxError:
            return True


class EvaluationResult:
    """
    Returned by every rule's evaluate() method.

    applicable      : bool   — does this rule apply to the code?
    confidence      : float  — 0.0 to 1.0 how certain we are it applies
    result_complexity: str   — complexity achieved after optimization
    improvement_gain : int   — current_rank - result_rank (>0 means improvement)
    reason          : str    — why applicable or why not
    suggestion      : dict   — {"approach","explanation","optimized_code"} or None
    rule_name       : str
    rule_description: str
    """

    def __init__(
        self,
        rule: OptimizationRule,
        applicable: bool,
        confidence: float = 0.0,
        reason: str = "",
        suggestion: Optional[Dict] = None,
        current_complexity: str = "Unknown",
    ):
        self.rule_name         = rule.name
        self.rule_description  = rule.description
        self.applicable        = applicable
        self.confidence        = round(confidence, 3)
        self.reason            = reason
        self.result_complexity = rule.result_complexity
        self.suggestion        = suggestion

        current_rank = _complexity_rank(current_complexity)
        result_rank  = _complexity_rank(self.result_complexity)
        self.improvement_gain  = max(0, current_rank - result_rank)

    def to_dict(self) -> Dict:
        return {
            "rule":              self.rule_name,
            "description":       self.rule_description,
            "applicable":        self.applicable,
            "confidence":        self.confidence,
            "result_complexity": self.result_complexity,
            "improvement_gain":  self.improvement_gain,
            "reason":            self.reason,
            "approach":          self.suggestion["approach"]      if self.suggestion else None,
            "explanation":       self.suggestion["explanation"]   if self.suggestion else None,
            "optimized_code":    self.suggestion["optimized_code"] if self.suggestion else None,
        }


# ===========================================================================
# RULE 1 — Binary Search  (O(n) or O(n²) → O(log n))
# ===========================================================================

class BinarySearchRule(OptimizationRule):
    name               = "linear_to_binary_search"
    description        = "Replace O(n) linear scan on sorted data with O(log n) binary search"
    result_complexity  = "O(log n)"

    _SORTED_SIGNALS = ["sorted", ".sort(", "ascending", "nondecreasing", "non-decreasing",
                       "sorted input", "sorted array", "sorted list"]
    _SEARCH_SIGNALS = ["search", "find", "target", "locate", "lookup", "indexOf",
                       "contains", "exist", "present"]

    def evaluate(self, code: str, analysis: Dict) -> EvaluationResult:
        code_lower     = code.lower()
        approach       = analysis["approach"]["primary"]
        current_time   = analysis["complexity"]["time_complexity"]
        current_rank   = _complexity_rank(current_time)
        result_rank    = _complexity_rank(self.result_complexity)

        # Only useful if we're currently slower than O(log n)
        if current_rank <= result_rank:
            return EvaluationResult(self, False, 0.0,
                "Already O(log n) or better — binary search won't help", None, current_time)

        has_sorted = any(s in code_lower for s in self._SORTED_SIGNALS)
        has_search = any(s in code_lower for s in self._SEARCH_SIGNALS)

        # Check if code already uses binary search
        already_bs = approach == "binary_search"
        if already_bs:
            return EvaluationResult(self, False, 0.0,
                "Code already uses binary search", None, current_time)

        if has_sorted and has_search:
            confidence = 0.90
            reason     = "Sorted input + search operation detected — binary search directly applicable"
        elif has_sorted:
            confidence = 0.60
            reason     = "Sorted input detected — binary search may apply if target lookup is needed"
        elif has_search:
            confidence = 0.35
            reason     = "Search operation found — if input can be sorted, binary search applies"
        else:
            return EvaluationResult(self, False, 0.0,
                "No search pattern or sorted input detected", None, current_time)

        func_name, params = self._get_func_info(code)
        optimized = textwrap.dedent(f"""\
            import bisect

            def {func_name}({params}):
                \"\"\"
                Optimized: O(log n) time | O(1) space
                Strategy : Binary search — halve the search space each step.
                           Requires sorted input.
                \"\"\"
                # Ensure sorted (O(n log n) one-time cost)
                nums_sorted = sorted(nums)   # remove if already sorted

                lo, hi = 0, len(nums_sorted) - 1
                while lo <= hi:
                    mid = (lo + hi) // 2
                    if nums_sorted[mid] == target:
                        return mid
                    elif nums_sorted[mid] < target:
                        lo = mid + 1    # target is in right half
                    else:
                        hi = mid - 1    # target is in left half

                return -1   # not found

            # One-liner alternative using Python's bisect:
            # idx = bisect.bisect_left(nums_sorted, target)
            # return idx if idx < len(nums_sorted) and nums_sorted[idx] == target else -1
        """)

        return EvaluationResult(self, True, confidence, reason, {
            "approach":       "Binary Search — O(log n) time, O(1) space",
            "explanation":    (
                f"Your current approach ({approach.replace('_',' ')}) runs in {current_time}. "
                "On sorted input, binary search repeatedly halves the search space. "
                "Each step eliminates half the candidates: at most log2(n) comparisons. "
                "O(log n) is asymptotically optimal for search on sorted data."
            ),
            "optimized_code": optimized,
        }, current_time)


# ===========================================================================
# RULE 2 — Hashmap Lookup  (O(n²) → O(n))
# ===========================================================================

class HashmapRule(OptimizationRule):
    name               = "brute_force_to_hashmap"
    description        = "Replace O(n²) pair/complement search with O(n) hashmap lookup"
    result_complexity  = "O(n)"

    _SIGNALS = ["target", "sum", "pair", "complement", "difference", "equal",
                "two sum", "find pair", "k sum", "k-sum"]

    def evaluate(self, code: str, analysis: Dict) -> EvaluationResult:
        code_lower   = code.lower()
        approach     = analysis["approach"]["primary"]
        current_time = analysis["complexity"]["time_complexity"]
        current_rank = _complexity_rank(current_time)
        result_rank  = _complexity_rank(self.result_complexity)

        if current_rank <= result_rank:
            return EvaluationResult(self, False, 0.0,
                "Already O(n) or better — hashmap won't improve time complexity", None, current_time)

        if approach == "hashmap":
            return EvaluationResult(self, False, 0.0,
                "Code already uses a hashmap approach", None, current_time)

        has_signal = any(s in code_lower for s in self._SIGNALS)
        has_nested = current_time in ("O(n^2)", "O(n^2 log n)")

        try:
            tree   = ast.parse(code)
            depth  = ComplexityAnalyzer._max_loop_depth(tree)
        except SyntaxError:
            depth  = 0

        if has_nested and has_signal:
            confidence = 0.92
            reason     = f"O(n^2) nested loops + pair/sum signal — hashmap directly applicable"
        elif has_nested:
            confidence = 0.55
            reason     = f"O(n^2) nested loops detected — hashmap may reduce if problem involves lookup"
        elif has_signal and depth >= 1:
            confidence = 0.70
            reason     = "Pair/complement signal in a loop — hashmap likely applicable"
        else:
            return EvaluationResult(self, False, 0.0,
                "No pair/lookup pattern or nested loops detected", None, current_time)

        func_name, params = self._get_func_info(code)
        optimized = textwrap.dedent(f"""\
            def {func_name}({params}):
                \"\"\"
                Optimized: O(n) time | O(n) space
                Strategy : Hashmap — store each element's index/value as we scan.
                           For each new element, check if complement exists in O(1).
                           Eliminates the inner loop entirely.
                \"\"\"
                seen = {{}}     # value -> index
                for i, num in enumerate(nums):
                    complement = target - num
                    if complement in seen:
                        return [seen[complement], i]
                    seen[num] = i
                return []
        """)

        return EvaluationResult(self, True, confidence, reason, {
            "approach":       "Hashmap — O(n) time, O(n) space",
            "explanation":    (
                f"Your current approach ({approach.replace('_',' ')}) runs in {current_time}. "
                "With a hashmap, you prestore each element. For every new element, "
                "check if its complement exists in O(1) — no inner loop needed. "
                "Trade-off: O(n) extra space for the hash table."
            ),
            "optimized_code": optimized,
        }, current_time)


# ===========================================================================
# RULE 3 — Two Pointers  (O(n²) → O(n) or O(n log n) with sort)
# ===========================================================================

class TwoPointersRule(OptimizationRule):
    name               = "to_two_pointers"
    description        = "Use two-pointer convergence on sorted data to eliminate nested loops"
    result_complexity  = "O(n log n)"   # worst case includes sorting

    _PAIR_SIGNALS  = ["target", "sum", "pair", "two sum", "k sum", "difference"]
    _SORT_SIGNALS  = ["sorted", ".sort(", "ascending", "sorted input", "nondecreasing"]

    def evaluate(self, code: str, analysis: Dict) -> EvaluationResult:
        code_lower   = code.lower()
        approach     = analysis["approach"]["primary"]
        current_time = analysis["complexity"]["time_complexity"]
        current_rank = _complexity_rank(current_time)
        result_rank  = _complexity_rank(self.result_complexity)

        if current_rank <= result_rank:
            return EvaluationResult(self, False, 0.0,
                "Already O(n log n) or better", None, current_time)

        if approach == "two_pointers":
            return EvaluationResult(self, False, 0.0,
                "Code already uses two pointers", None, current_time)

        has_pair    = any(s in code_lower for s in self._PAIR_SIGNALS)
        has_sorted  = any(s in code_lower for s in self._SORT_SIGNALS)
        has_nested  = current_time in ("O(n^2)", "O(n^2 log n)")

        if has_nested and (has_sorted or has_pair):
            if has_sorted and has_pair:
                confidence = 0.88
                reason     = "Sorted array + pair/sum problem — two pointers directly applicable"
            elif has_sorted:
                confidence = 0.70
                reason     = "Sorted input detected — two pointers applicable for many pair problems"
            else:
                confidence = 0.60
                reason     = "O(n^2) pair problem — two pointers applicable if we sort first"
        elif has_nested:
            confidence = 0.40
            reason     = "O(n^2) nested loops — two pointers may apply for array pair problems"
        else:
            return EvaluationResult(self, False, 0.0,
                "No pair/sorted signal or nested O(n^2) loops", None, current_time)

        func_name, params = self._get_func_info(code)
        optimized = textwrap.dedent(f"""\
            def {func_name}({params}):
                \"\"\"
                Optimized: O(n log n) time | O(1) space
                Strategy : Two pointers — sort once, then converge from both ends.
                           Sum too small? advance left. Too large? retreat right.
                           No extra space (except sort stack). Each element visited once.
                \"\"\"
                nums.sort()                      # O(n log n) — required once
                left, right = 0, len(nums) - 1

                while left < right:
                    current = nums[left] + nums[right]
                    if current == target:
                        return [left, right]
                    elif current < target:
                        left  += 1               # need a larger value
                    else:
                        right -= 1               # need a smaller value

                return []
        """)

        return EvaluationResult(self, True, confidence, reason, {
            "approach":       "Two Pointers — O(n log n) time, O(1) space",
            "explanation":    (
                f"Your current approach runs in {current_time}. "
                "Two pointers on a sorted array: place left=0, right=n-1. "
                "If sum < target: advance left (need larger). "
                "If sum > target: retreat right (need smaller). "
                "Each element visited at most once after sorting: O(n). "
                "Total O(n log n) due to sort. Space: O(1) — no extra structure. "
                "Note: Hashmap is O(n) time but needs O(n) space. "
                "Two pointers is O(n log n) time but only O(1) space."
            ),
            "optimized_code": optimized,
        }, current_time)


# ===========================================================================
# RULE 4 — Sliding Window  (O(n²) → O(n))
# ===========================================================================

class SlidingWindowRule(OptimizationRule):
    name               = "to_sliding_window"
    description        = "Replace O(n²) subarray scanning with O(n) sliding window"
    result_complexity  = "O(n)"

    _SIGNALS = [
        "subarray", "substring", "window", "contiguous", "consecutive",
        "max length", "min length", "max_len", "min_len", "max sum", "min sum",
        "longest", "shortest", "at most", "at least", "exactly k",
    ]

    def evaluate(self, code: str, analysis: Dict) -> EvaluationResult:
        code_lower   = code.lower()
        approach     = analysis["approach"]["primary"]
        current_time = analysis["complexity"]["time_complexity"]
        current_rank = _complexity_rank(current_time)
        result_rank  = _complexity_rank(self.result_complexity)

        if current_rank <= result_rank:
            return EvaluationResult(self, False, 0.0,
                "Already O(n) or better", None, current_time)

        if approach == "sliding_window":
            return EvaluationResult(self, False, 0.0,
                "Code already uses sliding window", None, current_time)

        has_signal = any(s in code_lower for s in self._SIGNALS)
        has_nested = current_time in ("O(n^2)", "O(n^2 log n)")

        if has_nested and has_signal:
            confidence = 0.88
            reason     = "O(n^2) loops + contiguous subarray/window signal — sliding window directly applicable"
        elif has_signal:
            confidence = 0.50
            reason     = "Contiguous subarray/window pattern detected — sliding window may apply"
        elif has_nested:
            confidence = 0.25
            reason     = "O(n^2) nested loops — if problem involves contiguous ranges, sliding window may help"
        else:
            return EvaluationResult(self, False, 0.0,
                "No subarray/window pattern and no O(n^2) structure", None, current_time)

        func_name, params = self._get_func_info(code)
        optimized = textwrap.dedent(f"""\
            def {func_name}({params}):
                \"\"\"
                Optimized: O(n) time | O(1) space
                Strategy : Sliding window — maintain [win_start, win_end] bounds.
                           Expand right each iteration; shrink left when constraint violated.
                           Each element enters and leaves the window at most once.
                \"\"\"
                if not nums:
                    return 0

                win_start  = 0
                max_len    = 0
                window_sum = 0

                for win_end in range(len(nums)):
                    window_sum += nums[win_end]            # expand window right

                    # Shrink from left while constraint is violated
                    while window_sum > target and win_start <= win_end:
                        window_sum -= nums[win_start]
                        win_start  += 1

                    max_len = max(max_len, win_end - win_start + 1)

                return max_len
        """)

        return EvaluationResult(self, True, confidence, reason, {
            "approach":       "Sliding Window — O(n) time, O(1) space",
            "explanation":    (
                f"Your current approach runs in {current_time}. "
                "Brute force scans all O(n^2) subarrays. A sliding window maintains "
                "a live window [win_start, win_end]: expand right on each step, "
                "shrink left when the constraint breaks. Each element added/removed "
                "at most once = O(n) total. Space: O(1) — just two indices and a running sum."
            ),
            "optimized_code": optimized,
        }, current_time)


# ===========================================================================
# RULE 5 — Prefix Sum  (O(n²) range queries → O(n + q))
# ===========================================================================

class PrefixSumRule(OptimizationRule):
    name               = "to_prefix_sum"
    description        = "Precompute prefix sums to answer O(n²) range queries in O(1) each"
    result_complexity  = "O(n)"

    _SIGNALS = [
        "range sum", "sum of range", "subarray sum", "query", "queries",
        "sum between", "prefix", "cumulative", "running sum", "sum from",
    ]

    def evaluate(self, code: str, analysis: Dict) -> EvaluationResult:
        code_lower   = code.lower()
        approach     = analysis["approach"]["primary"]
        current_time = analysis["complexity"]["time_complexity"]
        current_rank = _complexity_rank(current_time)
        result_rank  = _complexity_rank(self.result_complexity)

        if current_rank <= result_rank:
            return EvaluationResult(self, False, 0.0,
                "Already O(n) or better", None, current_time)

        if approach == "prefix_sum":
            return EvaluationResult(self, False, 0.0,
                "Code already uses prefix sum", None, current_time)

        has_range  = any(s in code_lower for s in self._SIGNALS)
        has_nested = current_time in ("O(n^2)", "O(n^2 log n)")

        if has_nested and has_range:
            confidence = 0.87
            reason     = "O(n^2) + range/query sum pattern — prefix sum will reduce to O(n+q)"
        elif has_range:
            confidence = 0.65
            reason     = "Range/query sum pattern detected — prefix sum applicable"
        elif has_nested:
            confidence = 0.20
            reason     = "O(n^2) loops — if involves range queries, prefix sum may help"
        else:
            return EvaluationResult(self, False, 0.0,
                "No range sum pattern and no O(n^2) structure", None, current_time)

        func_name, params = self._get_func_info(code)
        optimized = textwrap.dedent(f"""\
            def {func_name}(nums, queries):
                \"\"\"
                Optimized: O(n + q) time | O(n) space  (q = number of queries)
                Strategy : Prefix sum — precompute cumulative sums in O(n).
                           Each range [l, r] sum answered in O(1): prefix[r+1] - prefix[l].
                \"\"\"
                if not nums:
                    return []

                # Build prefix array in O(n)
                prefix = [0] * (len(nums) + 1)
                for i, val in enumerate(nums):
                    prefix[i + 1] = prefix[i] + val

                # Answer each (l, r) query in O(1)
                return [prefix[r + 1] - prefix[l] for l, r in queries]
        """)

        return EvaluationResult(self, True, confidence, reason, {
            "approach":       "Prefix Sum — O(n+q) time, O(n) space",
            "explanation":    (
                f"Your current approach computes sums with nested loops: {current_time}. "
                "A prefix sum array stores cumulative sums: prefix[i] = sum(nums[0..i-1]). "
                "Built in O(n) once, then any range [l, r] = prefix[r+1]-prefix[l] in O(1). "
                "For q queries: O(n+q) total — dramatically faster than O(n*q)."
            ),
            "optimized_code": optimized,
        }, current_time)


# ===========================================================================
# RULE 6 — Monotonic Stack  (O(n²) → O(n))
# ===========================================================================

class MonotonicStackRule(OptimizationRule):
    name               = "to_monotonic_stack"
    description        = "Replace O(n²) brute-force next-greater scans with O(n) monotonic stack"
    result_complexity  = "O(n)"

    _SIGNALS = [
        "next greater", "next smaller", "next larger", "previous greater",
        "next bigger", "stock span", "largest rectangle", "histogram",
        "nearest greater", "nearest smaller", "monotonic",
    ]

    def evaluate(self, code: str, analysis: Dict) -> EvaluationResult:
        code_lower   = code.lower()
        approach     = analysis["approach"]["primary"]
        current_time = analysis["complexity"]["time_complexity"]
        current_rank = _complexity_rank(current_time)
        result_rank  = _complexity_rank(self.result_complexity)

        if current_rank <= result_rank:
            return EvaluationResult(self, False, 0.0,
                "Already O(n) or better", None, current_time)

        if approach == "monotonic_stack":
            return EvaluationResult(self, False, 0.0,
                "Code already uses monotonic stack", None, current_time)

        has_signal = any(s in code_lower for s in self._SIGNALS)
        has_nested = current_time in ("O(n^2)", "O(n^2 log n)")

        if has_nested and has_signal:
            confidence = 0.93
            reason     = "O(n^2) + next-greater/smaller pattern — monotonic stack is the canonical O(n) solution"
        elif has_signal:
            confidence = 0.75
            reason     = "Next-greater/smaller pattern found — monotonic stack applicable"
        elif has_nested:
            confidence = 0.15
            reason     = "O(n^2) loops — if pattern involves next-greater queries, monotonic stack may help"
        else:
            return EvaluationResult(self, False, 0.0,
                "No next-greater/smaller pattern detected", None, current_time)

        func_name, params = self._get_func_info(code)
        optimized = textwrap.dedent(f"""\
            def {func_name}(nums):
                \"\"\"
                Optimized: O(n) time | O(n) space
                Strategy : Monotonic stack — maintain a stack of 'unsettled' indices.
                           When a new element is greater than the stack top,
                           it IS the next-greater answer for those indices. Pop them.
                           Each element pushed and popped at most once = O(n).
                \"\"\"
                n      = len(nums)
                result = [-1] * n      # default: no greater element
                stack  = []            # stack of indices (not values)

                for i in range(n):
                    # Resolve all stack entries where nums[i] is the answer
                    while stack and nums[stack[-1]] < nums[i]:
                        idx         = stack.pop()
                        result[idx] = nums[i]
                    stack.append(i)

                # Items left in stack have no greater element — result stays -1
                return result
        """)

        return EvaluationResult(self, True, confidence, reason, {
            "approach":       "Monotonic Stack — O(n) time, O(n) space",
            "explanation":    (
                f"Your current approach runs in {current_time} by checking every pair. "
                "A monotonic stack processes each element once. "
                "Unresolved indices wait in the stack. "
                "When we find a larger element, we 'resolve' all smaller stack entries in one pass. "
                "Each element pushed and popped at most once: O(n) total."
            ),
            "optimized_code": optimized,
        }, current_time)


# ===========================================================================
# RULE 7 — Memoization via @lru_cache  (O(2^n) → O(n))
# ===========================================================================

class MemoizationRule(OptimizationRule):
    name               = "recursion_to_memoization"
    description        = "Add @lru_cache to eliminate exponential recomputation in recursion"
    result_complexity  = "O(n)"

    def evaluate(self, code: str, analysis: Dict) -> EvaluationResult:
        approach     = analysis["approach"]["primary"]
        current_time = analysis["complexity"]["time_complexity"]
        current_rank = _complexity_rank(current_time)
        result_rank  = _complexity_rank(self.result_complexity)

        if current_rank <= result_rank:
            return EvaluationResult(self, False, 0.0,
                "Already efficient enough — memoization won't help", None, current_time)

        has_memo = ComplexityAnalyzer._has_memoization(code)
        if has_memo:
            return EvaluationResult(self, False, 0.0,
                "Code already uses memoization/caching", None, current_time)

        is_recursive = approach in ("recursion", "divide_and_conquer",
                                     "backtracking", "graph_dfs")
        exp_time     = "2^n" in current_time or "^n" in current_time

        if is_recursive and exp_time:
            confidence = 0.95
            reason     = f"Bare recursion with {current_time} — memoization directly applicable"
        elif is_recursive:
            confidence = 0.55
            reason     = "Recursive code detected — if it has overlapping subproblems, memoization will help"
        else:
            return EvaluationResult(self, False, 0.0,
                "No recursive pattern detected", None, current_time)

        # Auto-insert @lru_cache
        try:
            tree  = ast.parse(code)
            lines = code.splitlines()
            func_names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
            recursive_funcs = {
                n.func.id for n in ast.walk(tree)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id in func_names
            }
            insert_before = {
                node.lineno: " " * (node.col_offset or 0)
                for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef) and node.name in recursive_funcs
            }
            new_lines = ["import functools", ""]
            for i, line in enumerate(lines, start=1):
                if i in insert_before:
                    new_lines.append(f"{insert_before[i]}@functools.lru_cache(maxsize=None)")
                new_lines.append(line)
            optimized = "\n".join(new_lines)
        except Exception:
            optimized = f"import functools\n\n# Add @functools.lru_cache(maxsize=None) above your recursive function\n\n{code}"

        return EvaluationResult(self, True, confidence, reason, {
            "approach":       "Memoized Recursion — O(n) time, O(n) space",
            "explanation":    (
                f"Your recursive solution has {current_time} because it recomputes "
                "the same sub-problem arguments repeatedly. "
                "@functools.lru_cache caches every unique input. "
                "Each unique argument set solved exactly once: time drops to O(n). "
                "Zero restructuring of your logic required — just add the decorator."
            ),
            "optimized_code": optimized,
        }, current_time)


# ===========================================================================
# RULE 8 — Bottom-Up DP  (O(2^n) → O(n), iterative)
# ===========================================================================

class BottomUpDPRule(OptimizationRule):
    name               = "recursion_to_bottom_up_dp"
    description        = "Convert exponential recursion to O(n) iterative bottom-up DP"
    result_complexity  = "O(n)"

    _DP_SIGNALS = [
        "fib", "fibonacci", "climb", "stair", "coin", "change",
        "knapsack", "longest", "lcs", "edit distance", "rob",
        "house", "jump", "decode", "ways", "paths", "minimum cost",
    ]

    def evaluate(self, code: str, analysis: Dict) -> EvaluationResult:
        code_lower   = code.lower()
        approach     = analysis["approach"]["primary"]
        current_time = analysis["complexity"]["time_complexity"]
        current_rank = _complexity_rank(current_time)
        result_rank  = _complexity_rank(self.result_complexity)

        if current_rank <= result_rank:
            return EvaluationResult(self, False, 0.0,
                "Already O(n) — bottom-up DP won't improve", None, current_time)

        has_memo    = ComplexityAnalyzer._has_memoization(code)
        dp_approach = analysis["approach"]["primary"] == "dynamic_programming"
        if has_memo or dp_approach:
            return EvaluationResult(self, False, 0.0,
                "Code already uses memoization or bottom-up DP", None, current_time)

        is_recursive = approach in ("recursion", "divide_and_conquer")
        exp_time     = "2^n" in current_time or "^n" in current_time
        has_dp_kw    = any(kw in code_lower for kw in self._DP_SIGNALS)

        if is_recursive and exp_time and has_dp_kw:
            confidence = 0.85
            reason     = f"Bare recursion ({current_time}) + DP-solvable problem keyword found"
        elif is_recursive and exp_time:
            confidence = 0.60
            reason     = f"Bare recursion with {current_time} — if overlapping subproblems exist, bottom-up DP applies"
        elif is_recursive and has_dp_kw:
            confidence = 0.50
            reason     = "Recursive + DP-keyword — bottom-up DP may apply"
        else:
            return EvaluationResult(self, False, 0.0,
                "No recursive + DP-solvable pattern found", None, current_time)

        func_name, params = self._get_func_info(code)

        is_fib_like = any(kw in code_lower for kw in
                          ["fib", "climb", "stair", "rob", "house", "jump", "ways"])

        if is_fib_like:
            optimized = textwrap.dedent(f"""\
                def {func_name}({params}):
                    \"\"\"
                    Optimized: O(n) time | O(1) space
                    Strategy : Bottom-up DP with rolling variables.
                               Compute answers iteratively; keep only prev2, prev1.
                    \"\"\"
                    if n <= 0: return 0
                    if n == 1: return 1

                    prev2, prev1 = 0, 1     # dp[0], dp[1]

                    for _ in range(2, n + 1):
                        curr  = prev1 + prev2
                        prev2 = prev1
                        prev1 = curr

                    return prev1
            """)
            space_note = "O(1) space — rolling 2 variables"
        else:
            optimized = textwrap.dedent(f"""\
                def {func_name}({params}):
                    \"\"\"
                    Optimized: O(n) time | O(n) space
                    Strategy : Bottom-up DP table — fill from base cases upward.
                               No recursion stack; no redundant recomputation.
                    \"\"\"
                    dp    = [0] * (n + 1)
                    dp[0] = 0    # base case — adjust
                    dp[1] = 1    # base case — adjust

                    for i in range(2, n + 1):
                        dp[i] = dp[i - 1] + dp[i - 2]    # recurrence — adjust

                    return dp[n]
            """)
            space_note = "O(n) space for DP table"

        return EvaluationResult(self, True, confidence, reason, {
            "approach":       f"Bottom-Up DP — O(n) time, {space_note}",
            "explanation":    (
                f"Your recursive solution has {current_time} due to repeated sub-problem computation. "
                "Bottom-up DP fills a table from base cases upward — each state computed once. "
                "For 2-state recurrences (like Fibonacci), rolling variables reduce space to O(1). "
                "This eliminates both the recursion stack and redundant calls."
            ),
            "optimized_code": optimized,
        }, current_time)


# ===========================================================================
# COMBINE + RANK ALL CANDIDATES
# ===========================================================================

_ALL_RULES: List[OptimizationRule] = [
    BinarySearchRule(),
    HashmapRule(),
    SlidingWindowRule(),
    TwoPointersRule(),
    PrefixSumRule(),
    MonotonicStackRule(),
    MemoizationRule(),
    BottomUpDPRule(),
]


def optimize_code(code: str, pre_analysis: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Multi-candidate optimization engine.

    Evaluates ALL rules against the code simultaneously.
    Ranks all applicable suggestions by:
      1. improvement_gain (higher = more complexity reduction)
      2. confidence       (higher = more certain it applies)

    Parameters
    ----------
    code         : str  — raw solution source
    pre_analysis : dict — optional pre-computed analyze_code() result

    Returns
    -------
    {
        "original_approach":   str,
        "original_complexity": {"time": str, "space": str},
        "total_candidates":    int,   # number of applicable optimizations found
        "best": {
            "approach":          str,
            "result_complexity": str,
            "improvement_gain":  int,
            "confidence":        float,
            "explanation":       str,
            "optimized_code":    str,
            "rule":              str,
        },
        "alternatives": [         # other valid options, ranked
            {same structure as best}
        ],
        "not_applicable": [       # rules that were checked but didn't fit
            {"rule": str, "reason": str}
        ],
        "analysis":  dict,
    }
    """
    analysis = pre_analysis if pre_analysis is not None else analyze_code(code)

    orig_approach = analysis["approach"]["primary"].replace("_", " ").title()
    orig_time     = analysis["complexity"]["time_complexity"]
    orig_space    = analysis["complexity"]["space_complexity"]

    applicable     = []
    not_applicable = []

    for rule in _ALL_RULES:
        ev = rule.evaluate(code, analysis)
        if ev.applicable and ev.improvement_gain > 0:
            applicable.append(ev)
        else:
            not_applicable.append({
                "rule":   ev.rule_name,
                "reason": ev.reason,
            })

    # Sort by weighted score: improvement_gain × confidence
    # This ensures a highly-confident medium improvement (e.g. Hashmap 92%)
    # beats a low-confidence high improvement (e.g. Binary Search 35%).
    # Tie-break: higher confidence wins.
    applicable.sort(key=lambda e: (-(e.improvement_gain * e.confidence), -e.confidence))

    def _ev_to_dict(ev: EvaluationResult) -> Dict:
        return {
            "rule":              ev.rule_name,
            "approach":          ev.suggestion["approach"],
            "result_complexity": ev.result_complexity,
            "improvement_gain":  ev.improvement_gain,
            "confidence":        ev.confidence,
            "explanation":       ev.suggestion["explanation"],
            "optimized_code":    ev.suggestion["optimized_code"],
            "reason":            ev.reason,
        }

    if applicable:
        best         = _ev_to_dict(applicable[0])
        alternatives = [_ev_to_dict(ev) for ev in applicable[1:]]
        improvement  = (
            f"Best upgrade: '{orig_approach}' ({orig_time}) "
            f"-> '{best['approach']}' ({best['result_complexity']})"
        )
    else:
        best         = None
        alternatives = []
        improvement  = f"No optimization found — {orig_time} appears already efficient"

    return {
        "original_approach":   orig_approach,
        "original_complexity": {"time": orig_time, "space": orig_space},
        "total_candidates":    len(applicable),
        "best":                best,
        "alternatives":        alternatives,
        "not_applicable":      not_applicable,
        "improvement":         improvement,
        "analysis":            analysis,
    }


# ===========================================================================
# RL ENVIRONMENT INTEGRATION
# ===========================================================================

def optimization_action(action: Dict[str, Any]) -> Dict[str, Any]:
    """
    Unified RL entry point.
    Action keys: "code", "analysis" (optional pre-computed)
    """
    return optimize_code(
        code=action.get("code", ""),
        pre_analysis=action.get("analysis", None),
    )


# ===========================================================================
# SELF-TEST
# ===========================================================================

if __name__ == "__main__":
    print("=" * 72)
    print("  OPTIMIZATION ENGINE v3.0 — MULTI-CANDIDATE SELF-TEST")
    print("=" * 72)

    test_cases = [
        {
            "label": "Brute Force Two-Sum",
            "code": """
def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
""",
        },
        {
            "label": "Brute Force Max Subarray",
            "code": """
def max_subarray_sum(nums, target):
    # Find longest contiguous subarray with sum <= target
    max_len = 0
    for i in range(len(nums)):
        for j in range(i, len(nums)):
            if sum(nums[i:j+1]) <= target:
                max_len = max(max_len, j - i + 1)
    return max_len
""",
        },
        {
            "label": "Bare Fibonacci Recursion",
            "code": """
def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)
""",
        },
        {
            "label": "Linear Search on Sorted Array",
            "code": """
def find_target(nums, target):
    nums = sorted(nums)
    for i, n in enumerate(nums):
        if n == target:
            return i
    return -1
""",
        },
        {
            "label": "Next Greater Element — Nested Loop",
            "code": """
def next_greater(nums):
    result = [-1] * len(nums)
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            if nums[j] > nums[i]:
                result[i] = nums[j]
                break
    return result
""",
        },
        {
            "label": "Already Optimal (Hashmap Two-Sum)",
            "code": """
def two_sum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return [seen[target - n], i]
        seen[n] = i
    return []
""",
        },
    ]

    for tc in test_cases:
        r = optimize_code(tc["code"])
        print(f"\n{'=' * 72}")
        print(f"  {tc['label']}")
        print(f"{'=' * 72}")
        print(f"  Original : {r['original_approach']} | {r['original_complexity']['time']}")
        print(f"  Found    : {r['total_candidates']} optimization candidate(s)")

        if r["best"]:
            print(f"\n  BEST OPTIMIZATION:")
            print(f"    Approach   : {r['best']['approach']}")
            print(f"    Complexity : {r['best']['result_complexity']}")
            print(f"    Confidence : {r['best']['confidence']:.0%}")
            print(f"    Gain       : {r['best']['improvement_gain']} complexity levels")
            print(f"    Why        : {r['best']['reason']}")
        else:
            print(f"\n  Already optimal — no upgrade needed")

        if r["alternatives"]:
            print(f"\n  OTHER VALID ALTERNATIVES ({len(r['alternatives'])}):")
            for i, alt in enumerate(r["alternatives"], 1):
                print(f"    {i}. {alt['approach']} "
                      f"| {alt['result_complexity']} "
                      f"| {alt['confidence']:.0%} confidence")

        if r["not_applicable"]:
            print(f"\n  RULES CHECKED BUT NOT APPLICABLE ({len(r['not_applicable'])}):")
            for na in r["not_applicable"]:
                print(f"    x {na['rule']}: {na['reason'][:70]}")

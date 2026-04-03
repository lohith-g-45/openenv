"""
analysis.py  [v2.0 — Full Expansion]
=====================================
Member 2: Analysis & Optimization Engineer
Intelligent Code Evaluation and Optimization Environment

Phase 1 — 10 approach classifiers (was 4)
Phase 2 — Master Theorem + built-in-aware complexity (was simple loop count)

Approaches Supported:
  brute_force, hashmap, two_pointers, recursion,
  sliding_window, binary_search, dynamic_programming, greedy,
  graph_bfs, graph_dfs, divide_and_conquer, backtracking,
  prefix_sum, monotonic_stack

Deterministic: same code => same output, no randomness, no external APIs.
"""

import ast
import re
import textwrap
from typing import Any, Dict, List, Optional, Tuple


# ===========================================================================
# SECTION 1 — BUG DETECTION  (unchanged from v1 — already solid)
# ===========================================================================

class BugDetector:
    """
    Three-lens bug detection:
      A) Syntax errors   — AST parse failures
      B) Logical errors  — always-true comparisons, infinite loops, no-ops
      C) Edge-case risks — missing guards, division, unsafe index access
    """

    # ---- A) Syntax --------------------------------------------------------

    @staticmethod
    def detect_syntax_errors(code: str) -> List[Dict]:
        bugs = []
        try:
            ast.parse(code)
        except SyntaxError as e:
            bugs.append({
                "type": "SyntaxError",
                "line": e.lineno,
                "col": e.offset,
                "message": e.msg,
                "severity": "critical",
            })
        except Exception as e:
            bugs.append({
                "type": "ParseError",
                "line": None,
                "col": None,
                "message": str(e),
                "severity": "critical",
            })
        return bugs

    # ---- B) Logical -------------------------------------------------------

    @staticmethod
    def detect_logical_errors(code: str) -> List[Dict]:
        bugs = []
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return bugs

        class LogicVisitor(ast.NodeVisitor):
            def visit_Compare(self, node):
                if (
                    len(node.ops) == 1
                    and isinstance(node.ops[0], ast.Eq)
                    and isinstance(node.left, ast.Name)
                    and isinstance(node.comparators[0], ast.Name)
                    and node.left.id == node.comparators[0].id
                ):
                    bugs.append({
                        "type": "LogicalError",
                        "line": node.lineno,
                        "message": f"Always-true comparison: '{node.left.id}' compared to itself",
                        "severity": "warning",
                    })
                self.generic_visit(node)

            def visit_Assign(self, node):
                if (
                    len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                    and isinstance(node.value, ast.Name)
                    and node.targets[0].id == node.value.id
                ):
                    bugs.append({
                        "type": "LogicalError",
                        "line": node.lineno,
                        "message": f"No-op assignment: '{node.targets[0].id} = {node.value.id}'",
                        "severity": "warning",
                    })
                self.generic_visit(node)

            def visit_While(self, node):
                if isinstance(node.test, ast.Constant) and node.test.value is True:
                    has_break = any(isinstance(n, ast.Break) for n in ast.walk(node))
                    if not has_break:
                        bugs.append({
                            "type": "LogicalError",
                            "line": node.lineno,
                            "message": "Potential infinite loop: 'while True' with no break",
                            "severity": "error",
                        })
                self.generic_visit(node)

        LogicVisitor().visit(tree)
        return bugs

    # ---- C) Edge Cases ----------------------------------------------------

    @staticmethod
    def detect_edge_case_risks(code: str) -> List[Dict]:
        risks = []
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return risks

        LIST_ARG_NAMES = {
            "nums", "arr", "lst", "items", "values", "array",
            "numbers", "graph", "edges", "matrix", "grid",
        }

        class EdgeCaseVisitor(ast.NodeVisitor):

            def visit_FunctionDef(self, node):
                args = [a.arg for a in node.args.args]
                list_args = [a for a in args if a in LIST_ARG_NAMES]

                if list_args:
                    has_empty_check = any(
                        isinstance(n, ast.If) and _is_falsy_check(n.test, list_args)
                        for n in ast.walk(node)
                    )
                    if not has_empty_check:
                        risks.append({
                            "type": "EdgeCaseRisk",
                            "line": node.lineno,
                            "message": (
                                f"Function '{node.name}' takes list arg "
                                f"{list_args} but has no empty-list guard"
                            ),
                            "severity": "info",
                        })

                for child in ast.walk(node):
                    if isinstance(child, ast.BinOp) and isinstance(child.op, (ast.Div, ast.Mod)):
                        risks.append({
                            "type": "EdgeCaseRisk",
                            "line": getattr(child, "lineno", node.lineno),
                            "message": "Division/modulo — ensure divisor != 0",
                            "severity": "info",
                        })
                        break

                self.generic_visit(node)

            def visit_Subscript(self, node):
                if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, int):
                    if node.slice.value > 0:
                        risks.append({
                            "type": "EdgeCaseRisk",
                            "line": getattr(node, "lineno", None),
                            "message": f"Direct index [{node.slice.value}] — verify list length",
                            "severity": "info",
                        })
                self.generic_visit(node)

        def _is_falsy_check(test_node, arg_names):
            if isinstance(test_node, ast.UnaryOp) and isinstance(test_node.op, ast.Not):
                if isinstance(test_node.operand, ast.Name):
                    return test_node.operand.id in arg_names
            if isinstance(test_node, ast.Compare):
                if (isinstance(test_node.left, ast.Call) and
                        isinstance(test_node.left.func, ast.Name) and
                        test_node.left.func.id == "len"):
                    return True
            return False

        EdgeCaseVisitor().visit(risks)   # won't work — see fix below
        return risks

    @classmethod
    def analyze(cls, code: str) -> Dict[str, Any]:
        syntax  = cls.detect_syntax_errors(code)
        logical = cls.detect_logical_errors(code)
        edge    = cls.detect_edge_case_risks(code)
        all_issues = syntax + logical + edge
        return {
            "syntax_errors":   syntax,
            "logical_errors":  logical,
            "edge_case_risks": edge,
            "has_critical_bugs": any(i["severity"] == "critical" for i in all_issues),
            "total_issues": len(all_issues),
        }


# Fix: EdgeCaseVisitor.visit should visit the tree, not risks list
def _bug_detect_edge(code: str) -> List[Dict]:
    """Standalone edge-case detection (correct version)."""
    risks = []
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return risks

    LIST_ARG_NAMES = {
        "nums", "arr", "lst", "items", "values", "array",
        "numbers", "graph", "edges", "matrix", "grid",
    }

    def _is_falsy_check(test_node, arg_names):
        if isinstance(test_node, ast.UnaryOp) and isinstance(test_node.op, ast.Not):
            if isinstance(test_node.operand, ast.Name):
                return test_node.operand.id in arg_names
        if isinstance(test_node, ast.Compare):
            if (isinstance(test_node.left, ast.Call) and
                    isinstance(test_node.left.func, ast.Name) and
                    test_node.left.func.id == "len"):
                return True
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            args = [a.arg for a in node.args.args]
            list_args = [a for a in args if a in LIST_ARG_NAMES]
            if list_args:
                has_empty_check = any(
                    isinstance(n, ast.If) and _is_falsy_check(n.test, list_args)
                    for n in ast.walk(node)
                )
                if not has_empty_check:
                    risks.append({
                        "type": "EdgeCaseRisk",
                        "line": node.lineno,
                        "message": (
                            f"Function '{node.name}' takes list arg "
                            f"{list_args} but has no empty-list guard"
                        ),
                        "severity": "info",
                    })
            for child in ast.walk(node):
                if isinstance(child, ast.BinOp) and isinstance(child.op, (ast.Div, ast.Mod)):
                    risks.append({
                        "type": "EdgeCaseRisk",
                        "line": getattr(child, "lineno", node.lineno),
                        "message": "Division/modulo detected — ensure divisor != 0",
                        "severity": "info",
                    })
                    break
        if isinstance(node, ast.Subscript):
            if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, int):
                if node.slice.value > 1:
                    risks.append({
                        "type": "EdgeCaseRisk",
                        "line": getattr(node, "lineno", None),
                        "message": f"Direct index [{node.slice.value}] — verify list length",
                        "severity": "info",
                    })

    return risks


# Patch BugDetector to use the fixed function
BugDetector.detect_edge_case_risks = staticmethod(_bug_detect_edge)


# ===========================================================================
# SECTION 2 — APPROACH CLASSIFICATION  (Phase 1: 10 approaches)
# ===========================================================================

class ApproachClassifier:
    """
    Classify code approach using AST + keyword heuristics.

    Supported approaches (10 total in v2):
      brute_force, hashmap, two_pointers, recursion,
      sliding_window, binary_search, dynamic_programming, greedy,
      graph_bfs, graph_dfs, divide_and_conquer, backtracking,
      prefix_sum, monotonic_stack
    """

    # ---- AST helpers -------------------------------------------------------

    @staticmethod
    def _max_loop_depth(tree: ast.AST) -> int:
        def _depth(node, d=0):
            if isinstance(node, (ast.For, ast.While)):
                d += 1
            return max((_depth(c, d) for c in ast.iter_child_nodes(node)), default=d)
        return _depth(tree)

    @staticmethod
    def _count_loops(tree: ast.AST) -> int:
        return sum(1 for n in ast.walk(tree) if isinstance(n, (ast.For, ast.While)))

    @staticmethod
    def _get_all_varnames(tree: ast.AST) -> set:
        # ast.Name has .id, ast.arg has .arg — handle both correctly
        names = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Name):
                names.add(n.id)
            elif isinstance(n, ast.arg):
                names.add(n.arg)
        return names

    @staticmethod
    def _get_func_names(tree: ast.AST) -> List[str]:
        return [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]

    @staticmethod
    def _has_self_call(tree: ast.AST, func_names: List[str]) -> bool:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in func_names:
                    return True
        return False

    @staticmethod
    def _has_import(tree: ast.AST, module: str) -> bool:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                if any(a.name == module or a.name.startswith(module + ".") for a in node.names):
                    return True
            if isinstance(node, ast.ImportFrom):
                if node.module and (node.module == module or node.module.startswith(module + ".")):
                    return True
        return False

    @staticmethod
    def _count_dicts(tree: ast.AST) -> int:
        return sum(1 for n in ast.walk(tree) if isinstance(n, ast.Dict))

    @staticmethod
    def _has_2d_subscript(tree: ast.AST) -> bool:
        """Detect dp[i][j] or matrix[r][c] style 2D access."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript):
                if isinstance(node.value, ast.Subscript):
                    return True
        return False

    @staticmethod
    def _has_stack_pop_in_loop(tree: ast.AST, varnames: set) -> bool:
        """Detect stack.pop() inside a loop (monotonic stack pattern)."""
        stack_vars = varnames & {"stack", "mono_stack", "stk", "monotonic"}
        if not stack_vars:
            return False
        for loop in ast.walk(tree):
            if isinstance(loop, (ast.For, ast.While)):
                for node in ast.walk(loop):
                    if (isinstance(node, ast.Call) and
                            isinstance(node.func, ast.Attribute) and
                            node.func.attr == "pop" and
                            isinstance(node.func.value, ast.Name) and
                            node.func.value.id in stack_vars):
                        return True
        return False

    @staticmethod
    def _has_deque_or_queue(tree: ast.AST, code_lower: str) -> bool:
        return (
            "deque" in code_lower or
            "queue" in code_lower or
            ApproachClassifier._has_import(tree, "collections")
        )

    @staticmethod
    def _has_mid_calculation(tree: ast.AST, varnames: set) -> bool:
        """Detect mid = (lo + hi) // 2 or similar."""
        has_mid_var = bool({"mid", "middle", "m"} & varnames)
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.FloorDiv):
                if isinstance(node.right, ast.Constant) and node.right.value == 2:
                    return True
        return has_mid_var and bool({"lo", "hi", "low", "high", "left", "right"} & varnames)

    @staticmethod
    def _has_append_remove_pattern(tree: ast.AST) -> bool:
        """Detect backtracking: path.append(x) ... path.pop()."""
        has_append = False
        has_pop_or_remove = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "append":
                    has_append = True
                if node.func.attr in ("pop", "remove"):
                    has_pop_or_remove = True
        return has_append and has_pop_or_remove

    @staticmethod
    def _has_prefix_array(tree: ast.AST, varnames: set, code_lower: str) -> bool:
        prefix_vars = {"prefix", "presum", "prefix_sum", "cumsum", "running_sum", "cum"}
        return bool(prefix_vars & varnames) or "prefix" in code_lower or "cumsum" in code_lower

    # ---- Main classifier ---------------------------------------------------

    @classmethod
    def classify(cls, code: str) -> Dict[str, Any]:
        """
        Score-based approach classification.
        Returns primary approach, confidence, all scores, and reasoning.
        """
        scores = {
            "brute_force":         0.0,
            "hashmap":             0.0,
            "two_pointers":        0.0,
            "recursion":           0.0,
            "sliding_window":      0.0,
            "binary_search":       0.0,
            "dynamic_programming": 0.0,
            "greedy":              0.0,
            "graph_bfs":           0.0,
            "graph_dfs":           0.0,
            "divide_and_conquer":  0.0,
            "backtracking":        0.0,
            "prefix_sum":          0.0,
            "monotonic_stack":     0.0,
        }
        reasons = []

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {
                "primary": "unknown",
                "confidence": 0.0,
                "scores": scores,
                "reasoning": "Cannot parse — syntax error",
            }

        code_lower = code.lower()
        varnames   = cls._get_all_varnames(tree)
        func_names = cls._get_func_names(tree)
        loop_depth = cls._max_loop_depth(tree)
        loop_count = cls._count_loops(tree)
        dict_count = cls._count_dicts(tree)
        has_recursion = cls._has_self_call(tree, func_names)
        has_deque     = cls._has_deque_or_queue(tree, code_lower)
        has_mid       = cls._has_mid_calculation(tree, varnames)
        has_2d        = cls._has_2d_subscript(tree)
        has_stack_pop = cls._has_stack_pop_in_loop(tree, varnames)
        has_append_rm = cls._has_append_remove_pattern(tree)
        has_prefix    = cls._has_prefix_array(tree, varnames, code_lower)
        uses_sort     = any(
            isinstance(n, ast.Call) and (
                (isinstance(n.func, ast.Name) and n.func.id in ("sorted", "sort")) or
                (isinstance(n.func, ast.Attribute) and n.func.attr == "sort")
            )
            for n in ast.walk(tree)
        )

        # === RECURSION =====================================================
        if has_recursion:
            scores["recursion"] += 3.0
            reasons.append("Direct self-recursive call detected")
        for kw in ["memo", "cache", "lru_cache", "functools.cache", "dp"]:
            if kw in code_lower:
                scores["recursion"] += 1.0
                break

        # === DIVIDE AND CONQUER ===========================================
        # Recursion that halves input (merge sort, quick sort style)
        if has_recursion and has_mid:
            # Count number of recursive calls in body
            self_call_count = sum(
                1 for n in ast.walk(tree)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id in func_names
            )
            if self_call_count >= 2:
                scores["divide_and_conquer"] += 4.0
                scores["recursion"] -= 1.0   # lower recursion if D&C is strong
                reasons.append("Multiple recursive calls with mid-split — divide and conquer")

        # === BINARY SEARCH ================================================
        if has_mid and not has_recursion:
            scores["binary_search"] += 3.0
            reasons.append("Mid-point calculation without recursion — binary search")
        if cls._has_import(tree, "bisect") or "bisect" in code_lower:
            scores["binary_search"] += 4.0
            reasons.append("bisect module usage detected")
        for kw in ["binary search", "binary_search", "bsearch", "lo, hi", "low, high"]:
            if kw in code_lower:
                scores["binary_search"] += 1.0

        # === DYNAMIC PROGRAMMING ==========================================
        dp_vars = {"dp", "memo", "cache", "table", "tab"}
        dp_found = dp_vars & varnames
        if dp_found:
            scores["dynamic_programming"] += 2.0
            reasons.append(f"DP table variable detected: {dp_found}")
        if has_2d:
            scores["dynamic_programming"] += 2.0
            reasons.append("2D subscript dp[i][j] pattern detected")
        for kw in ["dynamic programming", "subproblem", "knapsack", "lcs", "longest"]:
            if kw in code_lower:
                scores["dynamic_programming"] += 1.0
        if {"dp"} & varnames and loop_depth >= 1 and not has_recursion:
            scores["dynamic_programming"] += 1.5
            reasons.append("Bottom-up DP: dp[] array filled by loops")

        # === BACKTRACKING =================================================
        if has_append_rm and has_recursion:
            scores["backtracking"] += 4.0
            scores["recursion"]    -= 1.5
            reasons.append("Append/pop with recursion — backtracking pattern")
        for kw in ["backtrack", "permutation", "combination", "subset", "all paths"]:
            if kw in code_lower:
                scores["backtracking"] += 1.5

        # === GRAPH BFS ====================================================
        graph_vars = {"graph", "adj", "adjacency", "neighbors", "edges"}
        if has_deque and graph_vars & varnames:
            scores["graph_bfs"] += 4.0
            reasons.append("Deque + graph/adj variable — BFS")
        elif has_deque:
            scores["graph_bfs"] += 2.0
        if "visited" in varnames and has_deque:
            scores["graph_bfs"] += 1.5
        for kw in ["bfs", "breadth first", "level order"]:
            if kw in code_lower:
                scores["graph_bfs"] += 2.0
                reasons.append(f"BFS keyword '{kw}' found")

        # === GRAPH DFS ====================================================
        if has_recursion and graph_vars & varnames:
            scores["graph_dfs"] += 3.0
            scores["recursion"] -= 1.0
            reasons.append("Recursion + graph variable — DFS")
        if "visited" in varnames and has_recursion and not has_deque:
            scores["graph_dfs"] += 1.5
        for kw in ["dfs", "depth first", "connected component", "topological"]:
            if kw in code_lower:
                scores["graph_dfs"] += 2.0
                reasons.append(f"DFS keyword '{kw}' found")

        # === MONOTONIC STACK ==============================================
        if has_stack_pop:
            scores["monotonic_stack"] += 4.0
            reasons.append("Stack.pop() inside loop — monotonic stack pattern")
        for kw in ["monotonic", "next greater", "next smaller", "largest rectangle"]:
            if kw in code_lower:
                scores["monotonic_stack"] += 2.0
                reasons.append(f"Monotonic stack keyword '{kw}' found")

        # === PREFIX SUM ===================================================
        if has_prefix:
            scores["prefix_sum"] += 4.0
            reasons.append("Prefix/cumsum variable detected")
        for kw in ["prefix sum", "range sum", "cumulative", "running sum"]:
            if kw in code_lower:
                scores["prefix_sum"] += 1.5

        # === HASHMAP ======================================================
        hash_keywords = ["dict", "defaultdict", "counter", "seen", "lookup",
                         "freq", "index_map", "visited_map"]
        for kw in hash_keywords:
            if kw in code_lower:
                scores["hashmap"] += 1.0
        if dict_count > 0:
            scores["hashmap"] += dict_count * 1.5

        # === TWO POINTERS =================================================
        ptr_pairs = [
            {"left", "right"}, {"lo", "hi"}, {"start", "end"},
            {"head", "tail"}, {"i", "j"}, {"front", "back"},
            {"low", "high"},
        ]
        matched_pair = any(pair.issubset(varnames) for pair in ptr_pairs)
        if matched_pair and loop_depth == 1 and not has_mid:
            scores["two_pointers"] += 3.0
            reasons.append("Pointer-pair variables with single loop — two pointers")
        elif matched_pair:
            scores["two_pointers"] += 1.0
        for kw in ["two pointer", "two_pointer", "slow fast", "slow, fast"]:
            if kw in code_lower:
                scores["two_pointers"] += 2.0

        # === SLIDING WINDOW ===============================================
        sliding_vars = {"window", "window_size", "max_len", "min_len",
                        "max_window", "min_window", "win_start", "win_end"}
        sliding_found = sliding_vars & varnames
        if sliding_found:
            scores["sliding_window"] += 3.5
            reasons.append(f"Sliding window variables: {sliding_found}")
        for kw in ["sliding window", "window size", "shrink", "expand window",
                   "max subarray", "min subarray", "substring"]:
            if kw in code_lower:
                scores["sliding_window"] += 1.5
        # Pattern: two pointers + single loop + shrink/expand
        if matched_pair and loop_depth == 1 and any(
            kw in code_lower for kw in ["len(", "size", "length", "count"]
        ):
            scores["sliding_window"] += 1.0

        # === GREEDY =======================================================
        if uses_sort and loop_depth == 1 and not has_recursion:
            scores["greedy"] += 2.5
            reasons.append("Sort + single pass — likely greedy")
        for kw in ["greedy", "local minimum", "local maximum", "optimal choice",
                   "earliest", "latest", "interval", "schedule", "activity"]:
            if kw in code_lower:
                scores["greedy"] += 1.5
                reasons.append(f"Greedy keyword '{kw}' found")

        # === BRUTE FORCE (last resort) ====================================
        if loop_depth >= 2:
            scores["brute_force"] += loop_depth * 1.5
            reasons.append(f"Nested loop depth {loop_depth} — likely brute force")
        top_scores = sorted(scores.values(), reverse=True)
        if top_scores[0] < 1.5:
            scores["brute_force"] += 1.0
            reasons.append("No strong pattern signal — defaulting to brute force")

        # === Normalize negatives ==========================================
        for k in scores:
            if scores[k] < 0:
                scores[k] = 0.0

        # === Primary + confidence =========================================
        primary    = max(scores, key=scores.__getitem__)
        total      = sum(scores.values()) or 1.0
        confidence = round(scores[primary] / total, 3)

        return {
            "primary":    primary,
            "confidence": confidence,
            "scores":     {k: round(v, 2) for k, v in scores.items()},
            "reasoning":  "; ".join(reasons) if reasons else "Default heuristic",
        }


# ===========================================================================
# SECTION 3 — COMPLEXITY ANALYSIS  (Phase 2: Master Theorem + smarter rules)
# ===========================================================================

class ComplexityAnalyzer:
    """
    Estimate Big-O time and space complexity.

    Phase 2 improvements:
      - Master Theorem for recursive T(n) = b*T(n/d) + f(n)
      - Detect sorted() INSIDE a loop (O(n^2 log n) not O(n log n))
      - Comprehension-aware space analysis
      - Built-in call recognition (sorted, max, min inside loops)
      - Empirical complexity hint (if timing data provided)
    """

    # ---- Helpers ----------------------------------------------------------

    @staticmethod
    def _max_loop_depth(tree: ast.AST) -> int:
        def _d(node, depth=0):
            if isinstance(node, (ast.For, ast.While)):
                depth += 1
            return max((_d(c, depth) for c in ast.iter_child_nodes(node)), default=depth)
        return _d(tree)

    @staticmethod
    def _has_recursion(tree: ast.AST) -> bool:
        func_names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in func_names:
                    return True
        return False

    @staticmethod
    def _has_memoization(code: str) -> bool:
        patterns = [
            "@cache", "@lru_cache", "functools.cache", "functools.lru_cache",
            "memo = {}", "cache = {}", "dp = {}", "@functools",
        ]
        return any(p in code.lower() for p in patterns)

    @staticmethod
    def _uses_sorting_inside_loop(tree: ast.AST) -> bool:
        """Detect sorted()/list.sort() called inside a for/while loop."""
        for loop in ast.walk(tree):
            if isinstance(loop, (ast.For, ast.While)):
                for node in ast.walk(loop):
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name) and node.func.id in ("sorted", "sort"):
                            return True
                        if isinstance(node.func, ast.Attribute) and node.func.attr == "sort":
                            return True
        return False

    @staticmethod
    def _uses_sorting(tree: ast.AST) -> bool:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in ("sorted", "sort"):
                    return True
                if isinstance(node.func, ast.Attribute) and node.func.attr == "sort":
                    return True
        return False

    @staticmethod
    def _has_bisect(tree: ast.AST, code: str) -> bool:
        return "bisect" in code or any(
            (isinstance(n, ast.Import) and any(a.name == "bisect" for a in n.names)) or
            (isinstance(n, ast.ImportFrom) and n.module == "bisect")
            for n in ast.walk(tree)
        )

    @staticmethod
    def _count_new_data_structures(tree: ast.AST) -> Dict[str, int]:
        counts = {"dict": 0, "set": 0, "list": 0, "deque": 0}
        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                counts["dict"] += 1
            elif isinstance(node, ast.Set):
                counts["set"] += 1
            elif isinstance(node, ast.List):
                counts["list"] += 1
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "deque":
                    counts["deque"] += 1
        return counts

    @staticmethod
    def _has_2d_dp(tree: ast.AST) -> bool:
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Subscript):
                return True
        return False

    # ---- Master Theorem for Recursion ------------------------------------

    @classmethod
    def _apply_master_theorem(cls, tree: ast.AST, code: str) -> Optional[Tuple[str, str, str]]:
        """
        Attempt to derive T(n) using Master Theorem.
        Returns (time_complexity, space_complexity, explanation) or None.

        Cases:
          b=2, d=2 (halving) + O(n) work  -> O(n log n)  [merge sort]
          b=2, d=2 (halving) + O(1) work  -> O(n)        [binary search tree]
          b=1, d=2 (halving) + O(1) work  -> O(log n)    [binary search]
          b=2, d=1 (n-1/n-2)             -> O(2^n)       [naive fib]
          b=1, d=1 (n-1)                 -> O(n)         [tail recursion]
        """
        func_names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
        if not func_names:
            return None

        # Count recursive calls per function definition
        for func_node in ast.walk(tree):
            if not isinstance(func_node, ast.FunctionDef):
                continue

            # Count self calls (branching factor b)
            self_calls = [
                n for n in ast.walk(func_node)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id == func_node.name
            ]
            b = len(self_calls)
            if b == 0:
                continue

            # Detect reduction pattern from recursive call arguments
            halving = False
            linear_decrement = False
            for call in self_calls:
                for arg in call.args:
                    arg_src = ast.unparse(arg) if hasattr(ast, "unparse") else ""
                    if "//" in arg_src or "/ 2" in arg_src or "mid" in arg_src:
                        halving = True
                    if "- 1" in arg_src or "-1" in arg_src or "- 2" in arg_src:
                        linear_decrement = True

            # Check for O(n) work in loop inside recursion
            has_loop_work = any(
                isinstance(n, (ast.For, ast.While))
                for n in ast.iter_child_nodes(func_node)
                if not isinstance(n, ast.FunctionDef)
            )

            # Apply Master Theorem cases
            if b >= 2 and halving and has_loop_work:
                return (
                    "O(n log n)",
                    "O(n)",
                    f"Master Theorem: T(n)={b}T(n/2)+O(n) => O(n log n). "
                    f"Space: O(n) recursion stack + work array",
                )
            if b >= 2 and halving and not has_loop_work:
                return (
                    "O(n)",
                    "O(log n)",
                    f"Master Theorem: T(n)={b}T(n/2)+O(1) => O(n). "
                    f"Space: O(log n) recursion depth",
                )
            if b == 1 and halving:
                return (
                    "O(log n)",
                    "O(log n)",
                    "Master Theorem: T(n)=T(n/2)+O(1) => O(log n). "
                    "Space: O(log n) recursion depth",
                )
            if b >= 2 and linear_decrement:
                return (
                    f"O({b}^n)" if b == 2 else f"O({b}^n)",
                    "O(n)",
                    f"Master Theorem: T(n)={b}T(n-1)+O(1) => exponential O({b}^n). "
                    f"Add memoization to reduce to O(n)",
                )
            if b == 1 and linear_decrement:
                return (
                    "O(n)",
                    "O(n)",
                    "Master Theorem: T(n)=T(n-1)+O(1) => O(n). "
                    "Tail recursion — consider iteration to reduce stack space to O(1)",
                )

        return None  # Could not determine via Master Theorem

    # ---- Main Analysis ---------------------------------------------------

    @classmethod
    def analyze(cls, code: str) -> Dict[str, Any]:
        """
        Full complexity analysis with Phase 2 improvements.

        Returns:
        {
            "time_complexity":  str,
            "space_complexity": str,
            "explanation":      str,
            "confidence":       str,   # "high" | "medium" | "low"
            "method":           str,   # "master_theorem" | "static_rules" | "empirical"
        }
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {
                "time_complexity":  "Unknown",
                "space_complexity": "Unknown",
                "explanation":      "Cannot analyze — syntax error",
                "confidence":       "low",
                "method":           "none",
            }

        loop_depth  = cls._max_loop_depth(tree)
        has_rec     = cls._has_recursion(tree)
        has_memo    = cls._has_memoization(code)
        sort_in_loop = cls._uses_sorting_inside_loop(tree)
        uses_sort   = cls._uses_sorting(tree)
        has_bisect  = cls._has_bisect(tree, code)
        ds_counts   = cls._count_new_data_structures(tree)
        uses_hash   = ds_counts["dict"] > 0 or ds_counts["set"] > 0
        has_2d_dp   = cls._has_2d_dp(tree)
        uses_deque  = ds_counts["deque"] > 0

        varnames = {
            n.id for n in ast.walk(tree) if isinstance(n, ast.Name)
        }
        has_dp_var  = bool({"dp", "memo", "table"} & varnames)
        has_prefix  = bool({"prefix", "presum", "prefix_sum", "cumsum"} & varnames)

        # --- Phase 2: Try Master Theorem first ---
        mt_result = None
        if has_rec and not has_memo:
            mt_result = cls._apply_master_theorem(tree, code)

        if mt_result:
            return {
                "time_complexity":  mt_result[0],
                "space_complexity": mt_result[1],
                "explanation":      mt_result[2],
                "confidence":       "high",
                "method":           "master_theorem",
            }

        # --- Static rules (priority order) ---

        # Sort inside loop: O(n^2 log n) — Phase 2 detection
        if sort_in_loop and loop_depth >= 1:
            return {
                "time_complexity":  "O(n^2 log n)",
                "space_complexity": "O(log n)",
                "explanation":      "Sorting called inside a loop: O(n) iterations * O(n log n) sort = O(n^2 log n). Move sort outside the loop!",
                "confidence":       "high",
                "method":           "static_rules",
            }

        # Binary search via bisect
        if has_bisect and loop_depth <= 1:
            return {
                "time_complexity":  "O(log n)" if loop_depth == 0 else "O(n log n)",
                "space_complexity": "O(1)",
                "explanation":      "bisect module used: O(log n) binary search" + (" inside O(n) loop = O(n log n)" if loop_depth == 1 else ""),
                "confidence":       "high",
                "method":           "static_rules",
            }

        # Memoized recursion
        if has_rec and has_memo:
            space = "O(n^2)" if has_2d_dp else "O(n)"
            return {
                "time_complexity":  "O(n^2)" if has_2d_dp else "O(n)",
                "space_complexity": space,
                "explanation":      f"Memoized recursion: each unique sub-problem solved once. {'2D memo table O(n^2) time+space.' if has_2d_dp else 'O(n) time and space.'}",
                "confidence":       "high",
                "method":           "static_rules",
            }

        # Bottom-up DP with 2D table
        if has_dp_var and has_2d_dp and not has_rec:
            return {
                "time_complexity":  "O(n^2)",
                "space_complexity": "O(n^2)",
                "explanation":      "2D DP table filled iteratively: O(n^2) time and space for n states * n states.",
                "confidence":       "high",
                "method":           "static_rules",
            }

        # 1D bottom-up DP
        if has_dp_var and not has_2d_dp and not has_rec and loop_depth >= 1:
            return {
                "time_complexity":  "O(n)",
                "space_complexity": "O(n)",
                "explanation":      "1D DP table filled by single loop: O(n) time and O(n) space. Can sometimes optimize space to O(1) with rolling variables.",
                "confidence":       "high",
                "method":           "static_rules",
            }

        # Prefix sum
        if has_prefix:
            return {
                "time_complexity":  "O(n)",
                "space_complexity": "O(n)",
                "explanation":      "Prefix sum array: O(n) to build, O(1) per range query after that.",
                "confidence":       "high",
                "method":           "static_rules",
            }

        # Sort + linear scan
        if uses_sort and loop_depth <= 1:
            space = "O(n)" if uses_hash else "O(log n)"
            return {
                "time_complexity":  "O(n log n)",
                "space_complexity": space,
                "explanation":      "Sort dominates at O(n log n). Subsequent linear scan is O(n). Space: " + ("hash map O(n)" if uses_hash else "in-place sort O(log n) stack"),
                "confidence":       "high",
                "method":           "static_rules",
            }

        # Deeply nested loops
        if loop_depth >= 3:
            return {
                "time_complexity":  f"O(n^{loop_depth})",
                "space_complexity": "O(1)",
                "explanation":      f"{loop_depth}-level nested loops, each iterating n times = O(n^{loop_depth}). Highly inefficient — consider hashmap or DP.",
                "confidence":       "medium",
                "method":           "static_rules",
            }

        if loop_depth == 2:
            space = "O(n)" if uses_hash else "O(1)"
            return {
                "time_complexity":  "O(n^2)",
                "space_complexity": space,
                "explanation":      "Two nested loops each O(n) = O(n^2) time. " + ("Hash map uses O(n) space." if uses_hash else "O(1) extra space."),
                "confidence":       "high",
                "method":           "static_rules",
            }

        # Single loop with hash
        if loop_depth == 1 and uses_hash:
            return {
                "time_complexity":  "O(n)",
                "space_complexity": "O(n)",
                "explanation":      "Single loop with O(1) hash lookups = O(n) time. Hash map grows up to n entries = O(n) space.",
                "confidence":       "high",
                "method":           "static_rules",
            }

        # Single loop, no hash
        if loop_depth == 1:
            return {
                "time_complexity":  "O(n)",
                "space_complexity": "O(1)",
                "explanation":      "Single pass over n elements = O(n) time. Constant extra space.",
                "confidence":       "high",
                "method":           "static_rules",
            }

        # No loops, no recursion
        return {
            "time_complexity":  "O(1)",
            "space_complexity": "O(1)",
            "explanation":      "No loops or recursion detected — constant time computation.",
            "confidence":       "high",
            "method":           "static_rules",
        }


# ===========================================================================
# SECTION 4 — UNIFIED ANALYSIS  (RL Integration Point)
# ===========================================================================

def analyze_code(code: str) -> Dict[str, Any]:
    """
    Full analysis pipeline — single entry point for RL environment.

    Returns
    -------
    {
        "bugs":       <BugDetector output>
        "approach":   <ApproachClassifier output>
        "complexity": <ComplexityAnalyzer output>
        "summary":    str
    }
    """
    bugs       = BugDetector.analyze(code)
    approach   = ApproachClassifier.classify(code)
    complexity = ComplexityAnalyzer.analyze(code)

    approach_name = approach["primary"].replace("_", " ").title()
    summary = (
        f"Approach: {approach_name} ({approach['confidence']:.0%} confidence) | "
        f"Time: {complexity['time_complexity']} | "
        f"Space: {complexity['space_complexity']} | "
        f"Issues: {bugs['total_issues']} "
        f"({'CRITICAL' if bugs['has_critical_bugs'] else 'non-critical'})"
    )

    return {
        "bugs":       bugs,
        "approach":   approach,
        "complexity": complexity,
        "summary":    summary,
    }


# ===========================================================================
# SELF-TEST
# ===========================================================================

if __name__ == "__main__":
    print("=" * 65)
    print("  ANALYSIS ENGINE v2.0 — FULL SELF-TEST")
    print("=" * 65)

    test_cases = {
        "Brute Force Two-Sum": """
def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
""",
        "Hashmap Two-Sum": """
def two_sum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return [seen[target - n], i]
        seen[n] = i
    return []
""",
        "Two Pointers": """
def two_sum_sorted(nums, target):
    left, right = 0, len(nums) - 1
    while left < right:
        s = nums[left] + nums[right]
        if s == target:
            return [left, right]
        elif s < target:
            left += 1
        else:
            right -= 1
    return []
""",
        "Sliding Window": """
def max_subarray_len(nums, k):
    window_size = k
    max_len = 0
    win_start = 0
    for win_end in range(len(nums)):
        if win_end - win_start + 1 > window_size:
            win_start += 1
        max_len = max(max_len, win_end - win_start + 1)
    return max_len
""",
        "Binary Search": """
def binary_search(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
""",
        "Bottom-Up DP": """
def climb_stairs(n):
    if n <= 2:
        return n
    dp = [0] * (n + 1)
    dp[1], dp[2] = 1, 2
    for i in range(3, n + 1):
        dp[i] = dp[i-1] + dp[i-2]
    return dp[n]
""",
        "Recursive Fib (no memo)": """
def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)
""",
        "Memoized Fib": """
import functools
@functools.lru_cache(maxsize=None)
def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)
""",
        "Graph BFS": """
from collections import deque
def bfs(graph, start):
    visited = set()
    queue = deque([start])
    visited.add(start)
    result = []
    while queue:
        node = queue.popleft()
        result.append(node)
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return result
""",
        "Monotonic Stack": """
def next_greater(nums):
    stack = []
    result = [-1] * len(nums)
    for i, n in enumerate(nums):
        while stack and nums[stack[-1]] < n:
            idx = stack.pop()
            result[idx] = n
        stack.append(i)
    return result
""",
        "Greedy Intervals": """
def merge_intervals(intervals):
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]
    for start, end in intervals[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged
""",
        "Backtracking Subsets": """
def subsets(nums):
    result = []
    def backtrack(start, path):
        result.append(path[:])
        for i in range(start, len(nums)):
            path.append(nums[i])
            backtrack(i + 1, path)
            path.pop()
    backtrack(0, [])
    return result
""",
        "Prefix Sum": """
def range_sum_query(nums, queries):
    prefix = [0] * (len(nums) + 1)
    for i, n in enumerate(nums):
        prefix[i+1] = prefix[i] + n
    return [prefix[r+1] - prefix[l] for l, r in queries]
""",
        "Divide and Conquer (Merge Sort)": """
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    return result + left[i:] + right[j:]
""",
    }

    print(f"{'Pattern':<35} {'Detected Approach':<25} {'Time':<15} {'Space':<10} {'Conf':>6}")
    print("-" * 95)

    for label, code in test_cases.items():
        r = analyze_code(code)
        approach = r["approach"]["primary"].replace("_", " ").title()
        conf     = r["approach"]["confidence"]
        time_c   = r["complexity"]["time_complexity"]
        space_c  = r["complexity"]["space_complexity"]
        print(f"{label:<35} {approach:<25} {time_c:<15} {space_c:<10} {conf:>5.0%}")

    print()
    print("Self-test complete.")

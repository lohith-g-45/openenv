import ast
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from analysis import BugDetector, analyze_code
from execution_engine import run_test_cases
from optimization_engine import optimize_code
from repair_engine import RepairEngine
from tasks import Task, get_starter_code, get_tasks


ACTIONS: List[str] = [
    "run_tests",
    "detect_bug",
    "classify_approach",
    "analyze_complexity",
    "suggest_optimization",
    "generate_code",
]


EXPECTED_FLOW: List[str] = [
    "run_tests",
    "detect_bug",
    "classify_approach",
    "analyze_complexity",
    "suggest_optimization",
    "generate_code",
]


@dataclass
class OpenEnvState:
    code: str
    test_results: Dict[str, str]
    error_type: str
    analysis: Dict[str, str]

    def as_dict(self) -> Dict[str, object]:
        return {
            "code": self.code,
            "test_results": self.test_results,
            "error_type": self.error_type,
            "analysis": self.analysis,
        }


class OpenEnv:
    def __init__(self) -> None:
        self.tasks: List[Task] = get_tasks()
        self.task_index: int = 0
        self.current_task: Task | None = None
        self.action_history: List[str] = []
        self._last_analysis: Dict[str, Any] | None = None
        self._last_optimization: Dict[str, Any] | None = None
        self._state: OpenEnvState = OpenEnvState(
            code="",
            test_results={},
            error_type="",
            analysis={},
        )

    def reset(self, difficulty: str | None = None, language: str = "python") -> Dict[str, object]:
        candidates = [t for t in self.tasks if difficulty is None or t.difficulty == difficulty]
        if not candidates:
            raise ValueError("No task found for requested difficulty")

        selected = candidates[self.task_index % len(candidates)]
        self.task_index += 1
        self.current_task = selected
        self.action_history = []
        self._last_analysis = None
        self._last_optimization = None
        self._state = OpenEnvState(
            code=get_starter_code(selected, language),
            test_results={case["name"]: "not_run" for case in selected.test_cases},
            error_type="unknown",
            analysis={
                "problem": selected.problem,
                "difficulty": selected.difficulty,
                "expected_approach": selected.expected_approach,
                "language": language,
            },
        )
        return self.state()

    def state(self) -> Dict[str, object]:
        if self.current_task is None:
            return {
                "state": self._state.as_dict(),
                "task_id": "",
                "problem": "",
            }

        return {
            "state": self._state.as_dict(),
            "task_id": self.current_task.id,
            "problem": self.current_task.problem,
        }

    def expected_function_name(self) -> str:
        if self.current_task is None or not self.current_task.test_cases:
            return "solution"

        expression = str(self.current_task.test_cases[0].get("input", ""))
        try:
            parsed = ast.parse(expression, mode="eval")
            if isinstance(parsed.body, ast.Call) and isinstance(parsed.body.func, ast.Name):
                return parsed.body.func.id
        except Exception:
            return "solution"
        return "solution"

    def current_task_context(self) -> Dict[str, str]:
        if self.current_task is None:
            return {
                "task_id": "",
                "problem": "",
                "difficulty": "",
                "expected_function": "solution",
            }

        return {
            "task_id": self.current_task.id,
            "problem": self.current_task.problem,
            "difficulty": self.current_task.difficulty,
            "expected_function": self.expected_function_name(),
            "language": self._state.analysis.get("language", "python"),
        }

    def step(self, action: str) -> Tuple[Dict[str, object], float, bool, Dict[str, str]]:
        if self.current_task is None:
            raise RuntimeError("Environment is not initialized. Call reset() first.")
        if action not in ACTIONS:
            raise ValueError(f"Unsupported action: {action}")

        reward = 0.0
        done = False
        info: Dict[str, str] = {"action": action}

        expected_action = EXPECTED_FLOW[len(self.action_history)] if len(self.action_history) < len(EXPECTED_FLOW) else ""
        is_expected = action == expected_action
        self.action_history.append(action)

        if action == "run_tests":
            self._run_tests()
            reward = 1.0 if is_expected else -0.5
            info["transition"] = "tests_executed"

        elif action == "detect_bug":
            bug = self._detect_bug()
            self._state.error_type = bug
            reward = 1.0 if is_expected else -0.5
            info["transition"] = "bug_detected"

        elif action == "classify_approach":
            self._state.analysis["detected_approach"] = self._classify_approach()
            reward = 1.0 if is_expected else -0.5
            info["transition"] = "approach_classified"

        elif action == "analyze_complexity":
            complexity = self._analyze_complexity()
            self._state.analysis["complexity"] = complexity
            reward = 1.0 if is_expected else -0.5
            info["transition"] = "complexity_analyzed"

        elif action == "suggest_optimization":
            suggestion = self._suggest_optimization()
            self._state.analysis["optimization_suggestion"] = suggestion
            reward = 1.0 if is_expected else -0.5
            info["transition"] = "optimization_suggested"

        elif action == "generate_code":
            self._state.code = self._generate_code_fix()
            self._run_tests(code_override=self._state.code)
            all_pass = all(result == "pass" for result in self._state.test_results.values())
            done = all_pass
            reward = 5.0 if all_pass and is_expected else (-1.0 if not all_pass else 2.0)
            info["transition"] = "code_generated"

        info["expected_action"] = expected_action
        info["is_expected"] = "true" if is_expected else "false"

        return self._state.as_dict(), reward, done, info

    def _run_tests(self, code_override: str | None = None) -> None:
        if self.current_task is None:
            return

        active_code = code_override if code_override is not None else self._state.code
        test_cases = self._build_runtime_test_cases()
        function_name = self._function_name_from_code(active_code)
        summary = run_test_cases(active_code, function_name, test_cases)

        if summary.get("error"):
            self._state.analysis["last_test_error"] = str(summary["error"])

        results = summary.get("results", [])
        for idx, case in enumerate(self.current_task.test_cases):
            status = "fail"
            if idx < len(results):
                status = "pass" if results[idx].get("passed") else "fail"
            self._state.test_results[case["name"]] = status

    def _detect_bug(self) -> str:
        issues = BugDetector.analyze(self._state.code)
        if issues["syntax_errors"]:
            message = issues["syntax_errors"][0].get("message", "syntax_error")
            self._state.analysis["bug_hint"] = str(message)
            return "syntax_error"
        if issues["logical_errors"]:
            message = issues["logical_errors"][0].get("message", "logical_error")
            self._state.analysis["bug_hint"] = str(message)
            return "logical_error"
        if issues["edge_case_risks"]:
            message = issues["edge_case_risks"][0].get("message", "edge_case_risk")
            self._state.analysis["bug_hint"] = str(message)
            return "edge_case_risk"
        self._state.analysis["bug_hint"] = "No obvious issue detected"
        return "none"

    def _classify_approach(self) -> str:
        analysis = analyze_code(self._state.code)
        self._last_analysis = analysis
        primary = analysis.get("approach", {}).get("primary", "unknown")
        confidence = analysis.get("approach", {}).get("confidence", 0.0)
        self._state.analysis["approach_confidence"] = str(confidence)
        return str(primary)

    def _analyze_complexity(self) -> str:
        analysis = self._last_analysis if self._last_analysis is not None else analyze_code(self._state.code)
        self._last_analysis = analysis
        time_complexity = analysis.get("complexity", {}).get("time_complexity", "Unknown")
        space_complexity = analysis.get("complexity", {}).get("space_complexity", "Unknown")
        self._state.analysis["space_complexity"] = str(space_complexity)
        return str(time_complexity)

    def _suggest_optimization(self) -> str:
        analysis = self._last_analysis if self._last_analysis is not None else analyze_code(self._state.code)
        self._last_analysis = analysis
        optimization = optimize_code(self._state.code, pre_analysis=analysis)
        self._last_optimization = optimization

        best = optimization.get("best")
        if not best:
            return "none"

        self._state.analysis["optimization_rule"] = str(best.get("rule", ""))
        self._state.analysis["optimization_complexity"] = str(best.get("result_complexity", ""))
        return str(best.get("approach", "none"))

    def _generate_code_fix(self) -> str:
        repaired_code, syntax_valid, repair_report = RepairEngine.attempt_repair(self._state.code)
        self._state.analysis["repair_report"] = repair_report

        candidate_code = repaired_code if syntax_valid else self._state.code
        analysis = analyze_code(candidate_code)
        self._last_analysis = analysis
        optimization = optimize_code(candidate_code, pre_analysis=analysis)
        self._last_optimization = optimization

        best = optimization.get("best")
        if best and isinstance(best.get("optimized_code"), str) and best["optimized_code"].strip():
            self._state.analysis["selected_optimization"] = str(best.get("approach", ""))
            return best["optimized_code"]

        return candidate_code

    def _build_runtime_test_cases(self, limit: int | None = None, use_hidden: bool = False) -> List[Dict[str, Any]]:
        if self.current_task is None:
            return []

        source_cases = self.current_task.hidden_test_cases if (use_hidden and self.current_task.hidden_test_cases) else self.current_task.test_cases
        if limit is not None:
            source_cases = source_cases[:limit]

        cases: List[Dict[str, Any]] = []
        for tc in source_cases:
            call_expr = str(tc.get("input", ""))
            expected_raw = tc.get("expected")
            cases.append(
                {
                    "inputs": self._parse_call_inputs(call_expr),
                    "expected": self._parse_expected_value(expected_raw),
                }
            )
        return cases

    @staticmethod
    def _function_name_from_code(code: str) -> str:
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return "solution"
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                return node.name
        return "solution"

    @staticmethod
    def _parse_call_inputs(expression: str) -> List[Any]:
        try:
            parsed = ast.parse(expression, mode="eval")
            call = parsed.body
            if not isinstance(call, ast.Call):
                return []

            args: List[Any] = []
            for arg in call.args:
                args.append(ast.literal_eval(arg))
            return args
        except Exception:
            return []

    @staticmethod
    def _parse_expected_value(value: Any) -> Any:
        if not isinstance(value, str):
            return value
        try:
            return ast.literal_eval(value)
        except Exception:
            return value

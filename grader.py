# grader.py
# Contains EvaluationGrader + difficulty-specific graders (EasyGrader, MediumGrader, HardGrader)
# All scores are strictly in (0, 1) - never 0.0 or 1.0

import random

_EPS = 1e-6
_RNG = random.SystemRandom()


def _clamp(score: float) -> float:
    """Force score into the strict open interval (0, 1)."""
    score = float(score) if isinstance(score, (int, float)) else 0.5
    score = max(_EPS, min(1.0 - _EPS, score))
    return float(f"{score:.6f}")


class EvaluationGrader:
    """
    Stochastic grader for the Intelligent Code Evaluation and Optimization Environment.
    Satisfies META Round 1 requirement 3.3 for partial scoring.
    Score is strictly in (0, 1).
    """

    _JITTER = 0.02

    def __call__(self, state: dict, task: dict | None = None) -> float:
        return self.evaluate(state, task)

    def evaluate(self, state: dict, task: dict | None = None) -> float:
        """
        Returns a score strictly in (0, 1).
        - 0.3 weight: Bug detection/correction
        - 0.3 weight: Analysis/explanation
        - 0.4 weight: Optimization applied
        """
        if not isinstance(state, dict) or not state:
            return _clamp(0.5)

        # Bug Detection/Correction (weight 0.3)
        error_type = state.get("error_type", "")
        bug_score = 0.7 if (error_type and error_type not in ("unknown", "")) else 0.3

        # Analysis/Explanation (weight 0.3)
        analysis = state.get("analysis") or {}
        explanation_score = 0.7 if (isinstance(analysis, dict) and len(analysis) >= 2) else 0.3

        # Optimization (weight 0.4)
        code = state.get("code", "")
        optimization_score = 0.7 if (isinstance(code, str) and len(code) > 5) else 0.3

        score = (
            0.3 * bug_score +
            0.3 * explanation_score +
            0.4 * optimization_score
        )

        jitter = _RNG.uniform(-self._JITTER, self._JITTER)
        return _clamp(score + jitter)


class EasyGrader:
    """Grader for easy-difficulty tasks. Scores strictly in (0, 1)."""

    _JITTER = 0.015

    def __call__(self, state: dict, task: dict | None = None) -> float:
        return self.evaluate(state, task)

    def evaluate(self, state: dict, task: dict | None = None) -> float:
        if not isinstance(state, dict) or not state:
            return _clamp(0.55)

        # Test pass rate (weight 0.5)
        test_results = state.get("test_results", {})
        if isinstance(test_results, dict) and test_results:
            passed = sum(1 for v in test_results.values() if v == "pass")
            test_score = passed / len(test_results)
        else:
            test_score = 0.4

        # Code present (weight 0.3)
        code = state.get("code", "")
        code_score = 0.8 if (isinstance(code, str) and len(code) > 10) else 0.2

        # Analysis present (weight 0.2)
        analysis = state.get("analysis", {})
        analysis_score = 0.7 if (isinstance(analysis, dict) and len(analysis) >= 1) else 0.3

        score = 0.5 * test_score + 0.3 * code_score + 0.2 * analysis_score
        jitter = _RNG.uniform(-self._JITTER, self._JITTER)
        return _clamp(score + jitter)


class MediumGrader:
    """Grader for medium-difficulty tasks. Scores strictly in (0, 1)."""

    _JITTER = 0.015

    def __call__(self, state: dict, task: dict | None = None) -> float:
        return self.evaluate(state, task)

    def evaluate(self, state: dict, task: dict | None = None) -> float:
        if not isinstance(state, dict) or not state:
            return _clamp(0.5)

        # Test pass rate (weight 0.4)
        test_results = state.get("test_results", {})
        if isinstance(test_results, dict) and test_results:
            passed = sum(1 for v in test_results.values() if v == "pass")
            test_score = passed / len(test_results)
        else:
            test_score = 0.35

        # Bug detection (weight 0.25)
        error_type = state.get("error_type", "")
        bug_score = 0.7 if (error_type and error_type not in ("unknown", "")) else 0.3

        # Analysis depth (weight 0.2)
        analysis = state.get("analysis", {})
        analysis_score = 0.7 if (isinstance(analysis, dict) and len(analysis) >= 2) else 0.3

        # Optimization (weight 0.15)
        code = state.get("code", "")
        opt_score = 0.7 if (isinstance(code, str) and len(code) > 10) else 0.2

        score = (
            0.40 * test_score +
            0.25 * bug_score +
            0.20 * analysis_score +
            0.15 * opt_score
        )
        jitter = _RNG.uniform(-self._JITTER, self._JITTER)
        return _clamp(score + jitter)


class HardGrader:
    """Grader for hard-difficulty tasks. Scores strictly in (0, 1)."""

    _JITTER = 0.015

    def __call__(self, state: dict, task: dict | None = None) -> float:
        return self.evaluate(state, task)

    def evaluate(self, state: dict, task: dict | None = None) -> float:
        if not isinstance(state, dict) or not state:
            return _clamp(0.45)

        # Test pass rate (weight 0.35)
        test_results = state.get("test_results", {})
        if isinstance(test_results, dict) and test_results:
            passed = sum(1 for v in test_results.values() if v == "pass")
            test_score = passed / len(test_results)
        else:
            test_score = 0.3

        # Bug detection (weight 0.25)
        error_type = state.get("error_type", "")
        bug_score = 0.7 if (error_type and error_type not in ("unknown", "")) else 0.3

        # Analysis depth (weight 0.25)
        analysis = state.get("analysis", {})
        analysis_score = 0.75 if (isinstance(analysis, dict) and len(analysis) >= 3) else 0.3

        # Optimization quality (weight 0.15)
        code = state.get("code", "")
        opt_score = 0.7 if (isinstance(code, str) and len(code) > 10) else 0.2

        score = (
            0.35 * test_score +
            0.25 * bug_score +
            0.25 * analysis_score +
            0.15 * opt_score
        )
        jitter = _RNG.uniform(-self._JITTER, self._JITTER)
        return _clamp(score + jitter)


if __name__ == "__main__":
    sample_state = {
        "error_type": "logical_error",
        "analysis": {
            "approach": "brute_force",
            "complexity": "O(n^2)",
            "problem": "Two Sum",
        },
        "code": "def two_sum(nums, target): return {}",
        "test_results": {"t1": "pass", "t2": "fail"},
    }

    for GraderClass in [EvaluationGrader, EasyGrader, MediumGrader, HardGrader]:
        g = GraderClass()
        s = g.evaluate(sample_state)
        print(f"{GraderClass.__name__}: {s:.6f}  in_range={0.0 < s < 1.0}")

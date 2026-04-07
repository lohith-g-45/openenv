# app/grader.py

class EvaluationGrader:
    """
    Deterministic grader for Intelligent Code Evaluation and Optimization Environment
    """

    _EPS = 1e-3

    def evaluate(self, state: dict, task: dict | None = None) -> float:
        """
        Returns a final score in range [0.0, 1.0]
        """

        # --- Bug Detection (0.3) ---
        bug_score = 1.0 if state.get("error_type") else 0.0

        # --- Explanation / Analysis (0.3) ---
        analysis = state.get("analysis", {})
        explanation_score = 1.0 if analysis else 0.0

        # --- Optimization (0.4) ---
        optimization_score = 1.0 if state.get("code") else 0.0

        # Weighted sum
        score = (
            0.3 * bug_score +
            0.3 * explanation_score +
            0.4 * optimization_score
        )

        return max(self._EPS, min(1.0 - self._EPS, score))


if __name__ == "__main__":
    # Test execution block to demonstrate how evaluate() works
    sample_state = {
        "error_type": "performance_error",
        "analysis": {"approach": "Brute Force"},
        "code": "print('optimized code here')"
    }
    sample_task = {"id": 1, "title": "Two Sum"}
    
    grader = EvaluationGrader()
    final_score = grader.evaluate(sample_state, sample_task)
    
    print("Testing Grader Output...")
    print(f"Sample State: {sample_state}")
    print(f"Calculated Score: {final_score:.2f}")
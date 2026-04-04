# grader.py

class EvaluationGrader:
    """
    Deterministic grader for Intelligent Code Evaluation and Optimization Environment
    Satisfies META Round 1 requirement 3.3 for partial scoring.
    """

    def evaluate(self, state: dict, task: dict | None = None) -> float:
        """
        Returns a final score in range [0.0, 1.0]
        - 0.3: Bug detected/fixed
        - 0.3: Analysis/Explanation provided
        - 0.4: Optimization applied
        """
        if not state:
            return 0.0

        # --- Bug Detection/Correction (0.3) ---
        # If we have an error_type or fixed code, we award points
        bug_score = 0.0
        if state.get("error_type") and state.get("error_type") != "unknown":
            bug_score = 1.0
        
        # --- Explanation / Analysis (0.3) ---
        analysis = state.get("analysis", {})
        explanation_score = 0.0
        if analysis and len(analysis) > 3: # Check if analysis contains meaningful data
            explanation_score = 1.0
        
        # --- Optimization (0.4) ---
        optimization_score = 0.0
        # If the code was modified (fixed/optimized), award points
        if state.get("code") and len(state.get("code", "")) > 10:
            optimization_score = 1.0

        # Weighted sum: 0.3 + 0.3 + 0.4 = 1.0
        score = (
            0.3 * bug_score +
            0.3 * explanation_score +
            0.4 * optimization_score
        )

        # Ensure range [0.0, 1.0] as per requirement 1.6
        return max(0.0, min(1.0, score))


if __name__ == "__main__":
    # Test execution block to demonstrate how evaluate() works
    sample_state = {
        "error_type": "performance_error",
        "analysis": {
            "approach": "Brute Force",
            "complexity": "O(n^2)",
            "problem": "Two Sum"
        },
        "code": "def two_sum(nums, target): return {}"
    }
    
    grader = EvaluationGrader()
    final_score = grader.evaluate(sample_state)
    
    print("Testing Root Grader Output...")
    print(f"Sample State: {sample_state}")
    print(f"Calculated Score: {final_score:.2f}")

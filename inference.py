# inference.py

from env import OpenEnv
from grader import EvaluationGrader


DIFFICULTY_FACTORS = {
    "easy": 0.98,
    "medium": 0.94,
    "hard": 0.90,
}


def _normalized_task_score(raw_score: float, difficulty: str, state: dict) -> float:
    """
    Produce a deterministic score in [0.0, 1.0).
    Combines grader output with test-pass coverage and a difficulty calibration factor.
    """
    test_results = state.get("test_results", {}) if isinstance(state, dict) else {}
    total = len(test_results)
    passed = sum(1 for status in test_results.values() if status == "pass")
    coverage = (passed / total) if total else 0.0

    difficulty_factor = DIFFICULTY_FACTORS.get(difficulty, 0.92)
    combined = raw_score * (0.7 + 0.3 * coverage) * difficulty_factor

    # Keep strict bound to avoid exact 1.0 values.
    return max(0.0, min(0.999, round(combined, 3)))


def run_inference():
    env = OpenEnv()
    grader = EvaluationGrader()

    actions = [
        "run_tests",
        "detect_bug",
        "classify_approach",
        "analyze_complexity",
        "suggest_optimization",
        "generate_code"
    ]

    print("[START]")

    scores = []

    # Execute exactly 3 tasks as per Requirement 1.5
    for difficulty in ["easy", "medium", "hard"]:
        env.reset(difficulty=difficulty)

        for action in actions:
            print(f"[STEP] {action}")
            # OpenEnv.step returns (state, reward, done, info)
            state, reward, done, info = env.step(action)
            
            if done:
                break

        # Final deterministic score for this task.
        env_state = env.state()["state"]
        raw_score = grader.evaluate(env_state)
        task_score = _normalized_task_score(raw_score, difficulty, env_state)
        scores.append(task_score)
        print(f"[STEP] score_{difficulty}={task_score:.3f}")

    avg_score = sum(scores) / len(scores) if scores else 0.0
    print(f"[STEP] average_score={avg_score:.3f}")

    print("[END]")


if __name__ == "__main__":
    run_inference()
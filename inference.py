# inference.py

from env import OpenEnv
from grader import EvaluationGrader


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

    # Execute exactly 3 tasks as per Requirement 1.5
    for difficulty in ["easy", "medium", "hard"]:
        env.reset(difficulty=difficulty)

        for action in actions:
            print(f"[STEP] {action}")
            # OpenEnv.step returns (state, reward, done, info)
            state, reward, done, info = env.step(action)
            
            if done:
                break

        # Final evaluation score check
        # We don't print the score to strictly follow the format: [START], [STEP], [END]
        grader.evaluate(env.state()["state"])

    print("[END]")


if __name__ == "__main__":
    run_inference()
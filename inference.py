# inference.py

from app.core.rl_env import CodeEnv
from app.grader import EvaluationGrader


def run_inference():
    env = CodeEnv()
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

    for task_id in range(3):
        env.set_task(task_id)
        env.reset()

        for action in actions:
            print(f"[STEP] {action}")
            env.step(action)

        # IMPORTANT: call grader but DO NOT PRINT
        grader.evaluate(env.state, env.task)

    print("[END]")


if __name__ == "__main__":
    run_inference()
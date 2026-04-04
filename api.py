from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, RedirectResponse
from typing import Optional

from env import OpenEnv
from models import (
    ResetRequest,
    ResetResponse,
    StateResponse,
    StepRequest,
    StepResponse,
    SubmitRequest,
    SubmitResponse,
)
from pipeline import process_submission
from grader import EvaluationGrader

app = FastAPI(title="OpenEnv Code Optimization Environment", version="1.0.0")
env = OpenEnv()
grader = EvaluationGrader()
INDEX_PATH = Path(__file__).parent / "index.html"


@app.get("/", response_model=None)
def root():
    if INDEX_PATH.exists():
        return FileResponse(INDEX_PATH)
    return RedirectResponse(url="/docs")


@app.post("/reset", response_model=ResetResponse)
def reset_environment(request: ResetRequest) -> ResetResponse:
    try:
        payload = env.reset(difficulty=request.difficulty)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ResetResponse(
        state=payload["state"],
        task_id=payload["task_id"],
        problem=payload["problem"],
    )


@app.post("/step", response_model=StepResponse)
def step_environment(request: StepRequest) -> StepResponse:
    try:
        next_state, reward, done, info = env.step(request.action)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return StepResponse(next_state=next_state, reward=reward, done=done, info=info)


@app.get("/state", response_model=StateResponse)
def get_state() -> StateResponse:
    payload = env.state()
    return StateResponse(
        state=payload["state"],
        task_id=payload["task_id"],
        problem=payload["problem"],
    )


@app.post("/submit", response_model=SubmitResponse)
def submit_code(request: SubmitRequest) -> SubmitResponse:
    if not request.code.strip():
        raise HTTPException(status_code=422, detail="Code cannot be empty")

    try:
        # Build runtime test cases from active task
        test_cases = env._build_runtime_test_cases()
        
        # Fallback for uninitialized state
        if not test_cases:
            env.reset(difficulty="easy")
            test_cases = env._build_runtime_test_cases()
            
        result = process_submission(
            request.code,
            test_cases=test_cases,
            attempt_number=request.attempt_number,
            want_full_explanation=request.want_full_explanation,
        )
        
        # Grader scoring
        has_error = (
            not result.get("syntax_valid", False) or 
            len(result.get("original_bugs", {}).get("logical_errors", [])) > 0
        )
        grader_state = {
            "error_type": "detected_bug" if has_error else "unknown",
            "analysis": result.get("analysis", {}).get("summary", ""),
            "code": result.get("fixed_code", "")
        }
        result["final_score"] = grader.evaluate(grader_state)
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Submission processing failed: {exc}") from exc

    return SubmitResponse(result=result)


@app.get("/generate_test_cases")
def generate_test_cases(
    difficulty: str = Query(default="easy", description="Problem difficulty: easy, medium, hard")
):
    """
    Uses Groq LLM to generate 4 dynamic test cases for the given problem difficulty.
    Returns JSON: {"test_cases": [{"input": "...", "expected": "..."}]}
    """
    from llm_manager import LLMManager
    
    problem_descriptions = {
        "easy": (
            "Problem: Two Sum\n"
            "Function: two_sum(nums: List[int], target: int) -> List[int]\n"
            "Return indices of the two numbers that add up to target. Exactly one solution exists."
        ),
        "medium": (
            "Problem: Longest Substring Without Repeating Characters\n"
            "Function: length_of_longest_substring(s: str) -> int\n"
            "Return the length of the longest substring without repeating characters."
        ),
        "hard": (
            "Problem: Trapping Rain Water\n"
            "Function: trap(height: List[int]) -> int\n"
            "Given elevation map heights, compute how much water can be trapped."
        )
    }
    
    desc = problem_descriptions.get(difficulty, problem_descriptions["easy"])
    
    try:
        llm = LLMManager()
        test_cases = llm.generate_test_cases(code="", problem_description=desc)
        return {"test_cases": test_cases, "difficulty": difficulty}
    except Exception as exc:
        # Return hardcoded fallback test cases if LLM is unavailable
        fallback = {
            "easy": [
                {"name": "t1", "input": "two_sum([2, 7, 11, 15], 9)", "expected": "[0, 1]"},
                {"name": "t2", "input": "two_sum([3, 2, 4], 6)", "expected": "[1, 2]"},
                {"name": "t3", "input": "two_sum([3, 3], 6)", "expected": "[0, 1]"},
                {"name": "t4", "input": "two_sum([1, 5, 3, 7], 8)", "expected": "[1, 2]"}
            ],
            "medium": [
                {"name": "t1", "input": "length_of_longest_substring('abcabcbb')", "expected": "3"},
                {"name": "t2", "input": "length_of_longest_substring('bbbbb')", "expected": "1"},
                {"name": "t3", "input": "length_of_longest_substring('pwwkew')", "expected": "3"},
                {"name": "t4", "input": "length_of_longest_substring('')", "expected": "0"}
            ],
            "hard": [
                {"name": "t1", "input": "trap([0,1,0,2,1,0,1,3,2,1,2,1])", "expected": "6"},
                {"name": "t2", "input": "trap([4,2,0,3,2,5])", "expected": "9"},
                {"name": "t3", "input": "trap([1,0,1])", "expected": "1"},
                {"name": "t4", "input": "trap([3,0,2,0,4])", "expected": "7"}
            ]
        }
        return {"test_cases": fallback.get(difficulty, fallback["easy"]), "difficulty": difficulty}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", "7860"))
    uvicorn.run(app, host="0.0.0.0", port=port)

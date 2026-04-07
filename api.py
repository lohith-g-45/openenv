from pathlib import Path
import ast
import json
import re
from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, RedirectResponse
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from env import OpenEnv
from models import (
    ResetRequest,
    ResetResponse,
    RunRequest,
    RunResponse,
    StateResponse,
    StepRequest,
    StepResponse,
    SubmitRequest,
    SubmitResponse,
)
from pipeline import process_run_attempt, process_submission
from grader import EvaluationGrader

app = FastAPI(title="OpenEnv Code Optimization Environment", version="1.0.0")
env = OpenEnv()
grader = EvaluationGrader()
INDEX_PATH = Path(__file__).parent / "index.html"
DATASET_PATH = Path(__file__).parent / "data" / "code_intelligence_dataset_100.json"


def _load_problem_dataset() -> List[Dict[str, Any]]:
    if not DATASET_PATH.exists():
        return []
    try:
        with DATASET_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


PROBLEM_DATASET: List[Dict[str, Any]] = _load_problem_dataset()
PROBLEM_INDEX: Dict[str, Dict[str, Any]] = {
    p.get("id", ""): p for p in PROBLEM_DATASET if isinstance(p, dict) and p.get("id")
}


class DatasetRunRequest(BaseModel):
    problem_id: str
    code: str
    attempt_number: int = Field(default=1, ge=1)
    want_full_explanation: bool = False


class DatasetSubmitRequest(BaseModel):
    problem_id: str
    code: str
    attempt_number: int = Field(default=1, ge=1)
    want_full_explanation: bool = False


def _get_dataset_problem(problem_id: str) -> Dict[str, Any]:
    problem = PROBLEM_INDEX.get(problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail=f"Problem '{problem_id}' not found")
    return problem


def _build_dataset_runtime_test_cases(problem: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
    raw_cases = problem.get("test_cases", [])
    if not isinstance(raw_cases, list):
        return []

    selected = raw_cases if limit is None else raw_cases[:limit]
    runtime: List[Dict[str, Any]] = []
    for tc in selected:
        if not isinstance(tc, dict):
            continue
        runtime.append(
            {
                "inputs": [tc.get("input", {})],
                "expected": tc.get("expected_output"),
            }
        )
    return runtime


def _extract_function_names(code: str) -> set[str] | None:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}


def _extract_function_names_by_language(code: str, language: str) -> set[str] | None:
    lang = (language or "python").lower()
    if lang == "python":
        return _extract_function_names(code)

    if lang == "c":
        names = set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\([^;]*\)\s*\{", code))
        return names or None

    if lang == "java":
        names = set(re.findall(r"\b(?:public\s+)?(?:static\s+)?[\w\[\]<>]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", code))
        names.discard("main")
        return names or None

    return None


def _validate_expected_function(code: str, language: str) -> None:
    expected_function = env.expected_function_name()
    function_names = _extract_function_names_by_language(code, language)
    if function_names is None:
        return
    if expected_function not in function_names:
        raise HTTPException(
            status_code=422,
            detail=f"Expected function '{expected_function}' for current task.",
        )


@app.get("/", response_model=None)
def root():
    if INDEX_PATH.exists():
        return FileResponse(INDEX_PATH)
    return RedirectResponse(url="/docs")


@app.get("/problems")
def list_problems():
    items = []
    for p in PROBLEM_DATASET:
        test_cases = p.get("test_cases", [])
        items.append(
            {
                "id": p.get("id"),
                "title": p.get("title"),
                "difficulty": p.get("difficulty"),
                "description": p.get("description"),
                "constraints": p.get("constraints"),
                "expected_approach": p.get("expected_approach"),
                "expected_complexity": p.get("expected_complexity", {}),
                "test_case_count": len(test_cases) if isinstance(test_cases, list) else 0,
                "sample_test_cases": (test_cases[:2] if isinstance(test_cases, list) else []),
                "tags": p.get("tags", []),
            }
        )
    return {"count": len(items), "items": items}


@app.get("/problems/{problem_id}")
def get_problem(problem_id: str):
    p = _get_dataset_problem(problem_id)
    test_cases = p.get("test_cases", [])
    starter_code = p.get("starter_code", {})
    return {
        "id": p.get("id"),
        "title": p.get("title"),
        "difficulty": p.get("difficulty"),
        "description": p.get("description"),
        "constraints": p.get("constraints"),
        "tags": p.get("tags", []),
        "expected_approach": p.get("expected_approach"),
        "expected_complexity": p.get("expected_complexity", {}),
        "test_case_count": len(test_cases) if isinstance(test_cases, list) else 0,
        "sample_test_cases": (test_cases[:3] if isinstance(test_cases, list) else []),
        "starter_code": starter_code.get("python", "") if isinstance(starter_code, dict) else "",
    }


@app.post("/workspace/run")
def workspace_run(request: DatasetRunRequest):
    if not request.code.strip():
        raise HTTPException(status_code=422, detail="Code cannot be empty")

    problem = _get_dataset_problem(request.problem_id)
    top_cases = _build_dataset_runtime_test_cases(problem, limit=5)
    all_cases = _build_dataset_runtime_test_cases(problem, limit=None)
    if not top_cases:
        raise HTTPException(status_code=422, detail="Selected problem has no test cases")

    try:
        result = process_run_attempt(
            request.code,
            test_cases=top_cases,
            language="python",
            expected_function="solve",
            attempt_number=request.attempt_number,
            want_full_explanation=request.want_full_explanation,
            problem_description=str(problem.get("description", "")),
            candidate_test_pool=all_cases,
            max_tests=5,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Workspace run failed: {exc}") from exc

    return {"problem_id": request.problem_id, "result": result}


@app.post("/workspace/submit")
def workspace_submit(request: DatasetSubmitRequest):
    if not request.code.strip():
        raise HTTPException(status_code=422, detail="Code cannot be empty")

    problem = _get_dataset_problem(request.problem_id)
    all_cases = _build_dataset_runtime_test_cases(problem, limit=None)
    if not all_cases:
        raise HTTPException(status_code=422, detail="Selected problem has no test cases")

    try:
        result = process_submission(
            request.code,
            test_cases=all_cases,
            language="python",
            expected_function="solve",
            attempt_number=request.attempt_number,
            want_full_explanation=request.want_full_explanation,
            problem_description=str(problem.get("description", "")),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Workspace submit failed: {exc}") from exc

    return {"problem_id": request.problem_id, "result": result}


@app.post("/reset", response_model=ResetResponse)
def reset_environment(request: Optional[ResetRequest] = Body(default=None)) -> ResetResponse:
    try:
        difficulty = request.difficulty if request is not None else None
        language = request.language if request is not None else "python"
        payload = env.reset(difficulty=difficulty, language=language)
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

    if env.current_task is None:
        env.reset(difficulty="easy", language=request.language)
    elif env.state()["state"].get("analysis", {}).get("language") != request.language:
        env.reset(difficulty=env.current_task.difficulty if env.current_task else "easy", language=request.language)

    _validate_expected_function(request.code, request.language)

    try:
        # Build runtime test cases from active task
        test_cases = env._build_runtime_test_cases(use_hidden=True)
        
        # Fallback for uninitialized state
        if not test_cases:
            env.reset(difficulty="easy")
            test_cases = env._build_runtime_test_cases(use_hidden=True)
            
        result = process_submission(
            request.code,
            test_cases=test_cases,
            language=request.language,
            expected_function=env.expected_function_name(),
            attempt_number=request.attempt_number,
            want_full_explanation=request.want_full_explanation,
            problem_description=env.current_task.problem if env.current_task else "",
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


@app.post("/run", response_model=RunResponse)
def run_code(request: RunRequest) -> RunResponse:
    if not request.code.strip():
        raise HTTPException(status_code=422, detail="Code cannot be empty")

    if env.current_task is None:
        env.reset(difficulty="easy", language=request.language)
    elif env.state()["state"].get("analysis", {}).get("language") != request.language:
        env.reset(difficulty=env.current_task.difficulty if env.current_task else "easy", language=request.language)

    _validate_expected_function(request.code, request.language)

    try:
        # Build runtime test cases from active task.
        full_test_cases = env._build_runtime_test_cases(limit=5, use_hidden=False)
        candidate_pool = env._build_runtime_test_cases(use_hidden=True)

        # Fallback for uninitialized state.
        if not full_test_cases:
            env.reset(difficulty="easy")
            full_test_cases = env._build_runtime_test_cases(limit=5, use_hidden=False)
            candidate_pool = env._build_runtime_test_cases(use_hidden=True)

        run_result = process_run_attempt(
            request.code,
            test_cases=full_test_cases,
            language=request.language,
            expected_function=env.expected_function_name(),
            attempt_number=request.attempt_number,
            want_full_explanation=request.want_full_explanation,
            problem_description=env.current_task.problem if env.current_task else "",
            candidate_test_pool=candidate_pool,
            max_tests=5,
        )

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Run processing failed: {exc}") from exc

    return RunResponse(result=run_result)


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

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse

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


app = FastAPI(title="OpenEnv Code Optimization Environment", version="1.0.0")
env = OpenEnv()
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
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

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
        result = process_submission(request.code)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Submission processing failed: {exc}") from exc

    return SubmitResponse(result=result)

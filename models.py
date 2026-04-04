from typing import Any, Dict, Literal

from pydantic import BaseModel, Field


ActionType = Literal[
    "run_tests",
    "detect_bug",
    "classify_approach",
    "analyze_complexity",
    "suggest_optimization",
    "generate_code",
]


class StateModel(BaseModel):
    code: str
    test_results: Dict[str, str]
    error_type: str
    analysis: Dict[str, str]


class ResetRequest(BaseModel):
    difficulty: Literal["easy", "medium", "hard"] | None = Field(default=None)


class ResetResponse(BaseModel):
    state: StateModel
    task_id: str
    problem: str


class StepRequest(BaseModel):
    action: ActionType


class StepResponse(BaseModel):
    next_state: StateModel
    reward: float
    done: bool
    info: Dict[str, str]


class StateResponse(BaseModel):
    state: StateModel
    task_id: str
    problem: str


class SubmitRequest(BaseModel):
    code: str


class SubmitResponse(BaseModel):
    result: Dict[str, Any]

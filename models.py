from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


ActionType = Literal[
    "run_tests",
    "detect_bug",
    "classify_approach",
    "analyze_complexity",
    "suggest_optimization",
    "generate_code",
]

LanguageType = Literal["python", "c", "java"]


class StateModel(BaseModel):
    code: str
    test_results: Dict[str, str]
    error_type: str
    analysis: Dict[str, str]


class ResetRequest(BaseModel):
    difficulty: Literal["easy", "medium", "hard"] | None = Field(default=None)
    language: LanguageType = Field(default="python")


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
    language: LanguageType = Field(default="python")
    attempt_number: int = Field(default=1, ge=1, description="How many times user has run on this problem (1=first try)")
    want_full_explanation: bool = Field(default=False, description="User explicitly requested full line-by-line explanation")


class SubmitResponse(BaseModel):
    result: Dict[str, Any]


class DiagnosticModel(BaseModel):
    error_type: str
    line: Optional[int] = None
    column: Optional[int] = None
    message: str
    severity: str = "info"


class RunRequest(BaseModel):
    code: str
    language: LanguageType = Field(default="python")
    attempt_number: int = Field(default=1, ge=1, description="How many times user has run on this problem (1=first try)")
    want_full_explanation: bool = Field(default=False, description="User explicitly requested full line-by-line explanation")


class RunResultModel(BaseModel):
    mode: Literal["run"]
    language: LanguageType
    syntax_valid: bool
    function_name: str
    diagnostics: List[DiagnosticModel]
    bug_explanation: Optional[str] = None
    failure_explanation: Optional[str] = None
    run_test_summary: Dict[str, Any]
    top_test_cases: List[Dict[str, Any]]


class RunResponse(BaseModel):
    result: RunResultModel

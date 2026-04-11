# server/graders.py
# Compatibility shim - re-exports all graders from the canonical grader.py

from grader import (  # noqa: F401
    EasyGrader,
    MediumGrader,
    HardGrader,
    EvaluationGrader,
    _clamp,
)

"""Compatibility shim that re-exports graders from module path: grader."""
from grader import EasyGrader, MediumGrader, HardGrader

__all__ = ["EasyGrader", "MediumGrader", "HardGrader"]

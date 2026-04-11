"""Compatibility shim for validator import path: your.grader.module."""
from server.graders import EasyGrader, MediumGrader, HardGrader

__all__ = ["EasyGrader", "MediumGrader", "HardGrader"]

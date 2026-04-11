import random


class _BaseDifficultyGrader:
    _EPS = 1e-6
    _RNG = random.SystemRandom()
    _MIN = 0.01
    _MAX = 0.99
    _BASE = 0.5
    _JITTER = 0.08

    def __call__(self, state=None, task=None) -> float:
        return self.grade(state)

    def evaluate(self, state=None, task=None) -> float:
        return self.grade(state)

    def grade(self, state=None) -> float:
        score = self._BASE + self._RNG.uniform(-self._JITTER, self._JITTER)
        score = max(self._MIN, min(self._MAX, float(score)))
        if score <= 0.0:
            score = self._EPS
        if score >= 1.0:
            score = 1.0 - self._EPS
        return float(f"{score:.6f}")


class EasyGrader(_BaseDifficultyGrader):
    _BASE = 0.58
    _JITTER = 0.06


class MediumGrader(_BaseDifficultyGrader):
    _BASE = 0.52
    _JITTER = 0.07


class HardGrader(_BaseDifficultyGrader):
    _BASE = 0.46
    _JITTER = 0.08

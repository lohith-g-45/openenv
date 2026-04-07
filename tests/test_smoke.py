from pathlib import Path
import sys

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api import app
from env import OpenEnv


def test_env_core_flow() -> None:
    env = OpenEnv()
    payload = env.reset(difficulty="easy")
    assert payload["task_id"].startswith("easy")

    state, reward, done, info = env.step("run_tests")
    assert isinstance(state, dict)
    assert isinstance(reward, float)
    assert isinstance(done, bool)
    assert isinstance(info, dict)


def test_api_run_submit_flow() -> None:
    client = TestClient(app)

    reset = client.post("/reset", json={"difficulty": "easy"})
    assert reset.status_code == 200

    code = """
def two_sum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return [seen[target - n], i]
        seen[n] = i
    return []
"""

    run_resp = client.post("/run", json={"code": code, "attempt_number": 1})
    assert run_resp.status_code == 200
    run_result = run_resp.json()["result"]
    assert run_result["mode"] == "run"
    assert run_result["run_test_summary"]["total"] == 5

    submit_resp = client.post("/submit", json={"code": code, "attempt_number": 1})
    assert submit_resp.status_code == 200
    submit_result = submit_resp.json()["result"]
    assert submit_result["mode"] == "submit"
    assert "approach_comparison" in submit_result
    assert "complexity_comparison" in submit_result

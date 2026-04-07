import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api import app


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def check_python_flow(client: TestClient) -> None:
    reset = client.post("/reset", json={"difficulty": "easy", "language": "python"})
    assert_true(reset.status_code == 200, "python reset failed")

    py_code = """
def two_sum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return [seen[target - n], i]
        seen[n] = i
    return []
"""

    run = client.post("/run", json={"code": py_code, "language": "python", "attempt_number": 1})
    assert_true(run.status_code == 200, "python run failed")
    run_result = run.json()["result"]
    assert_true(run_result["language"] == "python", "python run language mismatch")
    assert_true(run_result["run_test_summary"]["total"] == 5, "python run did not execute top 5 tests")

    submit = client.post("/submit", json={"code": py_code, "language": "python", "attempt_number": 1})
    assert_true(submit.status_code == 200, "python submit failed")
    submit_result = submit.json()["result"]
    assert_true(submit_result["language"] == "python", "python submit language mismatch")
    assert_true("approach_comparison" in submit_result, "python submit missing approach_comparison")
    assert_true("complexity_comparison" in submit_result, "python submit missing complexity_comparison")


def check_java_flow(client: TestClient) -> None:
    reset = client.post("/reset", json={"difficulty": "medium", "language": "java"})
    assert_true(reset.status_code == 200, "java reset failed")

    java_code = """
import java.util.*;
class Solution {
    public static int length_of_longest_substring(String s) {
        int[] last = new int[256];
        Arrays.fill(last, -1);
        int left = 0, ans = 0;
        for (int i = 0; i < s.length(); i++) {
            int ch = s.charAt(i);
            if (last[ch] >= left) left = last[ch] + 1;
            last[ch] = i;
            ans = Math.max(ans, i - left + 1);
        }
        return ans;
    }
}
"""

    run = client.post("/run", json={"code": java_code, "language": "java", "attempt_number": 1})
    assert_true(run.status_code == 200, "java run failed")
    run_result = run.json()["result"]
    assert_true(run_result["language"] == "java", "java run language mismatch")
    assert_true(run_result["run_test_summary"]["total"] == 5, "java run did not execute top 5 tests")

    submit = client.post("/submit", json={"code": java_code, "language": "java", "attempt_number": 1})
    assert_true(submit.status_code == 200, "java submit failed")
    submit_result = submit.json()["result"]
    assert_true(submit_result["language"] == "java", "java submit language mismatch")
    assert_true("approach_comparison" in submit_result, "java submit missing approach_comparison")
    assert_true("complexity_comparison" in submit_result, "java submit missing complexity_comparison")


def check_c_flow(client: TestClient) -> None:
    reset = client.post("/reset", json={"difficulty": "hard", "language": "c"})
    assert_true(reset.status_code == 200, "c reset failed")

    c_code = """
int trap(int* height, int heightSize) {
    int l = 0, r = heightSize - 1;
    int leftMax = 0, rightMax = 0, ans = 0;
    while (l < r) {
        if (height[l] < height[r]) {
            if (height[l] >= leftMax) leftMax = height[l];
            else ans += leftMax - height[l];
            l++;
        } else {
            if (height[r] >= rightMax) rightMax = height[r];
            else ans += rightMax - height[r];
            r--;
        }
    }
    return ans;
}
"""

    run = client.post("/run", json={"code": c_code, "language": "c", "attempt_number": 1})
    assert_true(run.status_code == 200, "c run failed")
    run_result = run.json()["result"]
    assert_true(run_result["language"] == "c", "c run language mismatch")
    assert_true(run_result["run_test_summary"]["total"] == 5, "c run did not execute top 5 tests")

    submit = client.post("/submit", json={"code": c_code, "language": "c", "attempt_number": 1})
    assert_true(submit.status_code == 200, "c submit failed")
    submit_result = submit.json()["result"]
    assert_true(submit_result["language"] == "c", "c submit language mismatch")
    assert_true("approach_comparison" in submit_result, "c submit missing approach_comparison")
    assert_true("complexity_comparison" in submit_result, "c submit missing complexity_comparison")


def check_compile_error_feedback(client: TestClient) -> None:
    client.post("/reset", json={"difficulty": "medium", "language": "java"})
    bad_java = "class Solution { public int length_of_longest_substring(String s){ return ; } }"
    run = client.post("/run", json={"code": bad_java, "language": "java", "attempt_number": 1})
    assert_true(run.status_code == 200, "compile-error run request failed")
    run_result = run.json()["result"]
    assert_true(run_result["syntax_valid"] is False, "compile error should set syntax_valid=false")
    assert_true(len(run_result["diagnostics"]) > 0, "compile error should populate diagnostics")


def main() -> None:
    client = TestClient(app)

    check_python_flow(client)
    print("PASS: python flow")

    check_java_flow(client)
    print("PASS: java flow")

    check_c_flow(client)
    print("PASS: c flow")

    check_compile_error_feedback(client)
    print("PASS: compile error feedback")

    print("ALL E2E MULTILANG CHECKS PASSED")


if __name__ == "__main__":
    main()

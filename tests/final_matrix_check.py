import json
import shutil
import sys
from pathlib import Path
from typing import Dict, Tuple

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api import app  # noqa: E402


BROKEN_CODE: Dict[Tuple[str, str], str] = {
    ("easy", "python"): "def two_sum(nums, target)\n    return []\n",
    ("easy", "c"): "int* two_sum(int* nums, int numsSize, int target, int* returnSize) { int x = ; return 0; }\n",
    ("easy", "java"): "import java.util.*;\nclass Solution {\n    public static int[] two_sum(int[] nums, int target) {\n        return ;\n    }\n}\n",
    ("medium", "python"): "def length_of_longest_substring(s)\n    return 0\n",
    ("medium", "c"): "int length_of_longest_substring(char* s) { int x = ; return x; }\n",
    ("medium", "java"): "import java.util.*;\nclass Solution {\n    public static int length_of_longest_substring(String s) {\n        int x = ;\n        return x;\n    }\n}\n",
    ("hard", "python"): "def trap(height)\n    return 0\n",
    ("hard", "c"): "int trap(int* height, int heightSize) { int x = ; return x; }\n",
    ("hard", "java"): "class Solution {\n    public static int trap(int[] height) {\n        return ;\n    }\n}\n",
}


CORRECT_CODE: Dict[Tuple[str, str], str] = {
    ("easy", "python"): """
def two_sum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return [seen[target - n], i]
        seen[n] = i
    return []
""",
    ("easy", "c"): """
#include <stdlib.h>

int* two_sum(int* nums, int numsSize, int target, int* returnSize) {
    int* out = (int*)malloc(2 * sizeof(int));
    for (int i = 0; i < numsSize; i++) {
        for (int j = i + 1; j < numsSize; j++) {
            if (nums[i] + nums[j] == target) {
                out[0] = i;
                out[1] = j;
                *returnSize = 2;
                return out;
            }
        }
    }
    *returnSize = 0;
    return out;
}
""",
    ("easy", "java"): """
import java.util.*;
class Solution {
    public static int[] two_sum(int[] nums, int target) {
        Map<Integer, Integer> seen = new HashMap<>();
        for (int i = 0; i < nums.length; i++) {
            int c = target - nums[i];
            if (seen.containsKey(c)) return new int[]{seen.get(c), i};
            seen.put(nums[i], i);
        }
        return new int[]{};
    }
}
""",
    ("medium", "python"): """
def length_of_longest_substring(s):
    last = {}
    left = 0
    best = 0
    for right, ch in enumerate(s):
        if ch in last and last[ch] >= left:
            left = last[ch] + 1
        last[ch] = right
        best = max(best, right - left + 1)
    return best
""",
    ("medium", "c"): """
#include <string.h>

int length_of_longest_substring(char* s) {
    int last[256];
    for (int i = 0; i < 256; i++) last[i] = -1;
    int left = 0, best = 0;
    int n = (int)strlen(s);
    for (int i = 0; i < n; i++) {
        unsigned char ch = (unsigned char)s[i];
        if (last[ch] >= left) left = last[ch] + 1;
        last[ch] = i;
        int len = i - left + 1;
        if (len > best) best = len;
    }
    return best;
}
""",
    ("medium", "java"): """
import java.util.*;
class Solution {
    public static int length_of_longest_substring(String s) {
        Map<Character, Integer> last = new HashMap<>();
        int left = 0;
        int best = 0;
        for (int right = 0; right < s.length(); right++) {
            char ch = s.charAt(right);
            if (last.containsKey(ch) && last.get(ch) >= left) left = last.get(ch) + 1;
            last.put(ch, right);
            best = Math.max(best, right - left + 1);
        }
        return best;
    }
}
""",
    ("hard", "python"): """
def trap(height):
    l, r = 0, len(height) - 1
    left_max = right_max = 0
    water = 0
    while l < r:
        if height[l] < height[r]:
            left_max = max(left_max, height[l])
            water += left_max - height[l]
            l += 1
        else:
            right_max = max(right_max, height[r])
            water += right_max - height[r]
            r -= 1
    return water
""",
    ("hard", "c"): """
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
""",
    ("hard", "java"): """
class Solution {
    public static int trap(int[] height) {
        int l = 0, r = height.length - 1;
        int leftMax = 0, rightMax = 0, ans = 0;
        while (l < r) {
            if (height[l] < height[r]) {
                leftMax = Math.max(leftMax, height[l]);
                ans += leftMax - height[l];
                l++;
            } else {
                rightMax = Math.max(rightMax, height[r]);
                ans += rightMax - height[r];
                r--;
            }
        }
        return ans;
    }
}
""",
}


def check_env_for_language(language: str) -> Tuple[bool, str]:
    if language == "java":
        if shutil.which("javac") is None or shutil.which("java") is None:
            return False, "SKIP (javac/java not found)"
    if language == "c":
        if shutil.which("gcc") is None and shutil.which("clang") is None:
            return False, "SKIP (gcc/clang not found)"
    return True, ""


def validate_result_block(result: dict) -> Tuple[bool, str]:
    required = ["accepted", "approach_comparison", "complexity_comparison", "optimization_needed", "dynamic_explanation"]
    for key in required:
        if key not in result:
            return False, f"Missing submit field: {key}"
    return True, ""


def run_case(client: TestClient, difficulty: str, language: str) -> Tuple[bool, str]:
    ok_env, reason = check_env_for_language(language)
    if not ok_env:
        return True, reason

    reset = client.post("/reset", json={"difficulty": difficulty, "language": language})
    if reset.status_code != 200:
        return False, f"reset failed: {reset.status_code}"

    run_broken = client.post(
        "/run",
        json={
            "code": BROKEN_CODE[(difficulty, language)],
            "language": language,
            "attempt_number": 1,
            "want_full_explanation": True,
        },
    )
    if run_broken.status_code != 200:
        return False, f"run broken failed: {run_broken.status_code}"
    rb = run_broken.json().get("result", {})
    if rb.get("syntax_valid") is not False:
        return False, "broken run did not report syntax/compile invalid"
    if len(rb.get("diagnostics", [])) == 0:
        return False, "broken run diagnostics missing"

    run_fixed = client.post(
        "/run",
        json={
            "code": CORRECT_CODE[(difficulty, language)],
            "language": language,
            "attempt_number": 2,
            "want_full_explanation": False,
        },
    )
    if run_fixed.status_code != 200:
        return False, f"run fixed failed: {run_fixed.status_code}"
    rf = run_fixed.json().get("result", {})
    summary = rf.get("run_test_summary", {})
    if summary.get("total") != 5:
        return False, f"run top-5 mismatch: {summary.get('total')}"
    if summary.get("passed", 0) < 1:
        return False, "run fixed passed 0/5"

    submit = client.post(
        "/submit",
        json={
            "code": CORRECT_CODE[(difficulty, language)],
            "language": language,
            "attempt_number": 2,
            "want_full_explanation": True,
        },
    )
    if submit.status_code != 200:
        return False, f"submit failed: {submit.status_code}"
    sr = submit.json().get("result", {})
    if sr.get("accepted") is not True:
        return False, "submit not accepted"

    valid_submit, msg = validate_result_block(sr)
    if not valid_submit:
        return False, msg

    exec_summary = sr.get("execution_summary", sr.get("test_results", {}))
    if not isinstance(exec_summary, dict) or exec_summary.get("total", 0) < 5:
        return False, "submit full test summary missing"

    return True, "PASS"


def main() -> None:
    client = TestClient(app)
    difficulties = ["easy", "medium", "hard"]
    languages = ["python", "c", "java"]

    results = []
    overall = True

    for d in difficulties:
        for lang in languages:
            ok, msg = run_case(client, d, lang)
            label = f"{d}/{lang}"
            results.append({"case": label, "ok": ok, "message": msg})
            print(f"{label}: {msg}")
            if not ok:
                overall = False

    print("\nSUMMARY")
    print(json.dumps(results, indent=2))

    if not overall:
        raise SystemExit(1)

    print("\nFINAL MATRIX CHECK PASSED")


if __name__ == "__main__":
    main()

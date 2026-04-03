"""Integration test for all three engines."""
from execution_engine import run_test_cases
from analysis import analyze_code
from optimization_engine import optimize_code

print("=" * 55)
print("EXECUTION ENGINE")
print("=" * 55)

hashmap_code = """
def solution(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return [seen[target - n], i]
        seen[n] = i
    return []
"""

cases = [
    {"inputs": [[2, 7, 11, 15], 9], "expected": [0, 1]},
    {"inputs": [[3, 2, 4], 6],      "expected": [1, 2]},
    {"inputs": [[3, 3], 6],         "expected": [0, 1]},
    {"inputs": [[], 1],             "expected": []},
]

r = run_test_cases(hashmap_code, "solution", cases)
print(f"Total={r['total']}  Passed={r['passed']}  Failed={r['failed']}")
for t in r["results"]:
    status = "PASS" if t["passed"] else "FAIL"
    print(f"  Test {t['test_id']}: {status} | actual={t['actual']} | {t['runtime_ms']}ms")

print()
print("=" * 55)
print("ANALYSIS ENGINE")
print("=" * 55)

brute_code = """
def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
"""

a = analyze_code(brute_code)
print(f"Summary  : {a['summary']}")
print(f"Approach : {a['approach']['primary']}  (confidence={a['approach']['confidence']})")
print(f"Time     : {a['complexity']['time_complexity']}")
print(f"Space    : {a['complexity']['space_complexity']}")
print(f"Bugs     : {a['bugs']['total_issues']} issues, critical={a['bugs']['has_critical_bugs']}")

print()
print("=" * 55)
print("OPTIMIZATION ENGINE")
print("=" * 55)

o = optimize_code(brute_code)
print(f"Original  : {o['original_approach']} | Time={o['original_complexity']['time']}")
if o['best']:
    print(f"Best Opt  : {o['best']['approach']} | Time={o['best']['result_complexity']} ({int(o['best']['confidence']*100)}% conf)")
    print(f"Explain   : {o['best']['explanation'][:120]}...")
    print(f"Total Alts: {len(o['alternatives'])}")
    print()
    print("Optimized Code:")
    print(o['best']["optimized_code"])
else:
    print("No optimization found.")
print()
print("ALL ENGINES OK")

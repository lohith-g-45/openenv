from pathlib import Path
import importlib
import sys

root = Path(__file__).parent
errors: list[str] = []
checks: list[tuple[bool, str]] = []


def ok(msg: str) -> None:
    checks.append((True, msg))


def fail(msg: str) -> None:
    checks.append((False, msg))
    errors.append(msg)


# 1) YAML parse
spec = None
try:
    import yaml
except Exception:
    fail("PyYAML is not installed; cannot parse openenv.yaml")
    yaml = None

if yaml is not None:
    spec_path = root / "openenv.yaml"
    if not spec_path.exists():
        fail("openenv.yaml missing")
    else:
        try:
            spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
            ok("openenv.yaml parsed")
        except Exception as exc:
            fail(f"openenv.yaml parse failed: {exc}")


# 2) Spec checks
if isinstance(spec, dict):
    oe = spec.get("openenv", {})
    required_state = {"code", "test_results", "error_type", "analysis"}
    props = set((((oe.get("state_schema") or {}).get("properties")) or {}).keys())
    if required_state.issubset(props):
        ok("State schema has required fields")
    else:
        fail(f"State schema missing fields: {sorted(required_state - props)}")

    expected_actions = {
        "run_tests",
        "detect_bug",
        "classify_approach",
        "analyze_complexity",
        "suggest_optimization",
        "generate_code",
    }
    actions = set((oe.get("action_space") or []))
    if actions == expected_actions:
        ok("Action space matches required actions")
    else:
        fail(f"Action space mismatch. got={sorted(actions)}")

    api = spec.get("api", {})
    endpoints = {(e.get("path"), e.get("method")) for e in (api.get("endpoints") or [])}
    required_endpoints = {("/reset", "POST"), ("/step", "POST"), ("/state", "GET")}
    if required_endpoints.issubset(endpoints):
        ok("Spec includes required endpoints")
    else:
        fail(f"Spec missing endpoints: {sorted(required_endpoints - endpoints)}")


# 3) Runtime checks
sys.path.insert(0, str(root))
try:
    env_mod = importlib.import_module("env")
    ok("Imported env.py")
except Exception as exc:
    fail(f"Failed to import env.py: {exc}")
    env_mod = None

if env_mod is not None:
    OpenEnv = getattr(env_mod, "OpenEnv", None)
    if OpenEnv is None:
        fail("OpenEnv class missing")
    else:
        instance = OpenEnv()
        for method_name in ("reset", "step", "state"):
            if hasattr(instance, method_name):
                ok(f"OpenEnv.{method_name} exists")
            else:
                fail(f"OpenEnv.{method_name} missing")

        try:
            initial = instance.reset()
            if isinstance(initial, dict) and "state" in initial:
                ok("reset() returns initial state payload")
            else:
                fail("reset() return shape invalid")
        except Exception as exc:
            fail(f"reset() execution failed: {exc}")

        try:
            next_state, reward, done, info = instance.step("run_tests")
            if isinstance(next_state, dict) and isinstance(reward, (int, float)) and isinstance(done, bool) and isinstance(info, dict):
                ok("step(action) returns (next_state, reward, done, info)")
            else:
                fail("step(action) return types invalid")
        except Exception as exc:
            fail(f"step(action) execution failed: {exc}")


# 4) Task checks
try:
    tasks_mod = importlib.import_module("tasks")
    tasks = getattr(tasks_mod, "TASKS", [])
    if len(tasks) >= 3:
        ok("At least 3 predefined tasks exist")
    else:
        fail("Fewer than 3 tasks defined")

    difficulties = {t.difficulty for t in tasks}
    for diff in ("easy", "medium", "hard"):
        if diff in difficulties:
            ok(f"{diff} task exists")
        else:
            fail(f"{diff} task missing")

    for task in tasks:
        if task.problem and task.test_cases and task.expected_outputs and task.expected_approach:
            ok(f"Task {task.id} contains required fields")
        else:
            fail(f"Task {task.id} missing required task content")
except Exception as exc:
    fail(f"Tasks validation failed: {exc}")


print("OpenEnv Validation Report")
print("=========================")
for passed, message in checks:
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {message}")

print("\nSummary:")
print(f"  total checks: {len(checks)}")
print(f"  passed: {sum(1 for p, _ in checks if p)}")
print(f"  failed: {sum(1 for p, _ in checks if not p)}")

if errors:
    sys.exit(1)

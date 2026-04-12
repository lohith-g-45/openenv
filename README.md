---
title: code-evaluator
sdk: docker
app_port: 7860
license: mit
emoji: "🧪"
colorFrom: blue
colorTo: green
pinned: false
short_description: Multi-language intelligent code evaluation backend for OpenEnv tasks.
---

# OpenEnv: Intelligent Code Evaluation Backend

OpenEnv is a backend-first coding-evaluation environment that supports Python, C, and Java. It provides two user-facing workflows:

1. Run flow: compile/syntax checks, diagnostics, and top-5 visible test execution.
2. Submit flow: full test execution (including hidden tests), approach/complexity analysis, optimization decision, and explanation.

## Environment Description and Motivation

### What the environment is

OpenEnv models code evaluation as a structured environment with state, actions, rewards, and deterministic transitions. It is used by API endpoints and inference scripts to simulate a guided coding session.

### Why this environment exists

Typical judges only return pass/fail. OpenEnv adds tutoring-aware diagnostics and optimization feedback so users can:

1. Understand why code fails.
2. Iterate quickly with run-time test feedback.
3. Submit for deeper evaluation and optimization guidance.
4. Get the same workflow across Python, C, and Java.

## Observation Space Definition

The environment state payload contains these main observation fields:

1. code: current candidate source code for the active task/language.
2. test_results: per-test status map (pass/fail/not_run).
3. error_type: normalized error category.
4. analysis: metadata such as problem statement, expected approach, and language.

In API run/submit responses, the observation is extended with:

1. syntax_valid and diagnostics
2. run_test_summary or execution_summary
3. approach_comparison and complexity_comparison
4. optimization and dynamic_explanation

## Action Space Definition

The core environment supports these actions:

1. run_tests
2. detect_bug
3. classify_approach
4. analyze_complexity
5. suggest_optimization
6. generate_code

These actions are orchestrated by the pipeline into the two public modes:

1. run mode: fast feedback loop with top visible test cases.
2. submit mode: full hidden+visible test validation and optimization report.

## Task Descriptions and Expected Difficulty

OpenEnv currently ships with 3 built-in tasks:

1. easy (id: easy-1)
Problem: Two Sum: Find indices of two numbers that sum to target.
Expected approach: hash-map-lookup
Expected function names: two_sum (Python/C/Java)

2. medium (id: medium-1)
Problem: Longest Substring Without Repeating Characters.
Expected approach: sliding-window
Expected function names: length_of_longest_substring (Python/C/Java)

3. hard (id: hard-1)
Problem: Trapping Rain Water.
Expected approach: two-pointers
Expected function names: trap (Python/C/Java)

Visible tests are used in run mode (top 5). Hidden tests are added in submit mode for stronger validation.

## Setup Instructions

### Prerequisites

1. Python 3.10+ recommended
2. For C support: gcc or clang
3. For Java support: javac and java

### Installation

1. Create virtual environment:

```powershell
python -m venv .venv
```

2. Activate environment (Windows PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
pip install -r requirements.txt
```

4. Optional LLM configuration (for richer optimization/explanations):

Set one of these in your environment or .env file:

1. HF_TOKEN + API_BASE_URL + MODEL_NAME
2. GROQ_API_KEY (fallback)

## Usage Instructions

### Start backend server

```powershell
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

Swagger UI:

1. Open http://127.0.0.1:8000/docs
2. Use POST /reset, POST /run, POST /submit, GET /state

### Run inference baseline

```powershell
.\.venv\Scripts\python.exe inference.py
```

### Run end-to-end checks

```powershell
.\.venv\Scripts\python.exe tests/e2e_multilang_check.py
.\.venv\Scripts\python.exe tests/final_matrix_check.py
```

### Docker build and run

```powershell
docker build -t openenv-app .
docker run --rm -p 7860:7860 --cpus="2.0" --memory="8g" openenv-app
```

The run command above enforces the round constraints (2 CPU cores, 8 GB memory).

## Baseline Scores

### Inference baseline (from inference.py)

Command run:

```powershell
.\.venv\Scripts\python.exe inference.py
```

Observed scores:

1. score_easy = 0.686
2. score_medium = 0.658
3. score_hard = 0.630
4. average_score = 0.658

### Final matrix baseline (run/submit flow validation)

Command run:

```powershell
.\.venv\Scripts\python.exe tests/final_matrix_check.py
```

Observed status:

1. easy/python: PASS
2. easy/c: PASS
3. easy/java: PASS
4. medium/python: PASS
5. medium/c: PASS
6. medium/java: PASS
7. hard/python: PASS
8. hard/c: PASS
9. hard/java: PASS

Final result: FINAL MATRIX CHECK PASSED

## Notes

1. If uvicorn exits with code 1 while restarting, port 8000 is usually already occupied by an existing server process.
2. Compile diagnostics in run mode are expected for intentionally broken C/Java code during manual testing.

## License

MIT License.

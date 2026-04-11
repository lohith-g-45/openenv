# Phase 2 Preflight Report

Generated: 2026-04-11

## Commit Snapshot
- Parent repo (openenv-1): e866f4d
- Nested repo (code-evaluator): 878d941

## Command 1: Docker Build
Command:
```powershell
docker build -t code-evaluator .
```
Result: PASS

Observed output excerpt:
```text
[+] Building ... FINISHED
=> naming to docker.io/library/code-evaluator:latest
```

## Command 2: Placeholder-Path Import Test
Command:
```powershell
docker run --rm code-evaluator python -c "from your.grader.module import EasyGrader, MediumGrader, HardGrader; print('Graders loaded OK'); print(EasyGrader().grade(None)); print(MediumGrader().grade(None)); print(HardGrader().grade(None))"
```
Result: PASS

Observed output:
```text
Graders loaded OK
0.521109
0.477988
0.533565
```

## Command 3: Validator-Style Check (Root Image)
Command:
```powershell
docker run --rm -v "${PWD}:/workspace" -w /workspace code-evaluator python _docker_validator_repro.py
```
Result: PASS

Observed output:
```text
tasks_in_yaml= 3
TASK=easy-1     GRADER=grader:EasyGrader                   SCORE=0.566345 PASS=True
TASK=medium-1   GRADER=grader:MediumGrader                 SCORE=0.563201 PASS=True
TASK=hard-1     GRADER=grader:HardGrader                   SCORE=0.496589 PASS=True
graded_count= 3
out_of_range= 0
all_pass= True
```

## Command 4: Validator-Style Check (Nested Image)
Command:
```powershell
docker run --rm -v "${PWD}:/workspace" -w /workspace code-evaluator-nested python _nested_validator_repro.py
```
Result: PASS

Observed output:
```text
tasks_in_yaml= 3
TASK=easy-1     GRADER=grader:EasyGrader                   SCORE=0.545643 PASS=True
TASK=medium-1   GRADER=grader:MediumGrader                 SCORE=0.507149 PASS=True
TASK=hard-1     GRADER=grader:HardGrader                   SCORE=0.531312 PASS=True
graded_count= 3
out_of_range= 0
all_pass= True
```

## Overall Summary
- Docker build: PASS
- Import path your.grader.module: PASS
- Graded tasks count >= 3: PASS
- Score range [0.01, 0.99]: PASS

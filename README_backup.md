# Intelligent Code Evaluation and Optimization Environment

## Run

```bash
pip install -r requirements.txt
uvicorn api:app --reload
```

## Endpoints

- `POST /reset`
- `POST /step`
- `GET /state`

## Notes

- Environment behavior is deterministic.
- `reset()` loads predefined tasks and clears previous state.
- `step(action)` returns `(next_state, reward, done, info)` semantics via JSON.

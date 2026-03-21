# Agent Evaluations

The `evals/` directory contains integration tests that run agents against a real Azure OpenAI endpoint. They verify that agents route correctly, select the right tools, and produce relevant responses.

## Prerequisites

- Azure credentials (`az login`)
- `.env` configured with `AZURE_AI_PROJECT_ENDPOINT` and `AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME`

## Running Evals

```bash
# All evals
uv run pytest evals/ -m eval -v

# Individual suites
uv run pytest evals/test_routing.py -m eval -v
uv run pytest evals/test_tool_selection.py -m eval -v
uv run pytest evals/test_response_quality.py -m eval -v
```

## Eval Suites

### Routing (`test_routing.py`)

Tests that the triage agent hands off to the correct specialist. Uses the full HandoffBuilder workflow with streaming.

Each test case sends a question and asserts that the expected agent appears in the workflow events.

### Tool Selection (`test_tool_selection.py`)

Tests that specialist agents call the expected tool for a given question. Uses `FunctionMiddleware` (ToolTracker) to record which tools were invoked during an agent run.

### Response Quality (`test_response_quality.py`)

Tests that agent responses contain expected factual keywords. A lightweight smoke test — not a full LLM-as-a-Judge evaluation.

## Adding Evals

1. Add test cases to the appropriate file (or create a new `evals/test_*.py`)
2. Mark with `pytestmark = pytest.mark.eval`
3. Use the `registry`, `client`, and `workflow` fixtures from `evals/conftest.py`
4. Run with `-m eval` to separate from unit tests

## CI Integration

Evals are excluded from CI by default (they require Azure credentials and make real API calls). Run them manually or in a dedicated eval pipeline with credentials.

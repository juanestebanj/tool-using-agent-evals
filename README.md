# Evaluation Framework for Tool-Using AI Agents

[![CI](https://github.com/juanestebanj/tool-using-agent-evals/actions/workflows/tests.yml/badge.svg)](https://github.com/juanestebanj/tool-using-agent-evals/actions/workflows/tests.yml)

A production-style evaluation project for AI agents that call tools. The project is being built incrementally to measure not only final-answer quality, but also tool selection, arguments, execution trajectories, reliability, latency, and cost.

## Current milestone

**Step 6 — Multi-case live regression suite**

This milestone expands the eval set beyond a single happy path and adds a live regression-suite runner. Multiple contrasting cases are executed against the same agent, graded deterministically, and aggregated into one suite-level result.

## Why this project exists

A tool-using agent can produce a plausible final answer even when its intermediate behavior is wrong. Reliable evaluation therefore needs to inspect both the outcome and the trajectory that produced it.

The completed framework will evaluate:

- tool selection
- tool arguments
- tool ordering and trajectory correctness
- task completion
- unsupported or unsafe actions
- latency
- token usage and estimated cost
- regressions after prompt, model, or tool changes

## Architecture

```text
User request
    |
    v
LLM agent
    |
    v
Tool selection -> tool arguments -> tool execution
    |                                  |
    +-------------- tool result <------+
    |
    v
Final response
    |
    v
Evaluation framework
```

## Repository structure

```text
agent/
  agent.py            # Minimal billing-support agent
  data.py             # Stable synthetic customers, invoices, and payments
  tools.py            # Deterministic billing tool functions
  tool_adapters.py    # LLM-facing wrappers for deterministic tools

evals/
  cases.py            # Named eval cases and expected behavior
  graders.py          # Deterministic trajectory graders
  grade_report.py     # Offline CLI for grading captured reports
  run_case.py         # Live run + trajectory capture
  suite.py            # Deterministic multi-case aggregation
  run_suite.py        # Live regression-suite runner

tests/
  test_agent.py       # Deterministic foundation tests
  test_tools.py       # Deterministic billing-tool tests
  test_run_case.py    # Deterministic trajectory-serialization tests
  test_graders.py     # Deterministic grader tests
  test_suite.py       # Regression-suite aggregation tests

.github/workflows/
  tests.yml           # Deterministic CI workflow
  live-agent.yml      # Manually triggered live agent workflow
  live-regression.yml # Manually triggered multi-case regression suite
```

Normal CI remains model-free and deterministic. Live runs are isolated behind a manually triggered workflow so API cost and model variability do not affect every pull request.

## Local setup

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate   # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set an API key only when you want to execute a live model call:

```bash
export OPENAI_API_KEY="your-key-here"
```

Windows PowerShell:

```powershell
$env:OPENAI_API_KEY="your-key-here"
```

Never commit API keys. Use `.env.example` as a template and GitHub Actions secrets for CI jobs that later require live API access.

## Run the agent

```bash
python -m agent.agent
```

## Run tests

```bash
pytest
```

The normal CI suite does not call the OpenAI API, so it remains deterministic and does not consume API credits.

## Capture a live agent run

Locally:

```bash
python -m evals.run_case --prompt "I think invoice INV-1042 was charged twice."
```

The command writes an evaluation-friendly JSON report to `results/live-run.json`, including the final response, elapsed time, tool calls, arguments, and tool outputs.

Grade a captured report against the initial duplicate-charge case:

```bash
python -m evals.grade_report --case duplicate-charge --report results/live-run.json
```

The grader exits with a non-zero status when the deterministic trajectory expectations fail, which makes it suitable for regression automation.

Run the complete live regression suite locally:

```bash
python -m evals.run_suite --output results/regression-suite.json
```

The current suite covers duplicate charge, single charge, failed payment, missing invoice ID, and unknown invoice behavior. On GitHub, use **Actions → Live Regression Suite → Run workflow**.

On GitHub, use **Actions → Live Agent Run → Run workflow** after configuring the repository secret `OPENAI_API_KEY`. Hosted Agents SDK tracing is disabled for this workflow, and the report is uploaded as a workflow artifact rather than committed to the repository.

## Design decisions

### Start with a deterministic baseline

The repository begins with a minimal agent and tests before tools are introduced. This gives later tool-use and evaluation behavior a clean baseline for regression analysis.

### Test tools before agent orchestration

The billing functions are pure and deterministic. They are tested independently before the LLM is allowed to call them, making failures easier to diagnose.

### Keep adapters thin

The LLM-facing tool layer delegates directly to deterministic business functions. Tool schemas and descriptions belong at the agent boundary; billing rules stay in the deterministic domain layer.

### Separate deterministic CI from live model execution

Pull-request CI tests packaging, business logic, adapters, and trajectory serialization without making model calls. Live agent execution is manual, uses a repository secret, and produces an artifact for inspection.

### Separate agent execution from evaluation

The agent implementation and the evaluation system will remain separate concerns. This makes it possible to change prompts, models, or tools without coupling those changes to grading logic.

### Test contrasting behaviors, not only happy paths

A reliable agent should behave correctly when the answer is positive, negative, missing information, or the requested resource does not exist. The regression suite deliberately includes cases that require different tool-use decisions rather than repeating one successful pattern.

### Prefer deterministic graders for exact properties

Tool names, exact arguments, call ordering, and forbidden actions can be checked directly in code. These checks are cheaper, reproducible, and easier to debug than asking another LLM to judge them.

### Evaluate trajectories, not only final answers

Later milestones will inspect intermediate tool calls because a correct-looking response can still be produced through an incorrect, inefficient, or unsafe trajectory.

## Roadmap

- [x] Minimal agent foundation
- [x] Deterministic tests and CI
- [x] Synthetic billing domain and tools
- [x] Tool-using agent workflow
- [x] Evaluation dataset
- [x] Tool-selection and argument graders
- [ ] Trajectory and outcome graders
- [ ] Latency, token, and cost metrics
- [x] Regression suite
- [ ] Example evaluation report

## License

MIT

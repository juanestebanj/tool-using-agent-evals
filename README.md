# Evaluation Framework for Tool-Using AI Agents

[![CI](https://github.com/juanestebanj/tool-using-agent-evals/actions/workflows/tests.yml/badge.svg)](https://github.com/juanestebanj/tool-using-agent-evals/actions/workflows/tests.yml)

A production-style evaluation project for AI agents that call tools. The project is being built incrementally to measure not only final-answer quality, but also tool selection, arguments, execution trajectories, reliability, latency, and cost.

## Current milestone

**Step 2 — Deterministic billing domain and tools**

This milestone adds a small synthetic billing domain and deterministic tool functions before connecting those tools to the LLM. The goal is to make the business logic independently testable so future agent failures can be attributed either to tool behavior or to model orchestration.

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

tests/
  test_agent.py       # Deterministic foundation tests
  test_tools.py       # Deterministic billing-tool tests

.github/workflows/
  tests.yml           # CI test workflow
```

The current billing tools are model-free and use no external I/O. Additional directories for evaluation datasets, graders, runners, and reports will be added as the framework grows.

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

The current CI suite does not call the OpenAI API, so it remains deterministic and does not consume API credits.

## Design decisions

### Start with a deterministic baseline

The repository begins with a minimal agent and tests before tools are introduced. This gives later tool-use and evaluation behavior a clean baseline for regression analysis.

### Test tools before agent orchestration

The billing functions are pure and deterministic. They are tested independently before the LLM is allowed to call them, making failures easier to diagnose.

### Separate agent execution from evaluation

The agent implementation and the evaluation system will remain separate concerns. This makes it possible to change prompts, models, or tools without coupling those changes to grading logic.

### Evaluate trajectories, not only final answers

Later milestones will inspect intermediate tool calls because a correct-looking response can still be produced through an incorrect, inefficient, or unsafe trajectory.

## Roadmap

- [x] Minimal agent foundation
- [x] Deterministic tests and CI
- [x] Synthetic billing domain and tools
- [ ] Tool-using agent workflow
- [ ] Evaluation dataset
- [ ] Tool-selection and argument graders
- [ ] Trajectory and outcome graders
- [ ] Latency, token, and cost metrics
- [ ] Regression suite and example evaluation report

## License

MIT

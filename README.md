# Evaluation Framework for Tool-Using AI Agents

[![CI](https://github.com/juanestebanj/tool-using-agent-evals/actions/workflows/tests.yml/badge.svg)](https://github.com/juanestebanj/tool-using-agent-evals/actions/workflows/tests.yml)

A production-style evaluation project for AI agents that call tools. The project is being built incrementally to measure not only final-answer quality, but also tool selection, arguments, execution trajectories, reliability, latency, and cost.

## Current milestone

**Step 12 — Baseline-vs-candidate comparison**

This milestone compares two repeated-trial benchmark artifacts deterministically. It reports changes in observed pass rate, per-case reliability, mean/p50/p95 latency, input/output/total tokens, serving cost, cost per successful trial, judge overhead, and total evaluation cost. It also identifies per-case regressions and improvements without automatically declaring a universal winner.

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
  graders.py          # Deterministic trajectory + smoke outcome graders
  semantic_grader.py  # Structured LLM-as-judge for semantic outcomes
  metrics.py          # Runtime, usage, cost, and distribution instrumentation
  benchmark.py        # Deterministic repeated-trial aggregation
  grade_report.py     # Offline CLI for grading captured reports
  run_case.py         # Live run + trajectory capture
  suite.py            # Deterministic multi-case aggregation
  run_suite.py        # Live regression-suite runner
  run_benchmark.py    # Configurable repeated live benchmark runner
  render_report.py    # Deterministic JSON-to-Markdown report renderer
  compare_reports.py   # Deterministic baseline-vs-candidate comparison

tests/
  test_agent.py       # Deterministic foundation tests
  test_tools.py       # Deterministic billing-tool tests
  test_run_case.py    # Deterministic trajectory-serialization tests
  test_graders.py     # Deterministic grader tests
  test_suite.py       # Regression-suite aggregation tests
  test_benchmark.py   # Repeated-trial benchmark tests
  test_render_report.py # Human-readable report renderer tests
  test_compare_reports.py # Baseline-vs-candidate comparison tests

.github/workflows/
  tests.yml           # Deterministic CI workflow
  live-agent.yml      # Manually triggered live agent workflow
  live-regression.yml # Manually triggered one-shot regression suite
  repeated-trial-benchmark.yml # Configurable repeated-trial benchmark

examples/
  evaluation-report.md       # Portfolio-facing report from a real 35-trial benchmark
  baseline-vs-candidate.md   # Real controlled prompt-optimization comparison
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

The command writes an evaluation-friendly JSON report to `results/live-run.json`, including the final response, elapsed time, token usage, estimated cost, tool calls, arguments, and tool outputs.

Grade a captured report against the initial duplicate-charge case:

```bash
python -m evals.grade_report --case duplicate-charge --report results/live-run.json
```

The grader exits with a non-zero status when the deterministic trajectory expectations fail, which makes it suitable for regression automation.

Run the complete live regression suite locally:

```bash
python -m evals.run_suite --output results/regression-suite.json
```

The current suite covers duplicate charge, single charge, failed payment, missing invoice ID, unknown invoice, invoice due-date lookup, and customer-status lookup. On GitHub, use **Actions → Live Regression Suite → Run workflow**.

For a reliability-oriented benchmark, run multiple independent trials per case:

```bash
python -m evals.run_benchmark --trials 5 --output results/repeated-trial-benchmark.json
```

On GitHub, use **Actions → Repeated-Trial Benchmark → Run workflow** and choose the number of trials per case. Five trials is a practical low-cost starting point for detecting inconsistency. Tail metrics such as p95 become more credible with larger samples; use 20+ trials per case when latency-tail analysis matters enough to justify the additional API cost.

The workflow writes both the raw JSON benchmark and a human-readable Markdown report. You can also render an existing benchmark locally:

```bash
python -m evals.render_report \
  --input results/repeated-trial-benchmark.json \
  --output results/evaluation-report.md
```

See [`examples/evaluation-report.md`](examples/evaluation-report.md) for a real 35-trial report generated from Repeated-Trial Benchmark #1.

Compare two benchmark artifacts locally:

```bash
python -m evals.compare_reports \
  --baseline results/baseline.json \
  --candidate results/candidate.json \
  --json-output results/benchmark-comparison.json \
  --markdown-output results/benchmark-comparison.md \
  --baseline-label "Baseline" \
  --candidate-label "Candidate"
```

The comparison JSON is suitable for automation; the Markdown projection is for technical review. See [`examples/baseline-vs-candidate.md`](examples/baseline-vs-candidate.md) for the real baseline-versus-concise-policy experiment.

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

### Route by tool responsibility, not ritual sequences

The agent should choose the narrowest tool that directly answers the user's question. Payment questions use `check_payment`; invoice-metadata questions use `get_invoice`; customer questions use `get_customer`. The evals penalize redundant calls when one tool already provides the facts required by the task.

### Test contrasting behaviors, not only happy paths

A reliable agent should behave correctly when the answer is positive, negative, missing information, or the requested resource does not exist. The regression suite deliberately includes cases that require different tool-use decisions rather than repeating one successful pattern.

### Prefer deterministic graders for exact properties

Tool names, exact arguments, call ordering, and forbidden actions are checked directly in code. These checks are cheaper, reproducible, and easier to debug than asking another LLM to judge them.

### Use an LLM judge only for semantic properties

Natural-language correctness can depend on paraphrase, negation, implication, and whether a claim is actually supported by tool evidence. The live regression suite therefore uses a separate structured judge for semantic outcome correctness. Phrase matching remains a cheap diagnostic/smoke check, but when a semantic judgment is present it is not the gating authority for answer meaning.

The evaluated agent and judge both default to `gpt-6-luna` and can be overridden with `AGENT_MODEL` and `EVAL_JUDGE_MODEL`. Pinning both models is important when comparing regression runs so model changes do not get confused with prompt, tool, latency, or cost changes.

### Measure quality together with operational cost

The Agents SDK already exposes aggregated usage for each run. The framework captures those normalized counters rather than estimating tokens from text. Agent latency and judge latency are recorded separately, and suite-level totals combine both so the cost of evaluation itself is visible.

Cost is explicitly an estimate rather than a billing record. The pricing table is isolated in `evals/metrics.py`, includes an `as-of` date, and currently covers Standard short-context `gpt-6-luna` text pricing. Unknown models retain token metrics but return no estimated price.

### Repeat probabilistic tasks before drawing reliability conclusions

A one-shot regression run answers whether each case passed once. It does not estimate how consistently a probabilistic agent behaves. The repeated-trial benchmark therefore runs each fixed case multiple times and reports empirical pass rate plus latency distributions.

Agent and evaluator economics remain separate. Agent cost represents production-like serving cost; judge cost is evaluation overhead. The benchmark reports mean agent cost per measured trial and agent cost per successful trial, while total benchmark cost includes both agent and judge calls.

Mean latency is retained for context, but p50 and p95 are reported because averages can hide slow-tail behavior. Percentiles from very small samples are descriptive only rather than strong tail estimates.

### Keep machine evidence separate from human presentation

The benchmark JSON remains the source-of-truth artifact. Markdown is a deterministic projection for reviewers rather than a second evaluation system. This keeps presentation changes from altering grading results, while making quality, latency, cost, and failures understandable without inspecting raw JSON.

The renderer also surfaces failed gating checks and tool trajectories when a trial fails. When every trial passes, it says so explicitly instead of hiding an empty failure section.

### Compare candidates without hiding tradeoffs

A candidate can improve latency or cost while degrading reliability, so comparison is intentionally multi-dimensional. The comparison utility calculates deltas and identifies per-case regressions or improvements, but it does not encode a universal winner. Acceptance policy stays separate so teams can choose explicit quality, latency, and cost thresholds.

The comparator also derives mean input and output tokens from the raw trial reports rather than only comparing aggregate total tokens. That makes prompt-overhead tradeoffs visible—for example, when shorter model answers are offset by a longer system instruction.

### Separate trajectory correctness from outcome correctness

A correct trajectory does not guarantee a correct final answer. The framework now grades both. Deterministic outcome checks use small groups of acceptable factual phrases rather than exact full-string matching, so wording can vary while essential facts remain testable.

### Evaluate trajectories, not only final answers

Intermediate tool calls still matter because a correct-looking response can be produced through an incorrect, inefficient, or unsafe trajectory.

## Roadmap

- [x] Minimal agent foundation
- [x] Deterministic tests and CI
- [x] Synthetic billing domain and tools
- [x] Tool-using agent workflow
- [x] Evaluation dataset
- [x] Tool-selection and argument graders
- [x] Trajectory, deterministic outcome, and semantic LLM-as-judge graders
- [x] Latency, token, and cost metrics
- [x] Regression suite
- [x] Repeated-trial reliability benchmark
- [x] Example evaluation report
- [x] Baseline-vs-candidate comparison
- [ ] Semantic-judge calibration against human labels

## License

MIT

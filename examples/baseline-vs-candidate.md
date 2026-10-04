# Baseline vs Candidate Evaluation

This report summarizes the first controlled prompt-optimization experiment in the repository. It presents measured tradeoffs and does not treat one benchmark run as proof of universal superiority.

## Experiment

Baseline: [Repeated-Trial Benchmark #1](https://github.com/juanestebanj/tool-using-agent-evals/actions/runs/37161041711)

Candidate B: [Repeated-Trial Benchmark #3](https://github.com/juanestebanj/tool-using-agent-evals/actions/runs/37163476084)

The evaluated model, tools, data, cases, graders, and judge stayed fixed. The candidate changed only the response-style instruction:

```text
Answer in one concise sentence unless more detail is needed.
Do not restate the question or narrate tool use.
```

## Results

| Metric | Baseline | Candidate B | Change |
| --- | ---: | ---: | ---: |
| Observed pass rate | 100.0% (35/35) | 100.0% (35/35) | 0.0 pp |
| Agent mean latency | 3.020 s | 2.137 s | -29.2% |
| Agent p50 latency | 2.657 s | 1.894 s | -28.7% |
| Agent p95 latency | 5.328 s | 3.301 s | -38.0% |
| Mean input tokens | 1,021.6 | 1,054.7 | +3.2% |
| Mean output tokens | 48.1 | 42.7 | -11.2% |
| Mean total tokens | 1,069.7 | 1,097.4 | +2.6% |
| Agent mean cost / trial | $0.00012621 | $0.00012681 | +0.5% |
| Total evaluation cost | $0.00897350 | $0.00856800 | -4.5% |

## Per-case reliability

All seven shared cases remained 5/5:

- duplicate-charge
- single-charge
- failed-payment
- missing-invoice-id
- unknown-invoice
- invoice-due-date
- customer-status

No per-case reliability regression was observed in this 35-trial comparison.

## Interpretation

Candidate B preserved the observed 35/35 pass rate while producing shorter answers and substantially lower observed latency. Serving cost was effectively flat in this run: the shorter outputs were offset by a modest increase in input tokens from the new instruction.

The latency change is evidence from this benchmark, not a guarantee that the instruction itself causes a 29–38% latency improvement in every environment. Larger repeated samples would be needed for stronger claims about tail latency.

The comparison intentionally does not assign a universal winner. Product and engineering acceptance policy should decide how to trade reliability, latency, cost, and user experience.

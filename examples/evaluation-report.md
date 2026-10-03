# Evaluation Report

## Executive summary

- **Observed pass rate:** 100.0% (35/35 live trials)
- **Cases:** 7
- **Trials per case:** 5
- **Failed trials:** 0
- **Agent latency:** mean 3.020 s, p50 2.657 s, p95 5.328 s
- **Agent tokens:** 1,069.7 mean tokens per measured trial
- **Agent estimated cost:** $0.00012621 mean per measured trial
- **Agent cost per successful trial:** $0.00012621

## Source

[Repeated-Trial Benchmark #1](https://github.com/juanestebanj/tool-using-agent-evals/actions/runs/37161041711) · commit `22675417b25b8045c8349988186da94fe982128e`

## Per-case reliability and agent performance

| Case | Passed | Observed pass rate | Mean latency | p50 | p95 | Mean tokens | Mean estimated cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| duplicate-charge | 5/5 | 100.0% | 4.884 s | 3.115 s | 8.843 s | 1,267.2 | $0.00015424 |
| single-charge | 5/5 | 100.0% | 3.111 s | 2.651 s | 4.331 s | 1,181.0 | $0.00013650 |
| failed-payment | 5/5 | 100.0% | 2.878 s | 2.738 s | 3.554 s | 1,177.2 | $0.00013620 |
| missing-invoice-id | 5/5 | 100.0% | 1.615 s | 1.537 s | 1.969 s | 530.2 | $0.00006790 |
| unknown-invoice | 5/5 | 100.0% | 3.376 s | 3.020 s | 4.782 s | 1,110.4 | $0.00013520 |
| invoice-due-date | 5/5 | 100.0% | 2.698 s | 2.549 s | 3.316 s | 1,126.0 | $0.00012940 |
| customer-status | 5/5 | 100.0% | 2.576 s | 2.426 s | 2.995 s | 1,096.0 | $0.00012400 |

## Evaluation overhead

The semantic judge is evaluation infrastructure, not part of the production-like agent serving cost. It is therefore reported separately.

- **Judge latency:** mean 2.341 s, p50 1.975 s, p95 4.687 s
- **Judge tokens:** 740.7 mean tokens per measured trial
- **Judge estimated cost:** $0.00013018 mean per measured trial
- **Total agent cost:** $0.00441720
- **Total judge cost:** $0.00455630
- **Total benchmark estimated cost:** $0.00897350
- **Combined measured agent + judge time:** 187.630 s

## Failed-trial analysis

No failed trials were observed in this benchmark run.

## Methodology

Each live trial is graded on exact trajectory properties such as required and forbidden tools, tool arguments, and tool ordering. A separate structured LLM-as-judge evaluates semantic outcome quality. Runtime, token usage, and estimated cost are captured for both the evaluated agent and the judge.

The benchmark repeats the same fixed cases because model behavior is probabilistic. The observed pass rate describes this benchmark run; it is not a claim of perfect production reliability.

Latency percentiles are most informative with larger samples. Overall p50/p95 use 35 agent observations here. Per-case percentile estimates use only 5 observations and should be treated as descriptive when that sample is small.

Estimated costs use the pricing table dated `2026-10-01` and are not billing records.

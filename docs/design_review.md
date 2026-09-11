# Design review from the 9.5/10 reference project

## What makes the reference effective

1. **Clear user journey.** The app explains what it does, what the user should adjust and how to interpret each output.
2. **Progressive disclosure.** Summary metrics come first; detailed company analysis, clustering and methodology appear later in separate tabs.
3. **Modular pipeline.** Loading, feature engineering, screening, clustering and reporting are separated into focused modules.
4. **Visible process.** A stage table shows how data move through the analytical workflow.
5. **Interactive exploration.** Users can change assumptions and inspect individual entities instead of only reading static charts.
6. **Practical hand-off.** Outputs, tests, logs and deployment configuration make the project feel complete.

## What should not be copied directly

- The stock-specific scoring, filters and portfolio selection do not fit a macroeconomic comparison.
- AI commentary is not needed when the assignment requires evidence grounded in the submitted dataset.
- A single overall score would hide the distinction between recovery, inflation, debt and external-balance trade-offs.
- Hard-coded macro commentary would weaken reproducibility.

## Design decisions applied to the IMF project

| Reference principle | IMF implementation |
|---|---|
| Start with the outcome | Executive overview opens with coverage, strongest and weakest recovery gaps, and three evidence cards. |
| Guide the user | Sidebar contains the research question, reading order and methodological warning. |
| Enable drill-down | Country lens supports indicator and country comparison over time. |
| Show analytical trade-offs | Separate recovery-versus-inflation and recovery-versus-debt views. |
| Make methods visible | Five-stage pipeline, model comparison, coverage heatmap and outlier table. |
| Support reproducibility | Download buttons, raw XML retention, metadata and exact SDMX query. |
| Avoid overclaiming | Alternative explanations and limitations remain attached to every candidate story. |

## Resulting dashboard narrative

```text
Research question
→ executive findings
→ country-level evidence
→ recovery/cost trade-offs
→ clusters and candidate stories
→ methodology, coverage and provenance
```

This structure borrows the reference project's communication discipline without copying its domain-specific scoring logic or conclusions.

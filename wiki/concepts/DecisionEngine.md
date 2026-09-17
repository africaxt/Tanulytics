---
type: concept
name: Decision Engine
aliases: [Human-Computer Integrative UI]
layer: Decision
framework: TraderChit Timeline
source_count: 1
sources: [raw/reports/TraderChit-by-Tanulytics-v2.pdf]
updated: 2026-06-28
tags: [decision-engine, ui, human-in-loop]
---

# Decision Engine

## Summary
The Decision Engine is the human-computer interface layer in the TraderChit timeline — the checkpoint between live data / signal generation and actual execution. It surfaces [[LearnAI]] outputs for human review before [[XeQT]] routes orders.

## Position in the timeline

```
Historical Data → Strategy Modeling → Live Data → Decision Engine → Execution → Repeat
```

## Purpose
Prevents fully autonomous execution — a human reviews the Target Portfolio proposed by LearnAI before XeQT acts on it. This is the "human in the loop" control point.

## Open questions
- Is this a standalone dashboard or integrated into an existing tool (Airtable, Notion, custom UI)?
- What override capabilities does it expose — reject, modify, or approve individual orders?
- Does it log human decisions for post-trade analysis and model feedback?

## Sources

| File | Date | Key takeaway |
|---|---|---|
| [[TraderChit-by-Tanulytics-v2.pdf]] | 2026-06-28 | Identified in the operational timeline between Live Data and Execution |

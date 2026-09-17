---
type: concept
name: GCP Infrastructure
aliases: [Google Cloud Platform, GCP]
layer: Infrastructure
source_count: 1
sources: [raw/reports/TraderChit-by-Tanulytics-v2.pdf]
updated: 2026-06-28
tags: [gcp, cloud, infrastructure]
---

# GCP Infrastructure

## Summary
Both [[LearnAI]] and [[XeQT]] run on Google Cloud Platform. GCP provides the compute and data layer underlying the full TraderChit stack.

## Components hosted
- LearnAI: Forecasting Algorithm training and inference, Portfolio Optimizer
- XeQT: Trading Algorithm, order management
- Historical Data store (shared between LearnAI and XeQT)

## Open questions
- Which GCP services are used — GKE (Kubernetes), Cloud Run, Compute Engine, BigQuery?
- Where does the Historical Data store live — BigQuery, Cloud SQL, GCS?
- Is there a failover or DR setup?
- How does the local IBKR TWS (macOS) connect to the GCP-hosted XeQT?

## Sources

| File | Date | Key takeaway |
|---|---|---|
| [[TraderChit-by-Tanulytics-v2.pdf]] | 2026-06-28 | GCP logo on computing infrastructure diagram; both LearnAI and XeQT hosted there |

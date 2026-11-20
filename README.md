<img alt="image" src="https://github.com/user-attachments/assets/12d3e0e1-f147-43b7-87d8-4c5baac30fe2" />

<p align="center">
  <b></b>
</p>
<h1 align="center">AI Verify Evals Toolkit</h1>
<p align="center">
  A dashboard-first safety testing suite to benchmark LLM applications, built by the <a href="https://aiverifyfoundation.sg/">AI Verify Foundation</a> and <a href="https://www.imda.gov.sg/">IMDA</a>.
</p>
<p align="center">
  <a href="https://github.com/aiverify-foundation/aiverify-evals-toolkit/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License: Apache 2.0"></a>
  <img src="https://img.shields.io/badge/python-3.12-blue.svg" alt="Python 3.12">
  <a href="https://github.com/aiverify-foundation/aiverify-evals-toolkit/releases"><img src="https://img.shields.io/github/v/release/aiverify-foundation/moonshot-cicd" alt="Latest release"></a>
  <a href="https://github.com/aiverify-foundation/aiverify-evals-toolkit/wiki"><img src="https://img.shields.io/badge/docs-wiki-informational" alt="Docs"></a>
</p>
<!--
  TODO(highest priority): replace this comment with a screenshot or short GIF of the
  human-in-the-loop review dashboard — this is the flagship product's primary surface
  and currently has zero visual representation anywhere in the repo or wiki. This one
  image will do more to convert a non-technical visitor than any paragraph below it.
-->
 
---
 
## What's in this repo
 
This repository contains **three products** built on a shared evaluation engine, aimed at three different user personas involved in benchmark testing of LLM models and applications. Find yours:
 
<table>
<tr>
<td width="34%" valign="top">

### AI Verify Evals Toolkit

**For: product managers, domain experts, risk/business reviewers — no coding required**

Run benchmark tests through a guided, step-by-step workflow. Review flagged results, and override erroneous automated verdicts to generate high-quality testing reports. Confidence intervals tell you how much to trust a result, not just what the score was.
 
**[→ Start here](https://github.com/aiverify-foundation/aiverify-evals-toolkit/wiki/AI-Verify-Evals-Toolkit-User-Guide)**
 
</td>
<td width="33%" valign="top">
  
### Moonshot CI/CD

**For: developers integrating safety testing into a pipeline**
 
The CLI and automation engine underneath the toolkit. Run benchmark + red-team suites as a pipeline step, gate merges on results, and store output natively in S3. Ships with a GitHub Actions example and an AWS CodeBuild CloudFormation template.
 
**[→ CI/CD quick start](https://github.com/aiverify-foundation/aiverify-evals-toolkit/wiki/Onboarding-Guide-for-CI-CD-Deployment)**
 
</td>
<td width="33%" valign="top">

### Process Checks

**For: governance and compliance teams**
 
A web app that maps test evidence from this toolkit against 11 internationally recognized AI governance principles for audit and regulatory review.
 
**[→ Process Checks guide](https://github.com/aiverify-foundation/aiverify-evals-toolkit/wiki/Process-Checks-Onboarding-Guide)**
 
</td>
</tr>
</table>


## Why teams use it
 - **Built-in benchmarks in three risk areas aligned to IMDA's Starter Kit** for LLM-based app testing: hallucination, undesirable content and adversarial vulnerabilities, including Singapore Undesirable Content and Singapore Factuality.
- **Automate at scale while retaining human oversight.** LLM-as-a-judge accelerates evaluation, while human reviewers can inspect, annotate, and override erroneous verdict. Every intervention is captured in an auditable trail, ensuring transparency and accountability.
- **Confidence intervals, not just a single number.** LLM outputs vary run to run. Results are reported with statistical confidence so a risk estimate carries a stated margin of uncertainty.
- **Extensible** — bring your own connectors, datasets, evaluation metrics without being limited to the built-in test bundles.
## Quick start with Docker (AI Verify Evals Toolkit)
```bash
docker run --detach --name aiverify-evals-toolkit --platform linux/amd64 -p 8000:8000 -v moonshot-cicd-data-volume:/var/lib/moonshot -e MOONSHOT_DB_PATH=/var/lib/moonshot/moonshot.db -e MOONSHOT_BENCHMARK_RESULTS_DIR=/var/lib/moonshot/results ghcr.io/aiverify-foundation/aiverify-evals-toolkit:latest moonshot-web
```
Lood the homepage via `localhost:8000`

## Documentation, by role
 
| If you are a... | Start here |
|---|---|
| **Business/product/risk reviewer** running a benchmark test and analyzing qualitative and quantitive insights |[Installation Guide](https://github.com/aiverify-foundation/aiverify-evals-toolkit/wiki/AI-Verify-Evals-Toolkit-Installation-Guide) · [User Guide](https://github.com/aiverify-foundation/aiverify-evals-toolkit/wiki/AI-Verify-Evals-Toolkit-User-Guide) |
| **Developer** wiring this into CI/CD pipelines| [Onboarding Guide for CI/CD Deployment](https://github.com/aiverify-foundation/aiverify-evals-toolkit/wiki/Onboarding-Guide-for-CI-CD-Deployment) |
| **Test developer** building custom tests | [Create Custom Moonshot Tests](https://github.com/aiverify-foundation/aiverify-evals-toolkit/wiki/Create-Custom-Moonshot-Tests) · [Custom Evaluation Metrics](https://github.com/aiverify-foundation/aiverify-evals-toolkit/wiki/Create-Custom-Evaluation-Metrics) · [Custom Connectors](https://github.com/aiverify-foundation/aiverify-evals-toolkit/wiki/Create-Custom-Connectors) |
| **Governance/compliance** consuming results as evidence | [Process Checks Quick Start Guide](https://github.com/aiverify-foundation/aiverify-evals-toolkit/wiki/Process-Checks-Quick-Start-Guide) |- **Comprehensive Test Result** in the widely-accepted `.json` format for easy read/write. Moonshot's result files are also compatible with the [AI Verify Testing Framework](https://aiverifyfoundation.sg/what-is-ai-verify/) and can be used to generate a business-ready summary report for internal compliance.

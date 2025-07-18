<div align="center">

![image](https://github.com/user-attachments/assets/ed578918-e26a-4ad6-9d33-307712127ce5)

**Version 1.1.0**

A simple and modular tool to evaluate any LLM-based AI applications.

[![Python 3.12](https://img.shields.io/badge/python-3.12-green)](https://www.python.org/downloads/release/python-3120/)


</div>

# ANNOUNCING PROJECT MOONSHOT (GA)

We are thrilled to announce the general availability version of Project Moonshot, a transformative update that redefines validation and governance of LLM-based AI applications, setting a new standard for the industry. Packed with groundbreaking enhancements, this powerful release delivers game-changing upgrades -- unlocking unmatched flexibility, efficiency, and scalability for your AI workflows. Most importantly, this version is designed for you to operationalize in your existing environment as seamlessly as possible.

We’re also excited to introduce the Process Checks (GenAI) web application, a dedicated tool aligned with the [AI Verify Testing Framework](https://aiverifyfoundation.sg/what-is-ai-verify/) to help companies assess the responsible implementation of their LLM-based AI applications against 11 internationally recognised AI governance principles.

Available as a standalone Docker image, it complements Project Moonshot’s core capabilities in technical testing, while preserving the lean, modular design of both solutions.

<br/>

## 🎯 Introduction

Developed and launched by the [Infocomm Media Development Authority](https://www.imda.gov.sg/resources/press-releases-factsheets-and-speeches/press-releases/2024/sg-launches-project-moonshot), [Moonshot](https://aiverifyfoundation.sg/project-moonshot/) is a powerful AI safety evaluation tool designed to seamlessly integrate into CI/CD pipelines, automate safety testing, and ensure the reliability of LLM-based AI Applications. 

</br>

## 🚀 Why Moonshot

In the rapidly evolving landscape of Generative AI, ensuring the safety, reliability, and performance of LLM applications is paramount. Moonshot addresses this critical need by providing a unified platform for:
- **Benchmark Tests:** Systematically test LLM-based Applications across critical trust & safety risks using a wide array of open-source benchmark datasets and metrics, including guided workflows to implement **IMDA's Starter Kit for LLM-based App Testing**.
- **Red Team Attacks:** Proactively identify vulnerabilities and potential misuse scenarios in your LLM applications through streamlined adversarial prompting.

</br>

## 🤖 Benefits of Integrating Moonshot into your CI/CD

- **Automation Testing:** Automate various AI safety testing whenever a new model or update is deployed 
- **Security & Compliance:** Detect potential AI risks and ensure compliance with AI governance policies before deployment, while generating logs and reports for governance and audit  
- **Streamlined Deployment:** Reducing bottlenecks and human intervention by integrating on-demand & scheduled AI safety checks directly into CI/CD 
- **Scalability, Cloud-Readiness & Extensibility:** Run multiple evaluations at scale across different cloud services and easily add new tests as AI regulations evolve 
- **Flexibility & Customizability:** Modular and plugin-based design allows dynamic running of selected tests based on governance policies while keeping the base image lightweight 
- **Cost & Resource Efficiency:** CI/CD optimization techniques like caching and parallel execution reduce compute, storage and operation cost 
- **Competitive Advantage & Business Benefits:** Automated AI safety testing allows for faster time-to-market, improves developer productivity with reduced manual safety testing, and ensures reliability with a better user experience in production

<br/>

## 🔑 Key Features

- **Benchmark Tests** that align with the four risk areas (i.e., _Hallucination_, _Undesirable Content_, _Data Disclosure_, and _Vulnerability to Adversarial Prompts_) as outlined in the [LLM Starter Kit for Safety Testing of LLM-Based Applications](https://www.imda.gov.sg/-/media/imda/files/about/emerging-tech-and-research/artificial-intelligence/large-language-model-starter-kit.pdf) recently released by IMDA. To understand more about the tests available, you can check out the `Test Methodology` section [here](https://github.com/aiverify-foundation/moonshot-cicd/wiki).
- **Powerful Automated Red Teaming Agents** that are easily customizable to your application use case. To understand more about customizing the Red Teaming Agents for your application use case, you can check out [this guide](https://github.com/aiverify-foundation/moonshot-cicd/wiki/Moonshot-Configurations).
- **Comprehensive Test Result** in the widely-accepted `.json` format for easy read/write. Moonshot's result files are also compatible with the [AI Verify Testing Framework](https://aiverifyfoundation.sg/what-is-ai-verify/) and can be used to generate a business-ready summary report for internal compliance.
- **Fully Containerized** as a Docker Image for easy download and deployment into your CI/CD pipelines or MLOps workflow. To understand how you can deploy Moonshot into your pipelines, you can check out [this guide](https://github.com/aiverify-foundation/moonshot-cicd/wiki/Onboarding-Guide-for-CI-CD-Deployment).
- **Native S3 Support** for easy read/write from your buckets.
- **Streamlined Experience** to run any combination of tests with just a **_single_** `moonshot run` command. To understand how you can use a simple command to run tests in Moonshot, you can check out [this guide](https://github.com/aiverify-foundation/moonshot-cicd/wiki/Running-Moonshot-Tests).
- **Extensible & Modular Design** for easy extension and integration with your LLM-based AI applications, benchmarks, and attack techniques. To understand how you can run Moonshot tests on your LLM-based AI applications, you can check out [this guide](https://github.com/aiverify-foundation/moonshot-cicd/wiki/Create-Custom-Connectors).

</br>

***
# Getting Started

Before jumping straight into the technical guides, below are some user personas that we think Moonshot will be helpful towards. Do take a moment to consider which user persona you belong to!

Alternatively, you can go straight to our [guides here](https://github.com/aiverify-foundation/moonshot-cicd/wiki) to get started!

<br/>

## What is your User Persona?
### 🤖 CI/CD Developer
If you are a CI/CD developer tasked to run safety tests on your LLM-based AI applications as part of your CI/CD workflow before production, you've come to the right place!
- Check out this [deployment guide](https://github.com/aiverify-foundation/moonshot-cicd/wiki/Onboarding-Guide-for-CI-CD-Deployment) to understand how you can easily deploy Moonshot in any CI/CD pipelines.
- For organizations using **_AWS CodeBuild_**, you can check out this [guide](https://github.com/aiverify-foundation/moonshot-cicd/wiki/Onboarding-Guide-for-AWS-CodeBuild-Deployment) instead.
    - If you are interested in contributing guides for other CI/CD platforms, kindly contact our Support Team at [info@aiverify.sg](mailto:info@aiverify.sg).
- There will be certain configurations required to operationalize Moonshot in your pipeline, so be sure to check out the [configuration guide here](https://github.com/aiverify-foundation/moonshot-cicd/wiki/Moonshot-Configurations) and [user guide to run Moonshot test](https://github.com/aiverify-foundation/moonshot-cicd/wiki/Running-Moonshot-Tests).
<br/>

### 📲 Application Owner
As an Application Owner, ensuring the safety of your LLM-based AI applications for your users will be the utmost priority. But we know that choosing the right safety tests for the right application use case can be immensely challenging -- and getting it wrong carries real reputational and even financial risks!

As such, the first batch of tests we've included are meant for testing Q&A-type applications -- if your application use case is for users to input a question and the LLM to generate an output, the tests here will be right up your alley!
- For a start, check out the `Test Methodology` section in our [Wiki here](https://github.com/aiverify-foundation/moonshot-cicd/wiki) to understand the different test cases for each of the four risk areas listed below, as well as the methodology for deriving the corresponding tests:
    - [Hallucination](https://github.com/aiverify-foundation/moonshot-cicd/wiki/Hallucination-for-Q&A)
    - [Undesirable Content](https://github.com/aiverify-foundation/moonshot-cicd/wiki/Undesirable-Content-for-Q&A)
    - [Data Disclosure](https://github.com/aiverify-foundation/moonshot-cicd/wiki/Data-Disclosure-for-Q&A)
    - [Vulnerability to Adversarial Prompts](https://github.com/aiverify-foundation/moonshot-cicd/wiki/Security-for-Q&A)
- You can also check out this [developer guide](https://github.com/aiverify-foundation/moonshot-cicd/wiki/Local-Repo-Setup) to understand how you can quickly `git clone` our repository and test out the tool!
- We've made it simple for you to use Moonshot and configure the tests to fit your use case:
    - To connect to your application endpoint, you can check out this [create custom endpoint guide](https://github.com/aiverify-foundation/moonshot-cicd/wiki/Create-Custom-Connectors).
    - To configure your tests, you can check out this [configuration guide](https://github.com/aiverify-foundation/moonshot-cicd/wiki/Moonshot-Configurations).
    - To run the tests, you can check out this [user guide](https://github.com/aiverify-foundation/moonshot-cicd/wiki/Running-Moonshot-Tests).
<br/>

### 🧑🏻‍🔬 Test Developer
Are you an AI practitioner tasked with developing tests specific to the application use case in your organization? We've created the following to assist you:
- [Expert Guide](https://github.com/aiverify-foundation/moonshot-cicd/wiki/Create-Custom-Moonshot-Tests) to develop your own Moonshot-compatible custom benchmark tests and red teaming agents.
- Every test requires proper evaluation to be effective, so be sure to check out this [guide](https://github.com/aiverify-foundation/moonshot-cicd/wiki/Create-Custom-Evaluation-Metrics).
- Other guides that you may find helpful:
    - To connect to your application endpoint, you can check out this [create custom endpoint guide](https://github.com/aiverify-foundation/moonshot-cicd/wiki/Create-Custom-Connectors).
    - To configure your tests, you can check out this [configuration guide](https://github.com/aiverify-foundation/moonshot-cicd/wiki/Moonshot-Configurations).
    - To run the tests, you can check out this [user guide](https://github.com/aiverify-foundation/moonshot-cicd/wiki/Running-Moonshot-Tests).
<br/>

### 🧑🏻‍🔬 AI Compliance
For folks from the audit or internal compliance team, you are not left out! We have also developed a web-based application that is aligned with the AI Verify Testing Framework -- Process Checks for Generative AI. This application enables you to assess the responsible implementation of AI system against 11 internationally recognised AI governance principles and generate a summary report for audit and validation.

For more information, check out the [framework here](https://aiverifyfoundation.sg/what-is-ai-verify/).

This application is available as a separate Docker image that the compliance team can easily download and deploy on the laptop.
- To understand how you can use the Process Checks application, you can check out this [onboarding guide](https://github.com/aiverify-foundation/moonshot-cicd/wiki/Process-Checks-Onboarding-Guide).
- Alternatively, you can download the [Quick Start Guide here](https://github.com/aiverify-foundation/moonshot-cicd/wiki/Process-Checks-Quick-Start-Guide) to get yourself up and running.

</br>

***
## 🤝 Contribution

Moonshot is an open-source project, and we welcome contributions from the community! Whether fixing a bug, adding a new feature, improving documentation, or suggesting an enhancement, your efforts are highly valued.

If you are interested to contribute, kindly contact our Support Team at [info@aiverify.sg](mailto:info@aiverify.sg).

</br>

## ✨ Project Status

This is the generally available version of Project Moonshot. We are actively developing new features, improving existing ones, and enhancing stability. We encourage you to try it out and provide feedback to [info@aiverify.sg](mailto:info@aiverify.sg).

</br>

## 📜 License

Moonshot is released under the [Apache Software License 2.0](https://www.apache.org/licenses/LICENSE-2.0.txt)

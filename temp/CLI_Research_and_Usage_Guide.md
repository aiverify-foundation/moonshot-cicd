# Moonshot CLI Research and Usage Guide

## Overview
This document provides a comprehensive analysis of the `cli()` function in `moonshot_core/src/entrypoints/cli/cli.py` and various methods to run the Moonshot application.

## CLI Function Analysis

### What `cli()` Does

The `cli()` function is the main entry point for the Moonshot command-line interface. Here's what it does:

1. **Click Group Definition**: It's defined as a Click group with `@click.group(invoke_without_command=True)`
2. **Welcome Display**: When no subcommand is provided, it displays:
   - Moonshot ASCII logo
   - Project metadata (name, version, author, license, description)
   - "Running application..." message
3. **Configuration Loading**: Initializes `AppConfig()` to load application configuration
4. **Command Registration**: Registers subcommands like `run`

### CLI Structure

```python
@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    # Main CLI group function
    if ctx.invoked_subcommand is None:
        # Show welcome page
    AppConfig()
    pass
```

### Available Commands

#### 1. Main Command (No Arguments)
- **Usage**: `moonshot` or `python -m moonshot_core`
- **Function**: Displays welcome screen and project information
- **Output**: ASCII logo + metadata

#### 2. Run Command
- **Usage**: `moonshot run <run_id> <test_config_id> <connector>`
- **Function**: Executes test runs with specified parameters
- **Parameters**:
  - `run_id`: Unique identifier for the test run
  - `test_config_id`: ID of the test configuration to run
  - `connector`: Connector configuration name

### Available Test Configurations

Based on `data/test_configs/tests.yaml`, the following test configurations are available:

#### Comprehensive Test Suites
- **qa-tests**: Complete test suite with 9 benchmarks and 3 red team attacks

#### Individual Test Configurations
- **prompt_injection_jailbreak**: Tests jailbreak prompt injection resistance
- **prompt_injection_obfuscation**: Tests obfuscated prompt injection resistance
- **prompt_injection_payload_splitting**: Tests payload splitting techniques
- **prompt_injection_role_playing**: Tests role-playing prompt injection
- **sensitive_data_disclosure_general**: Tests general sensitive data disclosure
- **brand_reputation_jailbreakbench**: Brand reputation tests (jailbreakbench)
- **brand_reputation_harmbench**: Brand reputation tests (harmbench)
- **brand_reputation_winobias_variation1**: Bias testing (winobias)
- **brand_reputation_bbq**: Bias testing (bbq)
- **hallucination**: Hallucination attack module testing
- **sensitive_data_disclosure**: Sensitive data disclosure attack module
- **system_prompt_leakage**: System prompt leakage testing
- **sample_test**: Sample test configuration

### Available Connectors

Based on `moonshot_config.yaml`, the following connectors are configured:

- **my-gpt-4o**: OpenAI GPT-4o model
- **my-gpt-4o-mini**: OpenAI GPT-4o-mini model
- **my-gpt-o1**: OpenAI o1 model
- **my-gpt-o1-mini**: OpenAI o1-mini model
- **my-aws-bedrock-conn**: AWS Bedrock with Claude 3 Haiku
- **my-aws-sagemaker-conn**: AWS SageMaker with GPT-4o-mini
- **my-rag-openai-adapter**: LangChain OpenAI adapter
- **sample-anthropic-adapter**: Anthropic Claude Sonnet 4

## How to Run the CLI

### Method 1: Using Poetry (Recommended)

```bash
# Navigate to the moonshot_core directory
cd /Users/kokbaisheng/code/moonshot-cicd/moonshot_core

# Install dependencies (first time only)
poetry install

# Run the main CLI (welcome screen)
poetry run python -m moonshot_core

# Run with the Poetry script
poetry run moonshot

# Run a specific test
poetry run moonshot run my-run-001 qa-tests my-gpt-4o
```

### Method 2: Direct Python Execution

```bash
# Navigate to the moonshot_core directory
cd /Users/kokbaisheng/code/moonshot-cicd/moonshot_core

# Run the main module
python -m moonshot_core

# Run the CLI file directly
python src/entrypoints/cli/cli.py

# Run a specific test (requires proper PYTHONPATH)
PYTHONPATH=src python -m entrypoints.cli.cli run my-run-001 qa-tests my-gpt-4o
```

### Method 3: Using the Entry Point Script

```bash
# After installing with poetry
cd /Users/kokbaisheng/code/moonshot-cicd/moonshot_core
poetry install

# Use the installed script
moonshot
moonshot run my-run-001 qa-tests my-gpt-4o
```

### Method 4: Docker Execution

```bash
# Build the Docker image
docker build -t moonshot-cicd .

# Run the container
docker run -it moonshot-cicd

# Run with specific test
docker run -it moonshot-cicd moonshot run my-run-001 qa-tests my-gpt-4o
```

## Example Usage Commands

### Basic Welcome Screen
```bash
poetry run moonshot
```

### Run Complete QA Test Suite
```bash
poetry run moonshot run qa-test-run-001 qa-tests my-gpt-4o
```

### Run Individual Tests
```bash
# Test prompt injection resistance
poetry run moonshot run prompt-test-001 prompt_injection_jailbreak my-gpt-4o

# Test sensitive data disclosure
poetry run moonshot run sensitive-test-001 sensitive_data_disclosure my-gpt-4o

# Test hallucination
poetry run moonshot run hallucination-test-001 hallucination my-gpt-4o
```

### Run with Different Connectors
```bash
# Using Anthropic Claude
poetry run moonshot run claude-test-001 qa-tests sample-anthropic-adapter

# Using AWS Bedrock
poetry run moonshot run bedrock-test-001 qa-tests my-aws-bedrock-conn
```

## Configuration Requirements

### Environment Variables
- **OpenAI API**: Set `OPENAI_API_KEY` environment variable
- **Anthropic API**: Set `ANTHROPIC_API_KEY` environment variable
- **AWS**: Configure AWS credentials for Bedrock/SageMaker

### Configuration Files
- **Main Config**: `moonshot_config.yaml` - Contains connector and metric configurations
- **Test Configs**: `data/test_configs/tests.yaml` - Contains test definitions
- **Datasets**: `data/datasets/` - Contains test datasets

## Progress Tracking

The CLI includes a sophisticated progress tracking system:

- **MoonshotProgressBar**: Custom progress bar with spinner, completion percentage, and elapsed time
- **ProgressManager**: Manages progress state and updates
- **Rich Integration**: Uses Rich library for beautiful terminal output

## Error Handling

The CLI includes comprehensive error handling:
- File existence checks for run IDs
- Configuration validation
- API error handling
- Progress tracking errors

## Output and Results

- **Results**: Stored in JSON format in the results directory
- **Logging**: Rich-formatted logging with different levels
- **Progress**: Real-time progress updates with visual indicators

## Troubleshooting

### Common Issues
1. **Missing Dependencies**: Run `poetry install`
2. **API Keys**: Ensure environment variables are set
3. **File Paths**: Ensure you're in the correct directory
4. **Python Path**: Use `PYTHONPATH=src` for direct Python execution

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
poetry run moonshot run my-test-001 qa-tests my-gpt-4o
```

## Architecture Overview

The CLI follows a clean architecture pattern:
- **Entry Points**: CLI interface (`cli.py`)
- **Adapters**: API adapter for test execution
- **Domain Services**: Task management, configuration loading
- **Ports**: Abstract interfaces for different components
- **Entities**: Data models for configurations and results

This modular design allows for easy extension and testing of individual components.

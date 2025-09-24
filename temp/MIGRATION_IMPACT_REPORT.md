# Migration Impact Report: Root → moonshot_core

## Overview
Several files and directories have been moved from the root folder to the `moonshot_core` subfolder. This migration impacts various actions, scripts, and references throughout the project. This document explains what actions have been broken by this move and how to fix them.

---

## What Was Moved?
- Most backend code, configuration files, and scripts (e.g., `Dockerfile`, `pyproject.toml`, `poetry.lock`, `pytest.ini`, `run_coverage.sh`, and the `data/`, `src/`, `tests/` folders) are now under `moonshot_core/`.

## Broken Actions
### 1. Docker Builds
**Old:**
```sh
docker build -t moonshot-cicd -f Dockerfile .
```
**New:**
```sh
docker build -t moonshot-cicd -f moonshot_core/Dockerfile moonshot_core
```
**Fix:** Update CI/CD workflows and local scripts to reference the new Dockerfile location and context.

fixed

### 2. Python Scripts & Entry Points
**Old:**
```sh
python src/...
```
**New:**
```sh
python moonshot_core/src/...
```
**Fix:** Update all script paths and entry points to include `moonshot_core/`.

### 3. Poetry & Dependency Management
**Old:**
```sh
poetry install
```
**New:**
```sh
cd moonshot_core
poetry install
```
**Fix:** Run poetry commands inside the `moonshot_core` directory. Update documentation and CI steps accordingly.

### 4. Test Execution
**Old:**
```sh
pytest
```
**New:**
```sh
cd moonshot_core
pytest
```
**Fix:** Run tests from within the `moonshot_core` directory. Update test scripts and CI configs.

### 5. Coverage Scripts
**Old:**
```sh
./run_coverage.sh
```
**New:**
```sh
cd moonshot_core
./run_coverage.sh
```
**Fix:** Update references to the coverage script location.

### 6. Data & Config File References
Any code or scripts referencing files like `data/`, `moonshot_config.yaml`, etc., must now use the `moonshot_core/` prefix.

---

## How to Fix
- **Update all paths** in scripts, CI/CD workflows, and documentation to include `moonshot_core/` where relevant.
- **Change working directory** to `moonshot_core` before running backend-related commands.
- **Review imports** in Python code for any hardcoded relative paths.
- **Update Docker build context and file references** in workflows and documentation.

---

## Example Fixes
- In GitHub Actions workflows, change:
  ```yaml
  - run: docker build -t moonshot-cicd -f Dockerfile .
  ```
  to:
  ```yaml
  - run: docker build -t moonshot-cicd -f moonshot_core/Dockerfile moonshot_core
  ```
- In documentation, update instructions to:
  ```sh
  cd moonshot_core
  poetry install
  pytest
  ```

---

## Summary
Any action, script, or workflow that previously referenced files in the root must now reference them in `moonshot_core/`. Update all relevant paths and working directories to restore functionality.

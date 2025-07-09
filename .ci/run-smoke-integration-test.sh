#!/bin/bash

# Read the first input argument 
test_type=$1

if [[ "$test_type" == "smoke" ]]; then
  echo "Running Smoke Tests..."
  cd moonshot-smoke-testing/test-moonshot-v1
  pip install python-dotenv PyYAML pytest
  pytest
elif [[ "$test_type" == "integration" ]]; then
  echo "Running Integration Tests..."
  cd moonshot-integration-testing/moonshot-v1-cli-integration
  pip install python-dotenv PyYAML pytest
  pytest
elif [[ "$test_type" == "pc_smoke" ]]; then
  echo "Running Process Checks Smoke Tests..."
  cd moonshot-smoke-testing
  npm install
  cd test-moonshot-v1
  npx playwright install --with-deps
  DEBUG=pw:api npx playwright test
elif [[ "$test_type" == "pc_integration" ]]; then
  echo "Running Process Checks Integration Tests..."
  cd moonshot-integration-testing/moonshot-v1-process-checks-integration-testing
  npm install
  cd tests
  npx playwright install --with-deps
  DEBUG=pw:api npx playwright test
else
  echo "Error: Unknown test type '$test_type'. Please use 'smoke' or 'integration'."
  exit 1
fi

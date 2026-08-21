#!/bin/bash

# Set permission
# chmod +x run_coverage.sh

# Run the tests with coverage, explicitly including both source directories
echo "Running tests with coverage..."
coverage run --source=src,process_check_app -m pytest

# Generate the coverage report with missing lines
echo "Generating coverage report..."
coverage report -m

# Generate the HTML coverage report
echo "Generating HTML coverage report..."
coverage html

echo "Coverage report complete!"
echo "View HTML report at: htmlcov/index.html"
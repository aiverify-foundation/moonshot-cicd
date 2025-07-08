#!/bin/bash

# Generate summary status of pre-build checks
# Note: this script must be run using source

# Function to generate code coverage summary status
read_coverage() {
  covPct=$(jq '.totals.percent_covered' combined-cov.json)
  covPctRounded=$(printf "%.0f" "$covPct")

  # Use GitHub environment variable COVERAGE_THRESHOLD, default to 70 if not set
  threshold=${COVERAGE_THRESHOLD:-70}
  echo threshold is $threshold 

  message="Coverage percentage: $covPctRounded (Threshold: $threshold)"
  export COVERAGE_SUMMARY="$message"

  if (( covPctRounded < threshold )); then
    RED='\033[0;31m'
    echo -e "${RED}${message}"
    return 1
  else
    GREEN='\033[0;92m'
    echo -e "${GREEN}${message}"
    return 0
  fi
}


# Function to generate unit test summary status
read_test() {
  testJson=$(jq '.report.summary' combined-test-report.json)
  testPassed=$(echo "$testJson" | jq '.passed // 0')
  testFailed=$(echo "$testJson" | jq '.failed // 0')
  message="Unit tests passed: $testPassed, failed: $testFailed"
  export UNITTEST_SUMMARY="$message"
  if [ "$testPassed" -eq 0 ] || [ "$testFailed" -ne 0 ]; then
    RED='\033[0;31m'
    echo -e "${RED}${message}"
    return 1
  else
    GREEN='\033[0;92m'
    echo -e "${GREEN}${message}"
    return 0
  fi
}

# Function to generate code quality summary status
read_lint() {
  last_line=$(tail -n 1 "$1-flake8-report.txt")
  message="Lint errors: $last_line"
  export LINT_SUMMARY="$message"
  if [ "$last_line" -ne 0 ]; then
    RED='\033[0;31m'
    echo -e "${RED}${message}"
    return 1
  else
    GREEN='\033[0;92m'
    echo -e "${GREEN}${message}"
    return 0
  fi
}

# Function to generate dependency vulnerability summary status
read_dependency() {
  content=$(<"$1-pip-audit-count.txt")
  if [[ $content == *"No known vulnerabilities found"* ]]; then
    numVul=0
  else
    numVul=$(grep -oP 'Found \K\d+' "$1-pip-audit-count.txt")
    numVul=${numVul:-0}
  fi
  message="Dependency vulnerabilities found: $numVul"
  export DEPENDENCY_SUMMARY="$message"
  if [ "$numVul" -ne 0 ]; then
    RED='\033[0;31m'
    echo -e "${RED}${message}"
    return 1
  else
    GREEN='\033[0;92m'
    echo -e "${GREEN}${message}"
    return 0
  fi
}

# Function to generate dependency license risk summary status
read_license() {
  strongCopyleftLic=("GPL" "AGPL" "EUPL" "OSL" "CPL")
  weakCopyleftLic=("LGPL" "MPL" "CCDL" "EPL" "CC-BY-SA")
  numStrongCopyleftLic=0
  numWeakCopyleftLic=0

  if [ -f licenses-found.md ]; then
    while IFS= read -r line; do
      # Special exception for text-unidecode with Artistic License
      if [[ $line == *"text-unidecode"* && $line == *"Artistic License"* ]]; then
        ((numWeakCopyleftLic++))
        continue
      fi
      # Check for strong copyleft licenses
      foundStrongLic=false
      for lic in "${strongCopyleftLic[@]}"; do
        if [[ $line == *"$lic"* ]]; then
          ((numStrongCopyleftLic++))
          foundStrongLic=true
          break
        fi
      done

      # Skip to next line if we found a strong license
      if $foundStrongLic; then
        continue
      fi

      # Check for weak copyleft licenses
      for lic in "${weakCopyleftLic[@]}"; do
        if [[ $line == *"$lic"* ]]; then
          ((numWeakCopyleftLic++))
          break
        fi
      done
    done < licenses-found.md
  fi

  message="Strong copyleft licenses found: $numStrongCopyleftLic, Weak copyleft licenses found: $numWeakCopyleftLic"
  export LICENSE_SUMMARY="$message"
  echo "$message"

  # Return 1 if strong copyleft licenses are found, otherwise return 0
  if [ "$numStrongCopyleftLic" -ne 0 ]; then
    return 1
  else
    return 0
  fi
}

# Function to generate Hadolint summary status
read_hadolint() {
  if [ ! -f hadolint-report.json ]; then
    echo "Hadolint report not found."
    return 1
  fi
  cat hadolint-report.json
  hadolintErrors=$(jq 'length' hadolint-report.json)
  message="Docker lint issues found: $hadolintErrors"
  export HADOLINT_SUMMARY="$message"

  if [ "$hadolintErrors" -ne 0 ]; then
    RED='\033[0;31m'
    echo -e "${RED}${message}"
    return 1
  else
    GREEN='\033[0;92m'
    echo -e "${GREEN}${message}"
    return 0
  fi
}

# Main function to determine which summary to generate
gen_summary() {
  if [[ $# -eq 0 ]]; then
    echo "No summaryToGen provided"
    exit 1
  fi

  summaryToGen=$1
  module=${2:-src}

  case $summaryToGen in
    "coverage")
      read_coverage "$module"
      ;;
    "test")
      read_test "$module"
      ;;
    "lint")
      read_lint "$module"
      ;;
    "dependency")
      read_dependency "$module"
      ;;
    "license")
      read_license "$module"
      ;;
    "hadolint")
      read_hadolint "$module"
      ;;
    *)
      echo "Unknown summary type: $summaryToGen"
      exit 1
      ;;
  esac
}

# Execute the main function
gen_summary "$@"
source_dirs="${@:-src process_check_app}"

export PYTHONPATH=$(pwd)
echo "Testing source dirs: $source_dirs"

echo "#############################################################################"
echo "###                        UNIT TEST & CODE COVERAGE                      ###"
echo "#############################################################################"

test_cmd="pytest -v --durations=20"

set +e
$test_cmd --cov=${source_dirs// / --cov=} --cov-branch --html=test-report.html --json=combined-test-report.json
exit_code=$?
coverage html
coverage json --pretty-print -o combined-cov.json
set -e
if [ $exit_code -ne 0 ]; then
  exit $exit_code
fi
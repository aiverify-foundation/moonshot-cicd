source_dirs="${@:-moonshot_core process_check_app}"

export PYTHONPATH=$(pwd)
echo "Testing source dirs: $source_dirs"

echo "#############################################################################"
echo "###                        UNIT TEST & CODE COVERAGE                      ###"
echo "#############################################################################"

set +e
overall_exit_code=0

for dir in $source_dirs; do
  echo "Running tests in $dir"
  (cd $dir && pytest -v --durations=20 --cov=. --cov-branch --html=../${dir}-test-report.html --json=../${dir}-test-report.json)
  exit_code=$?
  if [ $exit_code -ne 0 ]; then
    overall_exit_code=$exit_code
  fi
done

set -e
coverage combine $(for dir in $source_dirs; do echo "$dir/.coverage"; done)
coverage html
coverage json --pretty-print -o combined-cov.json

exit $overall_exit_code
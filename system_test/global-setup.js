const { spawnSync } = require('child_process');
const path = require('path');

/**
 * Playwright global setup: seed DB rows required by model-selection E2E tests.
 * Expects the API to already be running (see run-e2e-tests.sh or CI workflow).
 */
module.exports = async function globalSetup() {
  const python = process.env.E2E_PYTHON || 'python3';
  const scriptsDir = path.join(__dirname, 'scripts');
  const env = {
    ...process.env,
    BASE_URL: process.env.BASE_URL || 'http://localhost:8000',
    PYTHONPATH: process.env.PYTHONPATH || path.join(__dirname, '..', 'moonshot_core'),
  };

  for (const scriptName of ['seed_e2e_data.py', 'seed_completed_download_run.py']) {
    const script = path.join(scriptsDir, scriptName);
    const result = spawnSync(python, [script], { env, stdio: 'inherit' });
    if (result.status !== 0) {
      throw new Error(`${scriptName} failed (exit ${result.status ?? 'unknown'})`);
    }
  }
};

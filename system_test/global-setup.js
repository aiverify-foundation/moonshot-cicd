const { spawnSync } = require('child_process');
const path = require('path');

/**
 * Playwright global setup: seed DB rows required by model-selection E2E tests.
 * Expects the API to already be running (see run-e2e-tests.sh or CI workflow).
 */
module.exports = async function globalSetup() {
  const python = process.env.E2E_PYTHON || 'python3';
  const script = path.join(__dirname, 'scripts', 'seed_e2e_data.py');
  const result = spawnSync(python, [script], {
    env: {
      ...process.env,
      BASE_URL: process.env.BASE_URL || 'http://localhost:8000',
    },
    stdio: 'inherit',
  });
  if (result.status !== 0) {
    throw new Error(`E2E data seed failed (exit ${result.status ?? 'unknown'})`);
  }
};

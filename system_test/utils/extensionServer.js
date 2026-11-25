/**
 * Isolated FastAPI instances for benchmark-extensions E2E tests.
 *
 * The shared E2E stack (scripts/run-e2e-tests.sh) runs one API on :8000 with no overlay.
 * These helpers start extra API processes with their own port, DB, results dir, log file,
 * feature-flags file and overlay directory, so each test can choose the overlay state.
 *
 * The API process is started in its own process group so benchmark worker processes
 * spawned by a run are stopped together with it.
 */
const { spawn } = require('child_process');
const fs = require('fs');
const net = require('net');
const os = require('os');
const path = require('path');

const REPO_ROOT = path.resolve(__dirname, '..', '..');
const CORE_DIR = path.join(REPO_ROOT, 'moonshot_core');
const SOURCE_FLAGS_PATH = path.join(CORE_DIR, 'data', 'feature_flags.txt');
const FLAG_NAME = 'AIVET_OCT2026_MOON807';
const STARTUP_TIMEOUT_MS = 120000;
const STOP_TIMEOUT_MS = 15000;

/** Every live instance, so a crashed test run does not leave API processes behind. */
const liveInstances = new Set();

process.on('exit', () => {
  for (const instance of liveInstances) {
    instance.killProcessGroup('SIGKILL');
  }
});

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function freePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.unref();
    server.on('error', reject);
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address();
      server.close(() => resolve(port));
    });
  });
}

/** Copy the committed feature flags and set the MOON807 gate for this instance. */
function writeFlagsFile(filePath, enabled) {
  const source = fs.readFileSync(SOURCE_FLAGS_PATH, 'utf8');
  let found = false;
  const lines = source.split('\n').map((line) => {
    if (line.startsWith(`${FLAG_NAME}=`)) {
      found = true;
      return `${FLAG_NAME}=${enabled ? 'true' : 'false'}`;
    }
    return line;
  });
  if (!found) {
    lines.push(`${FLAG_NAME}=${enabled ? 'true' : 'false'}`);
  }
  fs.writeFileSync(filePath, lines.join('\n'));
}

function pythonExecutable() {
  return process.env.E2E_PYTHON || 'python3';
}

class ExtensionApi {
  /**
   * @param {object} [options]
   * @param {boolean} [options.flagOn=true] MOON807 gate for this instance.
   * @param {string|null} [options.overlayDir=null] Overlay directory, or null for "no overlay".
   */
  constructor({ flagOn = true, overlayDir = null } = {}) {
    this.root = fs.mkdtempSync(path.join(os.tmpdir(), 'moonshot-e2e-ext-'));
    this.flagOn = flagOn;
    this.overlayDir = overlayDir;
    this.port = null;
    this.proc = null;
    this.exited = true;
    this.dbPath = path.join(this.root, 'moonshot.db');
    this.resultsDir = path.join(this.root, 'results');
    this.logPath = path.join(this.root, 'api.log');
    this.stdoutPath = path.join(this.root, 'stdout.log');
    this.flagsPath = path.join(this.root, 'feature_flags.txt');
    this.missingOverlayPath = path.join(this.root, 'no-overlay-here');
  }

  /** Where tests build the overlay for this instance (inside the instance's temp root). */
  get overlayPath() {
    return path.join(this.root, 'overlay');
  }

  get baseURL() {
    if (this.port == null) {
      throw new Error('ExtensionApi has no port yet; call start() first.');
    }
    return `http://127.0.0.1:${this.port}`;
  }

  /** Directory the API should read as the overlay. A missing path means "no overlay". */
  get overlayEnvValue() {
    return this.overlayDir || this.missingOverlayPath;
  }

  async start() {
    if (this.proc) {
      throw new Error('ExtensionApi is already running.');
    }
    if (this.port == null) {
      this.port = await freePort();
    }
    writeFlagsFile(this.flagsPath, this.flagOn);

    const env = {
      ...process.env,
      PYTHONPATH: [CORE_DIR, path.join(CORE_DIR, 'src')].join(path.delimiter),
      PYTHONUNBUFFERED: '1',
      MOONSHOT_DB_PATH: this.dbPath,
      MOONSHOT_BENCHMARK_RESULTS_DIR: this.resultsDir,
      MOONSHOT_BENCHMARK_EXTENSIONS_DIR: this.overlayEnvValue,
      MS_LOG_PATH: this.logPath,
      MS_LOG_LEVEL: 'INFO',
      AIVET_FEATURE_FLAGS_PATH: this.flagsPath,
      // The portal page is served from this instance, so its own origin must be allowed.
      MS_CORS_ORIGINS: this.baseURL,
    };
    const args = [
      '-m',
      'uvicorn',
      'src.entrypoints.api:app',
      '--host',
      '127.0.0.1',
      '--port',
      String(this.port),
      '--log-level',
      'warning',
    ];
    const stdout = fs.openSync(this.stdoutPath, 'a');
    this.proc = spawn(pythonExecutable(), args, {
      cwd: CORE_DIR,
      env,
      stdio: ['ignore', stdout, stdout],
      detached: process.platform !== 'win32',
    });
    fs.closeSync(stdout);
    this.exited = false;
    liveInstances.add(this);
    this.proc.on('exit', () => {
      this.exited = true;
    });

    const deadline = Date.now() + STARTUP_TIMEOUT_MS;
    while (Date.now() < deadline) {
      if (this.exited) {
        throw new Error(
          `Extension API exited during startup. See ${this.stdoutPath}:\n${this.stdoutTail()}`
        );
      }
      try {
        const response = await fetch(`${this.baseURL}/api/feature-flags`);
        if (response.ok) {
          return;
        }
      } catch {
        // Not listening yet.
      }
      await sleep(500);
    }
    throw new Error(`Extension API did not become ready within ${STARTUP_TIMEOUT_MS} ms.`);
  }

  killProcessGroup(signal) {
    if (!this.proc || this.exited) {
      return;
    }
    try {
      if (process.platform === 'win32') {
        this.proc.kill(signal);
      } else {
        process.kill(-this.proc.pid, signal);
      }
    } catch {
      // Already gone.
    }
  }

  async stop() {
    if (!this.proc) {
      return;
    }
    const proc = this.proc;
    this.killProcessGroup('SIGTERM');
    const deadline = Date.now() + STOP_TIMEOUT_MS;
    while (!this.exited && Date.now() < deadline) {
      await sleep(200);
    }
    if (!this.exited) {
      this.killProcessGroup('SIGKILL');
      while (!this.exited) {
        await sleep(100);
      }
    }
    this.proc = null;
    liveInstances.delete(this);
    return proc;
  }

  async restart() {
    await this.stop();
    await this.start();
  }

  /** Remove the overlay directory from disk (the next start sees "no overlay"). */
  removeOverlayDir() {
    if (this.overlayDir) {
      fs.rmSync(this.overlayDir, { recursive: true, force: true });
    }
  }

  logText() {
    return fs.existsSync(this.logPath) ? fs.readFileSync(this.logPath, 'utf8') : '';
  }

  /** Byte-length-agnostic offset into the log; use with logSince(). */
  logOffset() {
    return this.logText().length;
  }

  logSince(offset) {
    return this.logText().slice(offset);
  }

  stdoutTail(lines = 40) {
    if (!fs.existsSync(this.stdoutPath)) {
      return '(no stdout captured)';
    }
    return fs.readFileSync(this.stdoutPath, 'utf8').split('\n').slice(-lines).join('\n');
  }

  async dispose() {
    await this.stop();
    fs.rmSync(this.root, { recursive: true, force: true });
  }
}

/**
 * Start an instance, run `fn(api)`, and always stop and clean it up afterwards.
 * @template T
 * @param {ConstructorParameters<typeof ExtensionApi>[0]} options
 * @param {(api: ExtensionApi) => Promise<T>} fn
 * @returns {Promise<T>}
 */
async function withExtensionApi(options, fn) {
  const api = new ExtensionApi(options);
  try {
    await api.start();
    return await fn(api);
  } finally {
    await api.dispose();
  }
}

/**
 * The portal hardcodes http://localhost:8000 (moonshot_portal_app/lib/api.ts).
 * Redirect those requests to the instance under test so the UI talks to the right API.
 * Call before page.goto().
 * @param {import('@playwright/test').Page} page
 * @param {string} baseURL
 */
async function routePortalApiTo(page, baseURL) {
  await page.route(/^http:\/\/localhost:8000\//, (route) => {
    const target = route.request().url().replace(/^http:\/\/localhost:8000/, baseURL);
    return route.continue({ url: target });
  });
}

module.exports = {
  ExtensionApi,
  withExtensionApi,
  routePortalApiTo,
  REPO_ROOT,
  CORE_DIR,
  sleep,
};

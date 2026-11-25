/**
 * API helpers for extension-provider tests: model configs, benchmark runs and polling.
 * All URLs are absolute (`baseURL` is the isolated API instance), so these work
 * regardless of the Playwright config baseURL.
 */
const { expect } = require('@playwright/test');

/** Run statuses that mean "still working". Anything else is terminal. */
const ACTIVE_RUN_STATUSES = new Set(['pending', 'running', 'in_progress', 'not_started']);

/** Names must be unique per API instance (run names and model config names). */
let nameCounter = 0;
function uniqueName(prefix) {
  nameCounter += 1;
  return `${prefix} ${Date.now()}-${nameCounter}`;
}

async function readJson(response) {
  const text = await response.text();
  try {
    return text ? JSON.parse(text) : null;
  } catch {
    return text;
  }
}

async function getJson(request, url) {
  const response = await request.get(url);
  return { status: response.status(), body: await readJson(response) };
}

async function listBundles(request, baseURL) {
  const { status, body } = await getJson(request, `${baseURL}/api/bundles`);
  expect(status).toBe(200);
  return body.bundles || [];
}

async function bundleNames(request, baseURL) {
  return (await listBundles(request, baseURL)).map((bundle) => bundle.name);
}

async function findBundle(request, baseURL, name) {
  const bundle = (await listBundles(request, baseURL)).find((row) => row.name === name);
  if (!bundle) {
    throw new Error(`Bundle "${name}" is not listed by /api/bundles`);
  }
  return bundle;
}

async function listProviders(request, baseURL) {
  const { status, body } = await getJson(request, `${baseURL}/api/providers`);
  expect(status).toBe(200);
  return Array.isArray(body) ? body : [];
}

async function findProvider(request, baseURL, systemName) {
  return (await listProviders(request, baseURL)).find((row) => row.system_name === systemName);
}

/**
 * Create a model config for a provider (same call the E2E seed uses).
 * @returns {Promise<{ id: number, modelId: number }>}
 */
async function createModelConfig(request, baseURL, providerId, modelName) {
  const response = await request.post(`${baseURL}/api/database-model-configs`, {
    data: {
      llm_provider_id: providerId,
      model_name: modelName,
      name: uniqueName('E2E extension model'),
      savedConfigPairs: {},
    },
  });
  const body = await readJson(response);
  expect(response.status(), JSON.stringify(body)).toBeLessThan(300);
  return { id: Number(body.id), modelId: Number(body.modelId) };
}

/**
 * Start a run of one bundle against a provider. Every prompt of the bundle runs (the example
 * datasets are small, and the stub connectors answer instantly).
 * Returns the run name; use waitForRun() to get the finished row.
 */
async function startRun(request, baseURL, { bundleName, providerSystemName, runName }) {
  const bundle = await findBundle(request, baseURL, bundleName);
  const provider = await findProvider(request, baseURL, providerSystemName);
  expect(provider, `provider ${providerSystemName} is listed`).toBeTruthy();
  const model = await createModelConfig(request, baseURL, Number(provider.id), provider.defaultModel);

  const response = await request.post(`${baseURL}/api/start-benchmark-run`, {
    data: {
      bundle_names: [bundle.id],
      run_name: runName,
      llm_provider_id: Number(provider.id),
      llm_provider_model_id: model.modelId,
      llm_provider_model_config_id: model.id,
    },
  });
  const body = await readJson(response);
  expect(response.status(), JSON.stringify(body)).toBe(200);
  return runName;
}

async function findRunByName(request, baseURL, runName) {
  const { body } = await getJson(request, `${baseURL}/api/benchmark-runs`);
  const runs = Array.isArray(body) ? body : body?.runs || [];
  const matches = runs.filter((run) => run.name === runName);
  if (matches.length === 0) {
    return null;
  }
  return matches.reduce((latest, run) => (run.id > latest.id ? run : latest));
}

/**
 * Poll until the named run leaves its active statuses.
 * @returns {Promise<object>} the run row from GET /api/benchmark-runs/{id}
 */
async function waitForRun(request, baseURL, runName, timeoutMs = 240000) {
  const deadline = Date.now() + timeoutMs;
  let last = null;
  while (Date.now() < deadline) {
    const listed = await findRunByName(request, baseURL, runName);
    if (listed) {
      const { status, body } = await getJson(request, `${baseURL}/api/benchmark-runs/${listed.id}`);
      if (status === 200) {
        last = body;
        if (!ACTIVE_RUN_STATUSES.has(body.status)) {
          return body;
        }
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 2000));
  }
  throw new Error(`Run "${runName}" did not finish within ${timeoutMs} ms (last: ${last?.status})`);
}

async function runPrompts(request, baseURL, runId) {
  const { status, body } = await getJson(request, `${baseURL}/api/benchmark-runs/${runId}/prompts`);
  expect(status).toBe(200);
  return Array.isArray(body) ? body : [];
}

module.exports = {
  uniqueName,
  getJson,
  readJson,
  listBundles,
  bundleNames,
  findBundle,
  listProviders,
  findProvider,
  createModelConfig,
  startRun,
  findRunByName,
  waitForRun,
  runPrompts,
};

/**
 * Build benchmark-extensions overlay directories for E2E tests.
 *
 * The valid overlay starts from the committed example (moonshot_core/benchmark-extensions.example)
 * and adds:
 *   - the OK and error stub connectors (fixtures/extensions/adapters/connector),
 *   - a providers.json listing both stubs and the example OpenAI connector,
 *   - an extension metric config and a bundle that uses it (the example has no metrics entry, see F10).
 */
const fs = require('fs');
const path = require('path');
const { ExtensionApi, REPO_ROOT } = require('./extensionServer');

const EXAMPLE_DIR = path.join(REPO_ROOT, 'moonshot_core', 'benchmark-extensions.example');
const STUB_CONNECTOR_DIR = path.join(__dirname, '..', 'fixtures', 'extensions', 'adapters', 'connector');

const OK_SYSTEM_NAME = 'e2e_ok_connector';
const ERROR_SYSTEM_NAME = 'e2e_error_connector';
const OVERLAY_BUNDLE_NAME = 'Custom Extension Sample';
const OVERLAY_BUNDLE_ID = 'custom-extension-sample';
const METRIC_BUNDLE_NAME = 'Custom Extension Metric';
const METRIC_BUNDLE_ID = 'custom-extension-metric';
const EXTENSION_METRIC_NAME = 'extension_example_metric_adapter';

const OK_PROVIDER = {
  name: 'E2E OK Connector',
  system_name: OK_SYSTEM_NAME,
  version: 1,
  adapter_module: 'ok_connector_adapter',
  defaultModel: 'ok-model',
  modelTextboxExplanation: 'Any model name; the stub ignores it',
  defaultConfigPairs: {},
};

const ERROR_PROVIDER = {
  name: 'E2E Error Connector',
  system_name: ERROR_SYSTEM_NAME,
  version: 1,
  adapter_module: 'error_connector_adapter',
  defaultModel: 'error-model',
  modelTextboxExplanation: 'Any model name; the stub always fails',
  defaultConfigPairs: {},
};

function exampleOpenAiProvider() {
  const raw = fs.readFileSync(
    path.join(EXAMPLE_DIR, 'adapters', 'connector', 'providers.json'),
    'utf8'
  );
  return JSON.parse(raw).providers[0];
}

function defaultProviders() {
  return { providers: [OK_PROVIDER, ERROR_PROVIDER, exampleOpenAiProvider()] };
}

const BASE_CONFIG_YAML = `connectors_configurations:
  - id: benchmark-extension-openai
    connector_adapter: benchmark_extension_openai_adapter
    model: gpt-4o-mini
`;

const EXTENSION_METRIC_CONFIG_YAML = `metrics:
  - name: ${EXTENSION_METRIC_NAME}
    connector_configurations:
      connector_adapter: ok_connector_adapter
      model: ok-model
      system_prompt: ""
    params: {}
`;

const SAMPLE_BUNDLE_YAML = `${OVERLAY_BUNDLE_ID}:
  description: Example bundle seeded from benchmark-extensions.
  category: Custom
  name: ${OVERLAY_BUNDLE_NAME}
  visible: true
  tests:
    - name: Sample accuracy check
      description: Uses the built-in accuracy metric on a small custom dataset.
      type: benchmark
      dataset: custom_extension_sample
      metric:
        name: accuracy_adapter
`;

const METRIC_BUNDLE_YAML = `${METRIC_BUNDLE_ID}:
  description: Example bundle that uses the extension metric adapter.
  category: Custom
  name: ${METRIC_BUNDLE_NAME}
  visible: true
  tests:
    - name: Sample extension metric check
      description: Uses the overlay metric adapter with the OK stub connector.
      type: benchmark
      dataset: custom_extension_sample
      metric:
        name: ${EXTENSION_METRIC_NAME}
`;

function writeText(filePath, text) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, text);
}

function configYaml({ withExtensionMetric }) {
  return withExtensionMetric ? `${BASE_CONFIG_YAML}${EXTENSION_METRIC_CONFIG_YAML}` : BASE_CONFIG_YAML;
}

function sharedYaml({ withExtensionMetric }) {
  return withExtensionMetric ? `${SAMPLE_BUNDLE_YAML}${METRIC_BUNDLE_YAML}` : SAMPLE_BUNDLE_YAML;
}

/** Write (or overwrite) providers.json. `null` removes it; a string is written as-is. */
function writeProviders(dir, providers) {
  const target = path.join(dir, 'adapters', 'connector', 'providers.json');
  if (providers === null) {
    fs.rmSync(target, { force: true });
    return;
  }
  const text = typeof providers === 'string' ? providers : JSON.stringify(providers, null, 2);
  writeText(target, text);
}

/**
 * Build a valid overlay directory at `dir` (replacing anything already there).
 * @param {string} dir
 * @param {{ withExtensionMetric?: boolean, providers?: object|string|null }} [options]
 * @returns {string} dir
 */
function buildOverlay(dir, { withExtensionMetric = true, providers = defaultProviders() } = {}) {
  fs.rmSync(dir, { recursive: true, force: true });
  fs.cpSync(EXAMPLE_DIR, dir, { recursive: true });
  fs.rmSync(path.join(dir, 'README.md'), { force: true });
  fs.rmSync(path.join(dir, 'adapters', 'connector', 'README.md'), { force: true });

  writeText(path.join(dir, 'moonshot_config.yaml'), configYaml({ withExtensionMetric }));
  writeText(path.join(dir, 'test_configs', 'shared.yaml'), sharedYaml({ withExtensionMetric }));

  for (const name of fs.readdirSync(STUB_CONNECTOR_DIR)) {
    fs.copyFileSync(
      path.join(STUB_CONNECTOR_DIR, name),
      path.join(dir, 'adapters', 'connector', name)
    );
  }
  writeProviders(dir, providers);
  return dir;
}

/**
 * Overlay variants that the verification doc says are invalid as a whole.
 * Each one starts from a valid overlay and breaks one thing.
 */
const INVALID_OVERLAY_KINDS = {
  // Overlay metric name equal to a built-in metric.
  'duplicate-metric': (dir) => {
    writeText(
      path.join(dir, 'moonshot_config.yaml'),
      `${BASE_CONFIG_YAML}metrics:
  - name: accuracy_adapter
    connector_configurations:
      connector_adapter: ""
      model: ""
      system_prompt: ""
    params:
      categorise_result: False
`
    );
  },
  'malformed-config': (dir) => {
    writeText(path.join(dir, 'moonshot_config.yaml'), 'metrics: [\n');
  },
  // Bundle whose dataset is in neither datasets/ nor data/datasets/.
  'missing-dataset': (dir) => {
    writeText(
      path.join(dir, 'test_configs', 'shared.yaml'),
      SAMPLE_BUNDLE_YAML.replace('dataset: custom_extension_sample', 'dataset: e2e_missing_dataset')
    );
  },
  // Overlay bundle key equal to a built-in bundle key.
  'duplicate-bundle-key': (dir) => {
    writeText(
      path.join(dir, 'test_configs', 'shared.yaml'),
      SAMPLE_BUNDLE_YAML.replace(`${OVERLAY_BUNDLE_ID}:`, 'undesirable-content:')
    );
  },
};

/** Build a valid overlay, then apply one invalid variant. */
function buildInvalidOverlay(dir, kind) {
  const apply = INVALID_OVERLAY_KINDS[kind];
  if (!apply) {
    throw new Error(`Unknown invalid overlay kind: ${kind}`);
  }
  buildOverlay(dir, { withExtensionMetric: false });
  apply(dir);
  return dir;
}

/**
 * Start an isolated API with an overlay built inside its temp root, run `fn(api)`, then clean up.
 *
 * @param {object} options
 * @param {boolean} [options.flagOn=true] MOON807 gate.
 * @param {'valid'|'invalid'|null} [options.overlay='valid'] Overlay to build, or null for none.
 * @param {string} [options.invalidKind] Required when overlay is 'invalid'.
 * @param {object} [options.overlayOptions] Passed to buildOverlay() when overlay is 'valid'.
 * @param {(api: ExtensionApi) => void|Promise<void>} [options.prepare] Runs after the overlay is built, before start.
 * @param {(api: ExtensionApi) => Promise<T>} fn
 * @template T
 * @returns {Promise<T>}
 */
async function withOverlayApi(
  { flagOn = true, overlay = 'valid', invalidKind, overlayOptions, prepare } = {},
  fn
) {
  const api = new ExtensionApi({ flagOn });
  try {
    if (overlay === 'valid') {
      buildOverlay(api.overlayPath, overlayOptions);
      api.overlayDir = api.overlayPath;
    } else if (overlay === 'invalid') {
      buildInvalidOverlay(api.overlayPath, invalidKind);
      api.overlayDir = api.overlayPath;
    }
    if (prepare) {
      await prepare(api);
    }
    await api.start();
    return await fn(api);
  } finally {
    await api.dispose();
  }
}

module.exports = {
  withOverlayApi,
  EXAMPLE_DIR,
  OK_PROVIDER,
  ERROR_PROVIDER,
  OK_SYSTEM_NAME,
  ERROR_SYSTEM_NAME,
  OVERLAY_BUNDLE_NAME,
  OVERLAY_BUNDLE_ID,
  METRIC_BUNDLE_NAME,
  METRIC_BUNDLE_ID,
  EXTENSION_METRIC_NAME,
  defaultProviders,
  buildOverlay,
  buildInvalidOverlay,
  writeProviders,
  writeText,
  configYaml,
  sharedYaml,
  INVALID_OVERLAY_KINDS,
};

/**
 * Claims: providers.json lists extension connectors as portal providers (F9). Invalid entries are
 * skipped one by one, a malformed file gives none, the rest of the overlay stays active, and an
 * extension provider is hidden whenever the overlay is not active, keeping its row.
 */
const path = require('path');
const { test, expect } = require('@playwright/test');
const { ExtensionApi } = require('../../utils/extensionServer');
const {
  buildOverlay,
  defaultProviders,
  withOverlayApi,
  writeProviders,
  writeText,
  OK_PROVIDER,
  OK_SYSTEM_NAME,
  OVERLAY_BUNDLE_NAME,
} = require('../../utils/extensionOverlay');
const { bundleNames, createModelConfig, findProvider, listProviders } = require('../../utils/extensionRuns');

test.setTimeout(480000);

const OPENAI_EXAMPLE_SYSTEM_NAME = 'benchmark_extension_openai_adapter';

test.describe('providers.json feeds the portal provider list', () => {
  test('a valid file lists the stub and the example OpenAI connector with their JSON defaults', async ({ request }) => {
    await withOverlayApi({ flagOn: true, overlay: 'valid' }, async (api) => {
      const providers = await listProviders(request, api.baseURL);

      const ok = providers.find((row) => row.system_name === OK_SYSTEM_NAME);
      expect(ok).toBeTruthy();
      expect(ok.name).toBe(OK_PROVIDER.name);
      expect(ok.defaultModel).toBe('ok-model');

      const openai = providers.find((row) => row.system_name === OPENAI_EXAMPLE_SYSTEM_NAME);
      expect(openai).toBeTruthy();
      expect(openai.defaultModel).toBe('gpt-4o-mini');
      expect(openai.defaultConfigPairs.temperature).toBe('1.0');

      // Built-in providers are unaffected.
      expect(providers.some((row) => row.system_name === 'openai_adapter')).toBe(true);

      const details = await request.get(
        `${api.baseURL}/api/providers/by-system-name/${OK_SYSTEM_NAME}/latest-details`
      );
      expect(details.status()).toBe(200);
    });
  });

  test('a malformed providers.json gives no extension providers and the overlay bundles stay active', async ({
    request,
  }) => {
    await withOverlayApi(
      { flagOn: true, overlay: 'valid', overlayOptions: { providers: '{ not json' } },
      async (api) => {
        const providers = await listProviders(request, api.baseURL);
        expect(providers.some((row) => row.system_name === OK_SYSTEM_NAME)).toBe(false);
        expect(api.logText()).toContain('Ignoring extension providers file');
        expect(await bundleNames(request, api.baseURL)).toContain(OVERLAY_BUNDLE_NAME);
      }
    );
  });

  test('bad entries are skipped one by one while the valid entry is kept', async ({ request }) => {
    const providers = {
      providers: [
        OK_PROVIDER,
        {
          name: 'Duplicate built-in',
          system_name: 'openai_adapter',
          version: 1,
          adapter_module: 'benchmark_extension_openai_adapter',
        },
        {
          name: 'Duplicate OK',
          system_name: OK_SYSTEM_NAME,
          version: 1,
          adapter_module: 'ok_connector_adapter',
        },
        {
          name: 'Unsafe path',
          system_name: 'e2e_unsafe',
          version: 1,
          adapter_module: '../escape',
        },
      ],
    };

    await withOverlayApi({ flagOn: true, overlay: 'valid', overlayOptions: { providers } }, async (api) => {
      const listed = await listProviders(request, api.baseURL);

      const okRows = listed.filter((row) => row.system_name === OK_SYSTEM_NAME);
      expect(okRows).toHaveLength(1);
      expect(okRows[0].name).toBe(OK_PROVIDER.name);

      const builtinRows = listed.filter((row) => row.system_name === 'openai_adapter');
      expect(builtinRows).toHaveLength(1);
      expect(builtinRows[0].name).not.toBe('Duplicate built-in');

      expect(listed.some((row) => row.system_name === 'e2e_unsafe')).toBe(false);
      expect(api.logText()).toContain('Skipping extension provider #');
      expect(await bundleNames(request, api.baseURL)).toContain(OVERLAY_BUNDLE_NAME);
    });
  });

  test('without providers.json the extension connector is not a portal provider', async ({ request }) => {
    await withOverlayApi({ flagOn: true, overlay: 'valid', overlayOptions: { providers: null } }, async (api) => {
      const providers = await listProviders(request, api.baseURL);
      expect(providers.some((row) => row.system_name === OK_SYSTEM_NAME)).toBe(false);
      expect(await bundleNames(request, api.baseURL)).toContain(OVERLAY_BUNDLE_NAME);
    });
  });

  test('hidden while the overlay is not active, and back with the same row id', async ({ request }) => {
    const api = new ExtensionApi({ flagOn: true });

    // Checks the provider list, the database-configs list and latest-details together.
    const expectVisible = async (expected) => {
      const listed = (await listProviders(request, api.baseURL)).some(
        (row) => row.system_name === OK_SYSTEM_NAME
      );
      expect(listed).toBe(expected);

      const withConfigs = await request.get(`${api.baseURL}/api/providers/with-database-model-configs`);
      expect(withConfigs.status()).toBe(200);
      expect(JSON.stringify(await withConfigs.json()).includes(OK_SYSTEM_NAME)).toBe(expected);

      const details = await request.get(
        `${api.baseURL}/api/providers/by-system-name/${OK_SYSTEM_NAME}/latest-details`
      );
      if (expected) {
        expect(details.status()).toBe(200);
      } else {
        expect(details.status()).not.toBe(200);
      }
    };

    try {
      buildOverlay(api.overlayPath);
      api.overlayDir = api.overlayPath;
      await api.start();

      // A model config makes the provider appear in the database-configs list when visible.
      const okRow = await findProvider(request, api.baseURL, OK_SYSTEM_NAME);
      const rowId = okRow.id;
      await createModelConfig(request, api.baseURL, Number(rowId), OK_PROVIDER.defaultModel);
      await expectVisible(true);

      // Flag off, overlay directory still present.
      await api.stop();
      api.flagOn = false;
      await api.start();
      await expectVisible(false);

      // Flag on, overlay directory removed.
      await api.stop();
      api.flagOn = true;
      api.removeOverlayDir();
      await api.start();
      await expectVisible(false);

      // Overlay back: same row id as before.
      buildOverlay(api.overlayPath);
      await api.restart();
      expect((await findProvider(request, api.baseURL, OK_SYSTEM_NAME)).id).toBe(rowId);
      await expectVisible(true);

      // Entry removed from providers.json.
      writeProviders(
        api.overlayPath,
        { providers: defaultProviders().providers.filter((row) => row.system_name !== OK_SYSTEM_NAME) }
      );
      await api.restart();
      await expectVisible(false);

      writeProviders(api.overlayPath, defaultProviders());
      await api.restart();
      expect((await findProvider(request, api.baseURL, OK_SYSTEM_NAME)).id).toBe(rowId);
      await expectVisible(true);

      // Invalid overlay (malformed moonshot_config.yaml).
      writeText(path.join(api.overlayPath, 'moonshot_config.yaml'), 'metrics: [\n');
      await api.restart();
      await expectVisible(false);

      buildOverlay(api.overlayPath);
      await api.restart();
      expect((await findProvider(request, api.baseURL, OK_SYSTEM_NAME)).id).toBe(rowId);
      await expectVisible(true);
    } finally {
      await api.dispose();
    }
  });
});

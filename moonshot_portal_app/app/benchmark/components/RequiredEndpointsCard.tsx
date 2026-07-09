"use client"
import React, { useEffect, useMemo, useState } from 'react';
import { Card, CardContent, CardDescription, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CircleCheckBig, CircleAlert } from 'lucide-react';
import {
    Accordion,
    AccordionContent,
    AccordionItem,
    AccordionTrigger,
  } from "@/components/ui/accordion"
import EditLlmAajProviderSheet from './EditLlmAajProviderSheet';
import { useCheckedTestNames } from '../../../hooks/useTestSelection';
import { useAppSelector } from '../../../hooks/reduxHooks';
import {
  ApiError,
  Bundle,
  fetchProviderLatestDetails,
  fetchProviders,
} from '../../../lib/api';
import {
  mapLlmProviderDtoToProvider,
  resolveAajEndpointCardLabel,
} from '../../../lib/aajProviderResolution';
import type { Provider } from '../types/modelSelection';

enum ConnectionStatus {
  CONNECTED = "connected",
  NOT_CONNECTED = "not connected",
  INVALID_TOKEN = "Invalid Token"
}

/** Redux `endpointStatus` key for LLM-as-judge provider rows (DB `metric_provider_system_name`). */
export function aajEndpointStatusKey(metricProviderSystemName: string): string {
  return `aaj:${metricProviderSystemName}`;
}

/** Whether an LLM-as-judge endpoint is satisfied for display / overall status. */
export function isAajEndpointAccepted(
  status: ConnectionStatus,
  apiKeyConfigured: boolean | undefined
): boolean {
  if (status === ConnectionStatus.INVALID_TOKEN) return false;
  return status === ConnectionStatus.CONNECTED || Boolean(apiKeyConfigured);
}

export type AajEndpointRow = {
  rowKey: string;
  modelName: string;
  status: ConnectionStatus;
  tests: string[];
  systemName: string;
  providerId: string | null;
  connectDisabled: boolean;
};

function renderEndpointStatusCard(
  modelName: string,
  status: ConnectionStatus,
  tests: string[],
  onConnect: () => void,
  connectDisabled: boolean
) {
  const getBadgeClasses = (status: ConnectionStatus) => {
    switch (status) {
      case ConnectionStatus.CONNECTED:
        return "bg-green-100 text-green-800 border-green-200";
      case ConnectionStatus.NOT_CONNECTED:
        return "bg-gray-100 text-gray-800 border-gray-200";
      case ConnectionStatus.INVALID_TOKEN:
        return "bg-red-100 text-red-800 border-red-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getBorderClasses = (status: ConnectionStatus) => {
    switch (status) {
      case ConnectionStatus.CONNECTED:
        return "border-green-200";
      case ConnectionStatus.NOT_CONNECTED:
        return "border-gray-200";
      case ConnectionStatus.INVALID_TOKEN:
        return "border-red-200";
      default:
        return "border-gray-200";
    }
  };

  const firstTest = tests.length > 0 ? tests[0] : '—';

  return (
    <Card className={`border ${getBorderClasses(status)} p-2 w-80`}>
      <CardContent className="px-1 py-1">
        <div>{modelName}</div>
        
        <div className="grid grid-cols-2 gap-4 mt-4">
          <div>
            <h3 className="font-semibold text-sm text-gray-700 mb-2">Tests</h3>
            <div className="space-y-1">
              <div className="text-sm text-gray-600">{firstTest}</div>
              <div className="text-sm text-gray-500 h-5">
                {tests.length > 1 ? `+${tests.length - 1} more` : '\u00A0'}
              </div>
            </div>
          </div>
          <div>
            <h3 className="font-semibold text-sm text-gray-700 mb-2">Status</h3>
            <Badge className={getBadgeClasses(status)}>
              {status}
            </Badge>
          </div>
        </div>
        
        <div className="mt-4 flex justify-start">
          <Button size="sm" className="text-xs" onClick={onConnect} disabled={connectDisabled}>
            Connect
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function renderEndpointStatusCardsGrid(
  endpoints: AajEndpointRow[],
  onConnect: (row: AajEndpointRow) => void
) {
  return (
    <div className="max-h-[400px] overflow-y-auto">
      <div className="grid grid-cols-2 gap-4">
        {endpoints.map((endpoint) => (
          <div key={endpoint.rowKey}>
            {renderEndpointStatusCard(
              endpoint.modelName,
              endpoint.status,
              endpoint.tests,
              () => onConnect(endpoint),
              endpoint.connectDisabled
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

type AajSheetState =
  | { kind: 'closed' }
  | { kind: 'open'; providerId: string; systemName: string; statusKey: string };

export default function RequiredEndpointsCard() {
  const [isAajSheetOpen, setIsAajSheetOpen] = useState(false);
  const [sheet, setSheet] = useState<AajSheetState>({ kind: 'closed' });
  const [apiProviders, setApiProviders] = useState<Provider[]>([]);
  const [providersLoading, setProvidersLoading] = useState(true);
  const [providersError, setProvidersError] = useState<string | null>(null);
  const [apiKeyConfiguredBySystem, setApiKeyConfiguredBySystem] = useState<
    Record<string, boolean>
  >({});
  const [keysLoading, setKeysLoading] = useState(false);

  const selectedTestNames = useCheckedTestNames();
  const bundles = useAppSelector((state) => state.bundles.data) as Bundle[];
  const endpointStatuses = useAppSelector((state) => state.endpointStatus) as Record<string, string>;

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setProvidersLoading(true);
      setProvidersError(null);
      try {
        const dtos = await fetchProviders();
        if (!cancelled) {
          setApiProviders(dtos.map(mapLlmProviderDtoToProvider));
        }
      } catch (e) {
        if (!cancelled) {
          setProvidersError(e instanceof ApiError ? e.message : "Failed to load providers");
          setApiProviders([]);
        }
      } finally {
        if (!cancelled) {
          setProvidersLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const sheetProvider = useMemo((): Provider | null => {
    if (sheet.kind !== "open") return null;
    return apiProviders.find((p) => p.id === sheet.providerId) ?? null;
  }, [sheet, apiProviders]);

  const systemNamesToFetch = useMemo((): string[] => {
    const bySystem = new Map<string, Set<string>>();
    bundles.forEach((bundle) => {
      bundle.tests.forEach((test) => {
        if (!selectedTestNames.includes(test.name)) return;
        if (!test.requires_llm_aaj || !test.metric_provider_system_name?.trim()) return;
        const sn = test.metric_provider_system_name.trim();
        if (!bySystem.has(sn)) {
          bySystem.set(sn, new Set());
        }
        bySystem.get(sn)!.add(test.name);
      });
    });
    const names: string[] = [];
    for (const systemName of bySystem.keys()) {
      const provider = apiProviders.find((p) => p.system_name === systemName);
      if (provider) {
        names.push(systemName);
      }
    }
    return names.sort();
  }, [bundles, selectedTestNames, apiProviders]);

  useEffect(() => {
    if (systemNamesToFetch.length === 0) {
      setApiKeyConfiguredBySystem({});
      setKeysLoading(false);
      return;
    }
    let cancelled = false;
    setKeysLoading(true);
    void (async () => {
      const entries = await Promise.all(
        systemNamesToFetch.map(async (systemName) => {
          try {
            const details = await fetchProviderLatestDetails(systemName);
            return [systemName, Boolean(details.api_key_configured)] as const;
          } catch {
            return [systemName, false] as const;
          }
        })
      );
      if (!cancelled) {
        setApiKeyConfiguredBySystem(Object.fromEntries(entries));
        setKeysLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [systemNamesToFetch]);

  const endpoints = useMemo((): AajEndpointRow[] => {
    const bySystem = new Map<string, Set<string>>();
    bundles.forEach((bundle) => {
      bundle.tests.forEach((test) => {
        if (!selectedTestNames.includes(test.name)) return;
        if (!test.requires_llm_aaj || !test.metric_provider_system_name?.trim()) return;
        const sn = test.metric_provider_system_name.trim();
        if (!bySystem.has(sn)) {
          bySystem.set(sn, new Set());
        }
        bySystem.get(sn)!.add(test.name);
      });
    });

    const rows: AajEndpointRow[] = [];
    for (const [systemName, testSet] of bySystem) {
      const provider = apiProviders.find((p) => p.system_name === systemName);
      const statusKey = aajEndpointStatusKey(systemName);
      const storedStatus = endpointStatuses[statusKey];
      const rawStatus = storedStatus
        ? (storedStatus as ConnectionStatus)
        : ConnectionStatus.NOT_CONNECTED;
      const apiKeyConfigured = apiKeyConfiguredBySystem[systemName];
      const status = isAajEndpointAccepted(rawStatus, apiKeyConfigured)
        ? ConnectionStatus.CONNECTED
        : rawStatus;
      const tests = Array.from(testSet).sort();
      const providerMissing = !provider;
      rows.push({
        rowKey: statusKey,
        modelName: resolveAajEndpointCardLabel(systemName, apiProviders),
        status,
        tests,
        systemName,
        providerId: provider?.id ?? null,
        connectDisabled: providerMissing,
      });
    }
    rows.sort((a, b) => a.systemName.localeCompare(b.systemName));
    return rows;
  }, [bundles, selectedTestNames, apiProviders, endpointStatuses, apiKeyConfiguredBySystem]);

  const overallStatus = useMemo(() => {
    if (endpoints.length === 0) {
      return true;
    }
    if (keysLoading) {
      return false;
    }
    return endpoints.every((e) => e.status === ConnectionStatus.CONNECTED);
  }, [endpoints, keysLoading]);

  const handleConnect = (row: AajEndpointRow) => {
    if (row.connectDisabled || !row.providerId) return;
    setSheet({
      kind: 'open',
      providerId: row.providerId,
      systemName: row.systemName,
      statusKey: row.rowKey,
    });
    setIsAajSheetOpen(true);
  };

  const handleSheetOpenChange = (open: boolean) => {
    setIsAajSheetOpen(open);
    if (!open) {
      setSheet({ kind: 'closed' });
    }
  };

  const sheetOpen = sheet.kind === 'open';
  const endpointStatusKeyForSheet = sheetOpen ? sheet.statusKey : null;

  return (
    <>
      <Card className="w-3xl mt-6 py-1">
        <Accordion type="single" collapsible defaultValue="item-1">
          <AccordionItem value="item-1">
            <AccordionTrigger className="flex flex-row items-center hover:no-underline px-6 py-4">
              <div className="flex-1">
                <CardTitle data-testid="additional-card-title">Connect LLM-as-judge Models</CardTitle>
                <CardDescription data-testid="additional-card-description">
                  Configure access to LLM-as-judge providers required by your selected tests.
                </CardDescription>
              </div>
              <div className="flex items-center">
                  {overallStatus ? (
                    <CircleCheckBig className="h-5 w-5 text-green-500" data-testid="required-endpoints-status-indicator" />
                  ) : (
                    <CircleAlert className="h-5 w-5 text-red-500" data-testid="required-endpoints-status-indicator" />
                  )}
              </div>
            </AccordionTrigger>
            <AccordionContent>
              <CardContent>
                {providersError ? (
                  <p className="text-sm text-red-600" role="alert">{providersError}</p>
                ) : null}
                {providersLoading ? (
                  <div className="text-center text-gray-500 py-8">Loading providers…</div>
                ) : endpoints.length > 0 ? (
                  renderEndpointStatusCardsGrid(endpoints, handleConnect)
                ) : (
                  <div className="text-center text-gray-500 py-8">
                    No required endpoints.
                  </div>
                )}
              </CardContent>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </Card>
      
      <EditLlmAajProviderSheet
        open={isAajSheetOpen}
        onOpenChange={handleSheetOpenChange}
        provider={sheetOpen ? sheetProvider : null}
        endpointStatusKey={endpointStatusKeyForSheet}
      />
    </>
  );
}

export { ConnectionStatus };

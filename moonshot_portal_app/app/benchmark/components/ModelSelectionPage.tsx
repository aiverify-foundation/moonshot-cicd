"use client"
import React, { useCallback, useEffect, useState } from 'react';
import { Breadcrumb, BreadcrumbList, BreadcrumbItem, BreadcrumbPage, BreadcrumbSeparator } from '@/components/ui/breadcrumb';
import RequiredEndpointsCard from "./RequiredEndpointsCard";
import SampleSizeCard from "./SampleSizeCard";
import TestNameAndDescriptionCard from "./TestNameAndDescriptionCard";
import SelectAppOrModelCard from "./SelectAppOrModelCard";
import { custom_connectors, configs } from "./MockData";
import type { Provider, ModelConfig } from "../types/modelSelection";
import { useAppDispatch, useAppSelector } from "@/hooks/reduxHooks";
import {
  fetchProviders,
  fetchProviderLatestDetails,
  ApiError,
  type DatabaseModelConfigDTO,
  type LlmProviderDetailsDTO,
  type LlmProviderDTO,
} from "@/lib/api";
import { setBenchmarkRunFks, setSelectedModel } from "@/store";

function sortModelConfigRows(a: ModelConfig, b: ModelConfig): number {
  const primary = (id: string) => {
    const i = id.indexOf(":");
    return i === -1 ? parseInt(id, 10) : parseInt(id.slice(0, i), 10);
  };
  const pa = primary(a.id);
  const pb = primary(b.id);
  if (pa !== pb) return pa - pb;
  return a.name.localeCompare(b.name);
}

function mapLlmProviderDtoToProvider(dto: LlmProviderDTO): Provider {
  const pairs = dto.defaultConfigPairs ?? {};
  return {
    id: dto.id,
    name: dto.name,
    type: "provider",
    defaultModel: dto.defaultModel ?? "",
    modelTextboxExplanation: dto.modelTextboxExplanation ?? "",
    configPairs: Object.keys(pairs).map((key) => ({
      key,
      value: String(pairs[key]),
    })),
    modelToken: dto.modelToken ?? "",
    system_name: dto.system_name,
  };
}

function mapProviderDetailsToModelRows(
  providerId: string,
  details: LlmProviderDetailsDTO
): ModelConfig[] {
  const dbConfigs = details.database_model_configs ?? [];
  const modelById = new Map(details.models.map((m) => [m.id, m]));
  const rows: ModelConfig[] = [];

  for (const c of dbConfigs) {
    const mid = Number(c.modelId);
    if (!Number.isFinite(mid) || mid <= 0) continue;
    const base = modelById.get(mid);
    rows.push({
      id: `${mid}:${c.id}`,
      name: (c.name ?? "").trim() ? c.name : base?.name ?? `Model ${mid}`,
      modelname: (c.modelname ?? "").trim() ? c.modelname : base?.name ?? "",
      provider: providerId,
      modelConfigId: String(c.id),
      savedConfigPairs: c.savedConfigPairs ?? {},
    });
  }

  // Once a provider has saved configs, keep the picker focused on those config rows.
  if (dbConfigs.length === 0) {
    for (const m of details.models) {
      rows.push({
        id: String(m.id),
        name: m.name,
        modelname: m.name,
        provider: providerId,
      });
    }
  }

  rows.sort(sortModelConfigRows);
  return rows;
}

function getSelectionValueForSavedConfig(savedConfig: DatabaseModelConfigDTO): string {
  return `${savedConfig.modelId}:${savedConfig.id}`;
}

export default function ModelSelectionPage() {
  const dispatch = useAppDispatch();
  const { selectedProvider, selectedModel, selectedConfig, isTestNameValid } =
    useAppSelector((state) => state.modelSelection);

  const [apiProviders, setApiProviders] = useState<Provider[]>([]);
  const [apiModels, setApiModels] = useState<ModelConfig[]>([]);
  const [providersLoading, setProvidersLoading] = useState(true);
  const [providersError, setProvidersError] = useState<string | null>(null);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [modelsError, setModelsError] = useState<string | null>(null);

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

  const isCustomConnector = custom_connectors.some(
    (connector) => connector.id === selectedProvider
  );

  const loadModelsForProvider = useCallback(async (providerId: string): Promise<ModelConfig[]> => {
    if (!providerId) {
      setApiModels([]);
      return [];
    }
    const providerRow = apiProviders.find((p) => p.id === providerId);
    const systemName = providerRow?.system_name;
    if (!systemName) {
      setApiModels([]);
      return [];
    }
    setModelsLoading(true);
    setModelsError(null);
    try {
      const details = await fetchProviderLatestDetails(systemName);
      const rows = mapProviderDetailsToModelRows(providerId, details);
      setApiModels(rows);
      return rows;
    } catch (e) {
      setModelsError(e instanceof ApiError ? e.message : "Failed to load models");
      setApiModels([]);
      return [];
    } finally {
      setModelsLoading(false);
    }
  }, [apiProviders]);

  useEffect(() => {
    if (isCustomConnector || !selectedProvider) {
      setApiModels([]);
      setModelsError(null);
      return;
    }
    void loadModelsForProvider(selectedProvider);
  }, [selectedProvider, isCustomConnector, loadModelsForProvider]);

  const refreshModelsForSelectedProvider = useCallback(async (savedConfig: DatabaseModelConfigDTO) => {
    if (!selectedProvider || isCustomConnector) return;
    const rows = await loadModelsForProvider(selectedProvider);
    const nextSelectedModel = getSelectionValueForSavedConfig(savedConfig);
    if (rows.some((row) => row.id === nextSelectedModel)) {
      const providerId = parseInt(selectedProvider, 10);
      const configId = parseInt(savedConfig.id, 10);
      dispatch(setSelectedModel(nextSelectedModel));
      dispatch(
        setBenchmarkRunFks({
          llm_provider_id: Number.isFinite(providerId) ? providerId : null,
          llm_provider_model_id: savedConfig.modelId,
          llm_provider_model_config_id: Number.isFinite(configId) ? configId : null,
        })
      );
    }
  }, [dispatch, selectedProvider, isCustomConnector, loadModelsForProvider]);

  const isModelSelected =
    (!isCustomConnector && selectedProvider && selectedModel) ||
    (isCustomConnector && selectedProvider && selectedConfig);

  return (
    <div className="p-8">
      <Breadcrumb data-testid="Breadcrumb">
        <BreadcrumbList>
          <BreadcrumbItem>New Benchmark Test</BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>Select Tests Or Test Bundles</BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>Select Model Or Application</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      <div className="flex items-center justify-between mb-6 mt-6">
        <div>
          <h1 className="text-2xl font-bold" data-testid="select-model-header">
            Configure And Run Tests
          </h1>
        </div>
      </div>

      <div className="flex flex-col items-center justify-center min-h-[200px] mb-10">
        <TestNameAndDescriptionCard />
        {isTestNameValid && (
          <>
            {providersError && (
              <p className="text-sm text-red-600 w-3xl mt-4" role="alert">
                {providersError}
              </p>
            )}
            {providersLoading ? (
              <p className="text-sm text-muted-foreground w-3xl mt-4">Loading providers…</p>
            ) : (
              <>
                {modelsError && (
                  <p className="text-sm text-red-600 w-3xl mt-2" role="alert">
                    {modelsError}
                  </p>
                )}
                {modelsLoading && selectedProvider && !isCustomConnector && (
                  <p className="text-sm text-muted-foreground w-3xl mt-2">Loading models…</p>
                )}
                <SelectAppOrModelCard
                  providers={apiProviders}
                  models={apiModels}
                  custom_connectors={custom_connectors}
                  configs={configs}
                  onModelsSaved={refreshModelsForSelectedProvider}
                />
              </>
            )}
          </>
        )}

        {isTestNameValid && isModelSelected && (
          <>
            <RequiredEndpointsCard />
            <SampleSizeCard />
          </>
        )}
      </div>
    </div>
  );
}

"use client"
import React, { useState, useMemo, useEffect } from 'react';
import { Button } from "@/components/ui/button"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { Card, CardContent, CardDescription, CardTitle } from "@/components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Check, ChevronsUpDown, Edit, Plus, CircleAlert, CircleCheckBig } from "lucide-react";
import type { Provider, ModelConfig, Config, ModelApp } from "../types/modelSelection";
import type { CustomAppConfigDTO, DatabaseModelConfigDTO } from "@/lib/api";
import { useAppDispatch, useAppSelector } from "@/hooks/reduxHooks";
import {
  setSelectedProvider,
  setSelectedModel,
  setSelectedConfig,
  setBenchmarkRunFks,
  updateConfigValidity,
} from "@/store";
import { decodeCustomAppProviderId } from "../constants/customAppConfig";
import EditModelSheet from "./EditModelSheet";
import EditCustomApplicationSheet from "./EditCustomApplicationSheet";

interface SelectAppOrModelCardProps {
  // Raw data
  providers: Provider[];
  models: ModelConfig[];
  custom_connectors: ModelApp[];
  configs: Config[];
  /** Called after a new DB model config is saved from EditModelSheet */
  onModelsSaved?: (savedConfig: DatabaseModelConfigDTO) => void | Promise<void>;
  /** Called after a custom app config is saved from EditCustomApplicationSheet */
  onConfigsSaved?: (savedConfig: CustomAppConfigDTO) => void | Promise<void>;
}

export default function SelectAppOrModelCard({
  providers,
  models,
  custom_connectors,
  configs,
  onModelsSaved,
  onConfigsSaved,
}: SelectAppOrModelCardProps) {
  const dispatch = useAppDispatch();
  
  // Redux state
  const { selectedProvider, selectedModel, selectedConfig, isConfigValid } = useAppSelector(state => state.modelSelection);
  
  // Local UI state
  const [providerOpen, setProviderOpen] = useState(false);
  const [modelOpen, setModelOpen] = useState(false);
  const [showAllStandardProviders, setShowAllStandardProviders] = useState(false);
  const [showAllCustomConnectors, setShowAllCustomConnectors] = useState(false);
  
  // Sheet state management
  const [sheetOpen, setSheetOpen] = useState(false);
  const [editingModel, setEditingModel] = useState<string>("");
  const [editingDatabaseConfigId, setEditingDatabaseConfigId] = useState<string | null>(null);
  const [customSheetOpen, setCustomSheetOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState<string>("");
  
  // Track config validity when selections change
  useEffect(() => {
    dispatch(updateConfigValidity());
  }, [selectedProvider, selectedModel, selectedConfig, dispatch]);
  
  // Computed values
  const filteredModels = useMemo(() => 
    models.filter(model => model.provider === selectedProvider),
    [models, selectedProvider]
  );
  
  const filteredConfigs = useMemo(() => 
    configs.filter(config => config.connector === selectedProvider),
    [configs, selectedProvider]
  );
  
  const isCustomConnector = useMemo(() => 
    custom_connectors.some(connector => connector.id === selectedProvider),
    [custom_connectors, selectedProvider]
  );
  
  // Sheet handlers
  const handleEditModel = (modelId: string, databaseConfigId?: string | null) => {
    setEditingModel(modelId);
    setEditingDatabaseConfigId(
      databaseConfigId != null && String(databaseConfigId).trim() !== ""
        ? String(databaseConfigId)
        : null
    );
    setSheetOpen(true);
  };

  const handleAddNewModel = () => {
    setEditingModel(selectedProvider); // Set selected provider to indicate new model creation for this provider
    setEditingDatabaseConfigId(null);
    setSheetOpen(true);
  };

  const handleEditConfig = (configId: string) => {
    setEditingConfig(configId);
    setCustomSheetOpen(true);
  };

  const handleAddNewConfig = () => {
    setEditingConfig(selectedProvider); // Set selected provider to indicate new configuration creation for this provider
    setCustomSheetOpen(true);
  };
  
  // Handle edit actions with event.stopPropagation
  const handleEditModelClick = (model: ModelConfig, event: React.MouseEvent) => {
    event.stopPropagation();
    handleEditModel(model.id, model.modelConfigId ?? null);
    setModelOpen(false);
  };
  
  const handleEditConfigClick = (configId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    handleEditConfig(configId);
    setModelOpen(false);
  };
  
  const handleAddNewModelClick = () => {
    handleAddNewModel();
    setModelOpen(false);
  };
  
  const handleAddNewConfigClick = () => {
    handleAddNewConfig();
    setModelOpen(false);
  };
  // Combine providers and custom connectors for sheets
  const allProviders = useMemo(() => [...providers, ...custom_connectors], [providers, custom_connectors]);

  return (
    <>
      <Card className="w-3xl py-1">
        <Accordion type="single" collapsible defaultValue="item-1">
          <AccordionItem value="item-1">
            <AccordionTrigger className="flex flex-row items-center hover:no-underline px-6 py-4">
              <div className="flex-1">
                <CardTitle data-testid="card-title">Select App or Model</CardTitle>
                <CardDescription data-testid="card-description">
                  Confirm the details of the app or model to be tested.
                </CardDescription>
              </div>
              {/* Status indicators */}
              <div className="flex items-center">
                {!isConfigValid && (
                  <CircleAlert className="h-5 w-5 text-red-500" data-testid="status-indicator" />
                )}
                {isConfigValid && (
                  <CircleCheckBig className="h-5 w-5 text-green-500" data-testid="status-indicator" />
                )}
              </div>
            </AccordionTrigger>
            <AccordionContent>
              <CardContent className="flex gap-6">
              <div className="w-80">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  LLM Provider
                </label>
                <Popover open={providerOpen} onOpenChange={setProviderOpen}>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      role="combobox"
                      aria-expanded={providerOpen}
                      className="w-full justify-between"
                      data-testid="provider-combobox-trigger"
                    >
                      {selectedProvider
                        ? allProviders.find((provider) => provider.id === selectedProvider)?.name
                        : "Select provider..."}
                      <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-full p-0" align="start">
                    <Command>
                      <CommandInput placeholder="Search providers..." />
                      <CommandList className="max-h-[300px] overflow-y-auto">
                        <CommandEmpty>No provider found.</CommandEmpty>
                        <CommandGroup heading="Model Providers" data-testid="model-providers-group">
                          {providers.slice(0, showAllStandardProviders ? providers.length : 3).map((provider) => (
                            <CommandItem
                              key={provider.id}
                              value={provider.id}
                              onSelect={(currentValue) => {
                                const newProvider = currentValue === selectedProvider ? "" : currentValue;
                                dispatch(setSelectedProvider(newProvider));
                                setProviderOpen(false);
                              }}
                              data-testid={`provider-option-${provider.id}`}
                            >
                              <Check
                                className={`mr-2 h-4 w-4 ${selectedProvider === provider.id ? "opacity-100" : "opacity-0"}`}
                              />
                              {provider.name}
                            </CommandItem>
                          ))}
                          {!showAllStandardProviders && providers.length > 3 && (
                            <CommandItem
                              value="view-all-standard"
                              onSelect={() => {
                                setShowAllStandardProviders(true);
                              }}
                              data-testid="view-all-standard-providers"
                            >
                              <Check className="mr-2 h-4 w-4 opacity-0" />
                              View All Standard Providers ({providers.length - 3})
                            </CommandItem>
                          )}
                          {showAllStandardProviders && (
                            <CommandItem
                              value="show-less-standard"
                              onSelect={() => {
                                setShowAllStandardProviders(false);
                              }}
                              data-testid="show-less-standard-providers"
                            >
                              <Check className="mr-2 h-4 w-4 opacity-0" />
                              Show Less
                            </CommandItem>
                          )}
                        </CommandGroup>
                        <CommandGroup heading="Custom Applications" data-testid="custom-applications-group">
                          {custom_connectors.slice(0, showAllCustomConnectors ? custom_connectors.length : 3).map((connector) => (
                            <CommandItem
                              key={connector.id}
                              value={connector.id}
                              onSelect={(currentValue) => {
                                const newProvider = currentValue === selectedProvider ? "" : currentValue;
                                dispatch(setSelectedProvider(newProvider));
                                setProviderOpen(false);
                              }}
                              data-testid={`custom-connector-option-${connector.id}`}
                            >
                              <Check
                                className={`mr-2 h-4 w-4 ${selectedProvider === connector.id ? "opacity-100" : "opacity-0"}`}
                              />
                              {connector.name}
                            </CommandItem>
                          ))}
                          {!showAllCustomConnectors && custom_connectors.length > 3 && (
                            <CommandItem
                              value="view-all-custom"
                              onSelect={() => {
                                setShowAllCustomConnectors(true);
                              }}
                              data-testid="view-all-custom-connectors"
                            >
                              <Check className="mr-2 h-4 w-4 opacity-0" />
                              View All Custom Connectors ({custom_connectors.length - 3})
                            </CommandItem>
                          )}
                          {showAllCustomConnectors && (
                            <CommandItem
                              value="show-less-custom"
                              onSelect={() => {
                                setShowAllCustomConnectors(false);
                              }}
                              data-testid="show-less-custom-connectors"
                            >
                              <Check className="mr-2 h-4 w-4 opacity-0" />
                              Show Less
                            </CommandItem>
                          )}
                        </CommandGroup>
                      </CommandList>
                    </Command>
                  </PopoverContent>
                </Popover>
              </div>
              
              {/* Model/Config selection combo box - only shows when provider is selected */}
              {selectedProvider && (
                <div className="flex-1">
                  <label className="block text-sm font-medium text-gray-700 mb-2" data-testid={isCustomConnector ? "configuration-label" : "model-label"}>
                    {isCustomConnector ? "Configuration" : "Model"}
                  </label>
                  <Popover open={modelOpen} onOpenChange={setModelOpen}>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        role="combobox"
                        aria-expanded={modelOpen}
                        className="w-full justify-between"
                        data-testid="model-combobox-trigger"
                      >
                        {isCustomConnector 
                          ? (selectedConfig
                              ? filteredConfigs.find((config) => config.id === selectedConfig)?.name
                              : "Select configuration...")
                          : (selectedModel
                              ? filteredModels.find((model) => model.id === selectedModel)?.name
                              : "Select model...")}
                        <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-full p-0" align="start">
                      <Command>
                        <CommandInput placeholder={isCustomConnector ? "Search configurations..." : "Search models..."} />
                        <CommandList>
                          <CommandEmpty>{isCustomConnector ? "No configuration found." : "No model found."}</CommandEmpty>
                          {isCustomConnector ? (
                            filteredConfigs.map((config) => (
                              <CommandItem
                                key={config.id}
                                value={config.id}
                                onSelect={(currentValue) => {
                                  const newConfig = currentValue === selectedConfig ? "" : currentValue;
                                  dispatch(setSelectedConfig(newConfig));
                                  if (newConfig) {
                                    const appId = decodeCustomAppProviderId(selectedProvider);
                                    const configId = parseInt(newConfig, 10);
                                    dispatch(
                                      setBenchmarkRunFks({
                                        llm_provider_id: null,
                                        llm_provider_model_id: null,
                                        llm_provider_model_config_id: null,
                                        custom_app_id: appId,
                                        custom_app_config_id: Number.isFinite(configId)
                                          ? configId
                                          : null,
                                      })
                                    );
                                  } else {
                                    dispatch(
                                      setBenchmarkRunFks({
                                        llm_provider_id: null,
                                        llm_provider_model_id: null,
                                        llm_provider_model_config_id: null,
                                        custom_app_id: null,
                                        custom_app_config_id: null,
                                      })
                                    );
                                  }
                                  setModelOpen(false);
                                }}
                                data-testid={`config-option-${config.id}`}
                                className="flex items-center justify-between"
                              >
                                <div className="flex items-center">
                                  <Check
                                    className={`mr-2 h-4 w-4 ${selectedConfig === config.id ? "opacity-100" : "opacity-0"}`}
                                  />
                                  {config.name}
                                </div>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-6 w-6 p-0 hover:bg-gray-100"
                                  onClick={(e) => handleEditConfigClick(config.id, e)}
                                  data-testid={`edit-config-${config.id}`}
                                >
                                  <Edit className="h-3 w-3" />
                                </Button>
                              </CommandItem>
                            ))
                          ) : (
                            filteredModels.map((model) => (
                              <CommandItem
                                key={model.id}
                                value={model.id}
                                onSelect={(currentValue) => {
                                  const newModel = currentValue === selectedModel ? "" : currentValue;
                                  dispatch(setSelectedModel(newModel));
                                  if (newModel && !isCustomConnector) {
                                    const pid = parseInt(selectedProvider, 10);
                                    const row = filteredModels.find((mo) => mo.id === newModel);
                                    const mcid = row?.modelConfigId
                                      ? parseInt(row.modelConfigId, 10)
                                      : NaN;
                                    dispatch(
                                      setBenchmarkRunFks({
                                        llm_provider_id: Number.isFinite(pid) ? pid : null,
                                        llm_provider_model_id: parseInt(newModel, 10),
                                        llm_provider_model_config_id: Number.isFinite(mcid)
                                          ? mcid
                                          : null,
                                        custom_app_id: null,
                                        custom_app_config_id: null,
                                      })
                                    );
                                  } else {
                                    dispatch(
                                      setBenchmarkRunFks({
                                        llm_provider_id: null,
                                        llm_provider_model_id: null,
                                        llm_provider_model_config_id: null,
                                        custom_app_id: null,
                                        custom_app_config_id: null,
                                      })
                                    );
                                  }
                                  setModelOpen(false);
                                }}
                                data-testid={`model-option-${model.id}`}
                                className="flex items-center justify-between"
                              >
                                <div className="flex items-center">
                                  <Check
                                    className={`mr-2 h-4 w-4 ${selectedModel === model.id ? "opacity-100" : "opacity-0"}`}
                                  />
                                  {model.name}
                                </div>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-6 w-6 p-0 hover:bg-gray-100"
                                  onClick={(e) => handleEditModelClick(model, e)}
                                  data-testid={`edit-model-${model.id}`}
                                >
                                  <Edit className="h-3 w-3" />
                                </Button>
                              </CommandItem>
                            ))
                          )}
                          <CommandItem
                            value="add-new-item"
                            onSelect={() => {
                              if (!isCustomConnector) {
                                handleAddNewModelClick();
                              } else {
                                handleAddNewConfigClick();
                              }
                            }}
                            data-testid={`add-new-${isCustomConnector ? 'config' : 'model'}-from-dropdown`}
                          >
                            <Plus className="mr-2 h-4 w-4" />
                            Add New {isCustomConnector ? 'Configuration' : 'Model'}
                          </CommandItem>
                        </CommandList>
                      </Command>
                    </PopoverContent>
                  </Popover>
                </div>
              )}
            </CardContent>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </Card>
    
    {/* Edit Model Sheet */}
    <EditModelSheet
      open={sheetOpen}
      onOpenChange={(open) => {
        setSheetOpen(open);
        if (!open) setEditingDatabaseConfigId(null);
      }}
      editingModel={editingModel}
      editingDatabaseConfigId={editingDatabaseConfigId}
      providers={allProviders}
      models={models}
      onSaved={onModelsSaved}
    />
    
    {/* Edit Custom Application Sheet */}
    <EditCustomApplicationSheet
      open={customSheetOpen}
      onOpenChange={setCustomSheetOpen}
      editingConfig={editingConfig}
      modelApps={custom_connectors}
      configs={configs}
      onSaved={onConfigsSaved}
    />
  </>
  );
}


"use client"
import React, { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Breadcrumb, BreadcrumbList, BreadcrumbItem, BreadcrumbPage, BreadcrumbSeparator } from '@/components/ui/breadcrumb';
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Check, ChevronsUpDown, Edit, Plus, CircleAlert, CircleCheckBig } from "lucide-react";
import { cn } from "@/lib/utils";
import EditModelSheet from "./EditModelSheet";
import EditCustomApplicationSheet from "./EditCustomApplicationSheet";
import RequiredEndpointsCard from "./RequiredEndpointsCard";
import SampleSizeCard from "./SampleSizeCard";
import { providers, models, custom_connectors, configs, type Provider, type ModelConfig, type Config, type ModelApp } from "./MockData";
import { useAppDispatch, useAppSelector } from "@/hooks/reduxHooks";
import { setSelectedProvider, setSelectedModel, setSelectedConfig, updateConfigValidity } from "@/store";

interface ModelSelectionPageProps {}

export default function ModelSelectionPage({}: ModelSelectionPageProps) {
  const dispatch = useAppDispatch();
  const { selectedProvider, selectedModel, selectedConfig, isConfigValid } = useAppSelector(state => state.modelSelection);
  
  const [providerOpen, setProviderOpen] = useState(false);
  const [modelOpen, setModelOpen] = useState(false);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [editingModel, setEditingModel] = useState<string>("");
  const [customSheetOpen, setCustomSheetOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState<string>("");
  const [showAllStandardProviders, setShowAllStandardProviders] = useState(false);
  const [showAllCustomConnectors, setShowAllCustomConnectors] = useState(false);

  // Combine providers and custom connectors
  const allProviders = [...providers, ...custom_connectors];

  // Get models filtered by selected provider
  const filteredModels = models.filter(model => model.provider === selectedProvider);
  
  // Get configs filtered by selected custom connector
  const filteredConfigs = configs.filter(config => config.connector === selectedProvider);
  
  // Check if selected provider is a custom connector
  const isCustomConnector = custom_connectors.some(connector => connector.id === selectedProvider);

  // Track config validity
  useEffect(() => {
    dispatch(updateConfigValidity());
  }, [selectedProvider, selectedModel, selectedConfig, dispatch]);

  // Handle edit model action
  const handleEditModel = (modelId: string, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent triggering the selection
    setEditingModel(modelId);
    setSheetOpen(true);
    setModelOpen(false); // Close the model dropdown
  };

  // Handle add new model action
  const handleAddNewModel = () => {
    console.log('Add new model clicked');
    setEditingModel(selectedProvider); // Set selected provider to indicate new model creation for this provider
    setSheetOpen(true);
    setProviderOpen(false); // Close the provider dropdown
  };

  // Handle edit configuration action
  const handleEditConfig = (configId: string, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent triggering the selection
    setEditingConfig(configId);
    setCustomSheetOpen(true);
    setModelOpen(false); // Close the model dropdown
  };

  // Handle add new configuration action
  const handleAddNewConfig = () => {
    console.log('Add new configuration clicked');
    setEditingConfig(selectedProvider); // Set selected provider to indicate new configuration creation for this provider
    setCustomSheetOpen(true);
    setModelOpen(false); // Close the model dropdown
  };

  return (
    <div className="p-8">
      <Breadcrumb data-testid="Breadcrumb">
        <BreadcrumbList>
          <BreadcrumbItem>
            New Benchmark Test
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            Select Model
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>Configure And Run Tests</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
      
      <div className="flex items-center justify-between mb-6 mt-6">
        <div>
          <h1 className="text-2xl font-bold" data-testid="select-model-header">Select Model</h1>
          <p className="text-gray-600" data-testid="select-model-description">Choose the model for your benchmark test</p>
        </div>
      </div>
      
      <div className="flex flex-col items-center justify-center min-h-[200px]">
        <Card className="w-3xl">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
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
          </CardHeader>
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
                              className={cn(
                                "mr-2 h-4 w-4",
                                selectedProvider === provider.id ? "opacity-100" : "opacity-0"
                              )}
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
                              className={cn(
                                "mr-2 h-4 w-4",
                                selectedProvider === connector.id ? "opacity-100" : "opacity-0"
                              )}
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
                                setModelOpen(false);
                              }}
                              data-testid={`config-option-${config.id}`}
                              className="flex items-center justify-between"
                            >
                              <div className="flex items-center">
                                <Check
                                  className={cn(
                                    "mr-2 h-4 w-4",
                                    selectedConfig === config.id ? "opacity-100" : "opacity-0"
                                  )}
                                />
                                {config.name}
                              </div>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 w-6 p-0 hover:bg-gray-100"
                                onClick={(e) => handleEditConfig(config.id, e)}
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
                                setModelOpen(false);
                              }}
                              data-testid={`model-option-${model.id}`}
                              className="flex items-center justify-between"
                            >
                              <div className="flex items-center">
                                <Check
                                  className={cn(
                                    "mr-2 h-4 w-4",
                                    selectedModel === model.id ? "opacity-100" : "opacity-0"
                                  )}
                                />
                                {model.name}
                              </div>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 w-6 p-0 hover:bg-gray-100"
                                onClick={(e) => handleEditModel(model.id, e)}
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
                              handleAddNewModel();
                            } else {
                              handleAddNewConfig();
                            }
                            setModelOpen(false);
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
        </Card>
        
        {/* Additional Card */}
        <RequiredEndpointsCard />
        
        {/* Sample Size Card */}
        <SampleSizeCard />
      </div>
      {/* Edit Model Sheet */}
      <EditModelSheet
        open={sheetOpen}
        onOpenChange={setSheetOpen}
        editingModel={editingModel}
        providers={allProviders}
        models={models}
      />
      
      {/* Edit Custom Application Sheet */}
      <EditCustomApplicationSheet
        open={customSheetOpen}
        onOpenChange={setCustomSheetOpen}
        editingConfig={editingConfig}
        modelApps={custom_connectors}
        configs={configs}
      />
    </div>
  );
}

"use client"
import React from 'react';
import { Button } from "@/components/ui/button"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { Card, CardContent, CardDescription, CardTitle } from "@/components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Check, ChevronsUpDown, Edit, Plus, CircleAlert, CircleCheckBig } from "lucide-react";
import { type Provider, type ModelConfig, type Config, type ModelApp } from "./MockData";
import { type AppDispatch } from "@/store";
import { setSelectedProvider, setSelectedModel, setSelectedConfig } from "@/store";

interface SelectAppOrModelCardProps {
  // State
  providerOpen: boolean;
  setProviderOpen: (open: boolean) => void;
  modelOpen: boolean;
  setModelOpen: (open: boolean) => void;
  showAllStandardProviders: boolean;
  setShowAllStandardProviders: (show: boolean) => void;
  showAllCustomConnectors: boolean;
  setShowAllCustomConnectors: (show: boolean) => void;
  
  // Redux state
  selectedProvider: string;
  selectedModel: string;
  selectedConfig: string;
  isConfigValid: boolean;
  
  // Data
  allProviders: (Provider | ModelApp)[];
  providers: Provider[];
  custom_connectors: ModelApp[];
  filteredModels: ModelConfig[];
  filteredConfigs: Config[];
  isCustomConnector: boolean;
  
  // Handlers
  handleEditModel: (modelId: string, event: React.MouseEvent) => void;
  handleAddNewModel: () => void;
  handleEditConfig: (configId: string, event: React.MouseEvent) => void;
  handleAddNewConfig: () => void;
  
  // Dispatch
  dispatch: AppDispatch;
}

export default function SelectAppOrModelCard({
  providerOpen,
  setProviderOpen,
  modelOpen,
  setModelOpen,
  showAllStandardProviders,
  setShowAllStandardProviders,
  showAllCustomConnectors,
  setShowAllCustomConnectors,
  selectedProvider,
  selectedModel,
  selectedConfig,
  isConfigValid,
  allProviders,
  providers,
  custom_connectors,
  filteredModels,
  filteredConfigs,
  isCustomConnector,
  handleEditModel,
  handleAddNewModel,
  handleEditConfig,
  handleAddNewConfig,
  dispatch,
}: SelectAppOrModelCardProps) {
  return (
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
                                    className={`mr-2 h-4 w-4 ${selectedModel === model.id ? "opacity-100" : "opacity-0"}`}
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
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </Card>
  );
}


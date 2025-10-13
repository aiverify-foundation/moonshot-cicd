"use client"
import React, { useState } from 'react';
import { Button } from "@/components/ui/button"
import { Breadcrumb, BreadcrumbList, BreadcrumbItem, BreadcrumbPage, BreadcrumbSeparator } from '@/components/ui/breadcrumb';
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Check, ChevronsUpDown, Edit, Plus, CircleAlert, CircleCheckBig } from "lucide-react";
import { cn } from "@/lib/utils";
import EditModelSheet from "./EditModelSheet";
import { providers, models, custom_connectors, type Provider, type Model } from "./MockData";

interface ModelSelectionPageProps {
  onBack: () => void;
  onNext: () => void;
}

export default function ModelSelectionPage({ onBack, onNext }: ModelSelectionPageProps) {
  const [providerOpen, setProviderOpen] = useState(false);
  const [modelOpen, setModelOpen] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<string>("");
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [sheetOpen, setSheetOpen] = useState(false);
  const [editingModel, setEditingModel] = useState<string>("");
  const [showAllStandardProviders, setShowAllStandardProviders] = useState(false);
  const [showAllCustomConnectors, setShowAllCustomConnectors] = useState(false);

  // Combine providers and custom connectors
  const allProviders = [...providers, ...custom_connectors];

  // Get models filtered by selected provider
  const filteredModels = models.filter(model => model.provider === selectedProvider);

  // Handle edit model action
  const handleEditModel = (modelValue: string, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent triggering the selection
    setEditingModel(modelValue);
    setSheetOpen(true);
    setModelOpen(false); // Close the model dropdown
  };

  // Handle add new model action
  const handleAddNewModel = () => {
    console.log('Add new model clicked');
    // Add your add new model logic here
    setProviderOpen(false); // Close the provider dropdown
  };

  return (
    <main className="p-8">
      <Breadcrumb data-testid="Breadcrumb">
        <BreadcrumbList>
          <BreadcrumbItem>
            New Benchmark Test
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>Select Model</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
      
      <div className="flex items-center justify-between mb-6 mt-6">
        <div>
          <h1 className="text-2xl font-bold" data-testid="select-model-header">Select Model</h1>
          <p className="text-gray-600" data-testid="select-model-description">Choose the model for your benchmark test</p>
        </div>
      </div>
      
      <div className="flex flex-col items-center justify-center min-h-[400px]">
        <Card className="w-full max-w-4xl">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Select Test Endpoint</CardTitle>
              <CardDescription>
                Confirm the details of the endpoint for this test
              </CardDescription>
            </div>
            {/* Status indicators */}
            <div className="flex items-center">
              {selectedProvider && !selectedModel && (
                <CircleAlert className="h-5 w-5 text-red-500" />
              )}
              {selectedProvider && selectedModel && (
                <CircleCheckBig className="h-5 w-5 text-green-500" />
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                LLM Provider
              </label>
              <Popover open={providerOpen} onOpenChange={setProviderOpen}>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    role="combobox"
                    aria-expanded={providerOpen}
                    className="w-[780px] justify-between"
                    data-testid="provider-combobox-trigger"
                  >
                    {selectedProvider
                      ? allProviders.find((provider) => provider.value === selectedProvider)?.label
                      : "Select provider..."}
                    <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-full p-0" align="start">
                  <Command>
                    <CommandInput placeholder="Search providers..." />
                    <CommandList className="max-h-[300px] overflow-y-auto">
                      <CommandEmpty>No provider found.</CommandEmpty>
                      
                      <CommandGroup heading="Standard Providers">
                        {providers.slice(0, showAllStandardProviders ? providers.length : 3).map((provider) => (
                          <CommandItem
                            key={provider.value}
                            value={provider.value}
                            onSelect={(currentValue) => {
                              setSelectedProvider(currentValue === selectedProvider ? "" : currentValue);
                              setSelectedModel(""); // Reset model selection when provider changes
                              setProviderOpen(false);
                            }}
                            data-testid={`provider-option-${provider.value}`}
                          >
                            <Check
                              className={cn(
                                "mr-2 h-4 w-4",
                                selectedProvider === provider.value ? "opacity-100" : "opacity-0"
                              )}
                            />
                            {provider.label}
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

                      <CommandGroup heading="Custom Connectors">
                        {custom_connectors.slice(0, showAllCustomConnectors ? custom_connectors.length : 3).map((connector) => (
                          <CommandItem
                            key={connector.value}
                            value={connector.value}
                            onSelect={(currentValue) => {
                              setSelectedProvider(currentValue === selectedProvider ? "" : currentValue);
                              setSelectedModel(""); // Reset model selection when provider changes
                              setProviderOpen(false);
                            }}
                            data-testid={`custom-connector-option-${connector.value}`}
                          >
                            <Check
                              className={cn(
                                "mr-2 h-4 w-4",
                                selectedProvider === connector.value ? "opacity-100" : "opacity-0"
                              )}
                            />
                            {connector.label}
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

                      <CommandGroup heading="Actions">
                        <CommandItem
                          value="add-new-model"
                          onSelect={handleAddNewModel}
                          data-testid="add-new-model"
                        >
                          <Plus className="mr-2 h-4 w-4" />
                          Add New Model
                        </CommandItem>
                      </CommandGroup>
                    </CommandList>
                  </Command>
                </PopoverContent>
              </Popover>
            </div>
            
            {/* Model selection combo box - only shows when provider is selected */}
            {selectedProvider && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Model
                </label>
                <Popover open={modelOpen} onOpenChange={setModelOpen}>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      role="combobox"
                      aria-expanded={modelOpen}
                      className="w-[780px] justify-between"
                      data-testid="model-combobox-trigger"
                    >
                      {selectedModel
                        ? filteredModels.find((model) => model.value === selectedModel)?.label
                        : "Select model..."}
                      <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-full p-0" align="start">
                    <Command>
                      <CommandInput placeholder="Search models..." />
                      <CommandList>
                        <CommandEmpty>No model found.</CommandEmpty>
                        {filteredModels.map((model) => (
                          <CommandItem
                            key={model.value}
                            value={model.value}
                            onSelect={(currentValue) => {
                              setSelectedModel(currentValue === selectedModel ? "" : currentValue);
                              setModelOpen(false);
                            }}
                            data-testid={`model-option-${model.value}`}
                            className="flex items-center justify-between"
                          >
                            <div className="flex items-center">
                              <Check
                                className={cn(
                                  "mr-2 h-4 w-4",
                                  selectedModel === model.value ? "opacity-100" : "opacity-0"
                                )}
                              />
                              {model.label}
                            </div>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-6 w-6 p-0 hover:bg-gray-100"
                              onClick={(e) => handleEditModel(model.value, e)}
                              data-testid={`edit-model-${model.value}`}
                            >
                              <Edit className="h-3 w-3" />
                            </Button>
                          </CommandItem>
                        ))}
                        
                        <CommandGroup heading="Actions">
                          <CommandItem
                            value="add-new-model"
                            onSelect={() => {
                              console.log('Add new model clicked from model dropdown');
                              setModelOpen(false);
                            }}
                            data-testid="add-new-model-from-model-dropdown"
                          >
                            <Plus className="mr-2 h-4 w-4" />
                            Add New Model
                          </CommandItem>
                        </CommandGroup>
                      </CommandList>
                    </Command>
                  </PopoverContent>
                </Popover>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
      
      <div className="flex justify-between pt-6">
        <Button 
          variant="outline" 
          className="flex items-center gap-2"
          onClick={onBack}
          data-testid="back-to-bundles-button"
        >
          Back to Bundle Selection
        </Button>
        <Button 
          className="flex items-center gap-2" 
          onClick={onNext}
          data-testid="run-benchmark-tests"
        >
          Run Benchmark Tests
        </Button>
      </div>

      {/* Edit Model Sheet */}
      <EditModelSheet
        open={sheetOpen}
        onOpenChange={setSheetOpen}
        editingModel={editingModel}
        providers={allProviders}
        models={models}
      />
    </main>
  );
}

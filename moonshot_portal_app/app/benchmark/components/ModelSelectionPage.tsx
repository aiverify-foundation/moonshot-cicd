"use client"
import React, { useState, useEffect } from 'react';
import { Breadcrumb, BreadcrumbList, BreadcrumbItem, BreadcrumbPage, BreadcrumbSeparator } from '@/components/ui/breadcrumb';
import { Button } from '@/components/ui/button';
import EditModelSheet from "./EditModelSheet";
import EditCustomApplicationSheet from "./EditCustomApplicationSheet";
import RequiredEndpointsCard from "./RequiredEndpointsCard";
import SampleSizeCard from "./SampleSizeCard";
import TestNameAndDescriptionCard from "./TestNameAndDescriptionCard";
import SelectAppOrModelCard from "./SelectAppOrModelCard";
import { providers, models, custom_connectors, configs } from "./MockData";
import { useAppDispatch, useAppSelector } from "@/hooks/reduxHooks";
import { updateConfigValidity } from "@/store";

export default function ModelSelectionPage() {
  const dispatch = useAppDispatch();
  const { selectedProvider, selectedModel, selectedConfig, isConfigValid, isTestNameValid } = useAppSelector(state => state.modelSelection);
  
  // Sheet state management
  const [sheetOpen, setSheetOpen] = useState(false);
  const [editingModel, setEditingModel] = useState<string>("");
  const [customSheetOpen, setCustomSheetOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState<string>("");

  // Check if selected provider is a custom connector
  const isCustomConnector = custom_connectors.some(connector => connector.id === selectedProvider);

  // Check if both provider and model/config are selected
  const isModelSelected = (!isCustomConnector && selectedProvider && selectedModel) || 
                          (isCustomConnector && selectedProvider && selectedConfig);

  // Track config validity
  useEffect(() => {
    dispatch(updateConfigValidity());
  }, [selectedProvider, selectedModel, selectedConfig, dispatch]);

  // Combine providers and custom connectors for sheets
  const allProviders = [...providers, ...custom_connectors];

  // Handle edit model action
  const handleEditModel = (modelId: string) => {
    setEditingModel(modelId);
    setSheetOpen(true);
  };

  // Handle add new model action
  const handleAddNewModel = () => {
    setEditingModel(selectedProvider); // Set selected provider to indicate new model creation for this provider
    setSheetOpen(true);
  };

  // Handle edit configuration action
  const handleEditConfig = (configId: string) => {
    setEditingConfig(configId);
    setCustomSheetOpen(true);
  };

  // Handle add new configuration action
  const handleAddNewConfig = () => {
    setEditingConfig(selectedProvider); // Set selected provider to indicate new configuration creation for this provider
    setCustomSheetOpen(true);
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
          Select Recipes Or Bundles
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>Select Model Or Application</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      <div className="flex items-center justify-between mb-6 mt-6">
        <div>
          <h1 className="text-2xl font-bold" data-testid="select-model-header">Configure And Run Tests</h1>
        </div>
      </div>
      
      
      <div className="flex flex-col items-center justify-center min-h-[200px] mb-10">
        
        <TestNameAndDescriptionCard />
        {/* TODO: Look into how to clean this up, it probably can be done better*/}
        {isTestNameValid && (
          <SelectAppOrModelCard
            selectedProvider={selectedProvider}
            selectedModel={selectedModel}
            selectedConfig={selectedConfig}
            isConfigValid={isConfigValid}
            providers={providers}
            models={models}
            custom_connectors={custom_connectors}
            configs={configs}
            onEditModel={handleEditModel}
            onAddNewModel={handleAddNewModel}
            onEditConfig={handleEditConfig}
            onAddNewConfig={handleAddNewConfig}
          />
        )}
        
        {/* Additional Card - only show when both provider and model/config are selected */}
        {(isTestNameValid && isModelSelected) && (
          <>
            <RequiredEndpointsCard />
            <SampleSizeCard />
          </>
        )}
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

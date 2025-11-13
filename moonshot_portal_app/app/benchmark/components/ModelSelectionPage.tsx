"use client"
import React, { useState, useEffect } from 'react';
import { Breadcrumb, BreadcrumbList, BreadcrumbItem, BreadcrumbPage, BreadcrumbSeparator } from '@/components/ui/breadcrumb';
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
  const { selectedProvider, selectedModel, selectedConfig, isConfigValid, isTestNameFilled } = useAppSelector(state => state.modelSelection);
  
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
          <h1 className="text-2xl font-bold" data-testid="select-model-header">Configure And Run Tests</h1>
        </div>
      </div>
      
      
      <div className="flex flex-col items-center justify-center min-h-[200px]">
        
        <TestNameAndDescriptionCard />

        {/* TODO: Look into how to clean this up, it probably can be done better*/}
        <SelectAppOrModelCard
          providerOpen={providerOpen}
          setProviderOpen={setProviderOpen}
          modelOpen={modelOpen}
          setModelOpen={setModelOpen}
          showAllStandardProviders={showAllStandardProviders}
          setShowAllStandardProviders={setShowAllStandardProviders}
          showAllCustomConnectors={showAllCustomConnectors}
          setShowAllCustomConnectors={setShowAllCustomConnectors}
          selectedProvider={selectedProvider}
          selectedModel={selectedModel}
          selectedConfig={selectedConfig}
          isConfigValid={isConfigValid}
          allProviders={allProviders}
          providers={providers}
          custom_connectors={custom_connectors}
          filteredModels={filteredModels}
          filteredConfigs={filteredConfigs}
          isCustomConnector={isCustomConnector}
          handleEditModel={handleEditModel}
          handleAddNewModel={handleAddNewModel}
          handleEditConfig={handleEditConfig}
          handleAddNewConfig={handleAddNewConfig}
          dispatch={dispatch}
        />
        
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

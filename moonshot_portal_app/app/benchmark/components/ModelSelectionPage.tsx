"use client"
import React from 'react';
import { Breadcrumb, BreadcrumbList, BreadcrumbItem, BreadcrumbPage, BreadcrumbSeparator } from '@/components/ui/breadcrumb';
import { Button } from '@/components/ui/button';
import RequiredEndpointsCard from "./RequiredEndpointsCard";
import SampleSizeCard from "./SampleSizeCard";
import TestNameAndDescriptionCard from "./TestNameAndDescriptionCard";
import SelectAppOrModelCard from "./SelectAppOrModelCard";
import { providers, models, custom_connectors, configs } from "./MockData";
import { useAppSelector } from "@/hooks/reduxHooks";

export default function ModelSelectionPage() {
  const { selectedProvider, selectedModel, selectedConfig, isTestNameValid } = useAppSelector(state => state.modelSelection);

  // Check if selected provider is a custom connector
  const isCustomConnector = custom_connectors.some(connector => connector.id === selectedProvider);

  // Check if both provider and model/config are selected
  const isModelSelected = (!isCustomConnector && selectedProvider && selectedModel) || 
                          (isCustomConnector && selectedProvider && selectedConfig);

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
        {/* if Test Name is valid, display the Select App or Model Card*/}
        {isTestNameValid && (
          <SelectAppOrModelCard
            providers={providers}
            models={models}
            custom_connectors={custom_connectors}
            configs={configs}
          />
        )}
        
        {/* If Test Name is valid and a provider and model/config are selected, display the Required Endpoints and Sample Size Cards*/}
        {(isTestNameValid && isModelSelected) && (
          <>
            <RequiredEndpointsCard />
            <SampleSizeCard />
          </>
        )}
      </div>
    </div>
  );
}

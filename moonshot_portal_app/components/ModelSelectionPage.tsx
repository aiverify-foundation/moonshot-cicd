"use client"
import React from 'react';
import { Button } from "@/components/ui/button"
import { Breadcrumb, BreadcrumbList, BreadcrumbItem, BreadcrumbPage, BreadcrumbSeparator } from '@/components/ui/breadcrumb';

interface ModelSelectionPageProps {
  onBack: () => void;
  onNext: () => void;
}

export default function ModelSelectionPage({ onBack, onNext }: ModelSelectionPageProps) {
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
      
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        <p className="text-gray-600">Model selection interface will be implemented here</p>
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
    </main>
  );
}

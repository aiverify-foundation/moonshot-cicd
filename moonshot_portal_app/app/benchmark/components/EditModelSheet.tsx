"use client"
import React from 'react';
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";

interface EditModelSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  editingModel: string;
  providers: Array<{ value: string; label: string }>;
  models: Array<{ value: string; label: string; provider: string }>;
}

export default function EditModelSheet({ 
  open, 
  onOpenChange, 
  editingModel, 
  providers, 
  models 
}: EditModelSheetProps) {
  const currentModel = models.find(m => m.value === editingModel);
  const currentProvider = providers.find(p => p.value === currentModel?.provider);

  const handleSave = () => {
    // Add your save logic here
    console.log('Saving model configuration for:', editingModel);
    onOpenChange(false);
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[400px] sm:w-[540px]">
        <SheetHeader>
          <SheetTitle>Edit Model Configuration</SheetTitle>
          <SheetDescription>
            Configure settings for {currentModel?.label || 'the selected model'}
          </SheetDescription>
        </SheetHeader>
        <div className="mt-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Model Name
            </label>
            <input
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              defaultValue={currentModel?.label || ''}
              placeholder="Enter model name"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Provider
            </label>
            <input
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              defaultValue={currentProvider?.label || ''}
              placeholder="Enter provider name"
              readOnly
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              API Endpoint
            </label>
            <input
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter API endpoint URL"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Max Tokens
            </label>
            <input
              type="number"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter max tokens"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Temperature
            </label>
            <input
              type="number"
              step="0.1"
              min="0"
              max="2"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter temperature (0-2)"
            />
          </div>
          <div className="flex justify-end space-x-2 pt-4">
            <Button
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button onClick={handleSave}>
              Save Changes
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}

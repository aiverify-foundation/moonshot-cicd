"use client"
import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CircleCheckBig } from 'lucide-react';
import {
    Accordion,
    AccordionContent,
    AccordionItem,
    AccordionTrigger,
  } from "@/components/ui/accordion"
import EditModelSheet from './EditModelSheet';
import { providers, models } from './MockData';

enum ConnectionStatus {
  CONNECTED = "connected",
  NOT_CONNECTED = "not connected",
  INVALID_TOKEN = "Invalid Token"
}

// Helper function to render endpoint status card
const renderEndpointStatusCard = (modelName: string, status: ConnectionStatus, tests: string[], onConnect: () => void) => {
  const getBadgeClasses = (status: ConnectionStatus) => {
    switch (status) {
      case ConnectionStatus.CONNECTED:
        return "bg-green-100 text-green-800 border-green-200";
      case ConnectionStatus.NOT_CONNECTED:
        return "bg-gray-100 text-gray-800 border-gray-200";
      case ConnectionStatus.INVALID_TOKEN:
        return "bg-red-100 text-red-800 border-red-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getBorderClasses = (status: ConnectionStatus) => {
    switch (status) {
      case ConnectionStatus.CONNECTED:
        return "border-green-200";
      case ConnectionStatus.NOT_CONNECTED:
        return "border-gray-200";
      case ConnectionStatus.INVALID_TOKEN:
        return "border-red-200";
      default:
        return "border-gray-200";
    }
  };

  return (
    <Card className={`border ${getBorderClasses(status)} p-2 w-80`}>
      <CardContent className="px-1 py-1">
        <div>{modelName}</div>
        
        <div className="grid grid-cols-2 gap-4 mt-4">
          <div>
            <h3 className="font-semibold text-sm text-gray-700 mb-2">Tests</h3>
            <div className="space-y-1">
              <div className="text-sm text-gray-600">{tests[0]}</div>
              <div className="text-sm text-gray-500 h-5">
                {tests.length > 1 ? `+${tests.length - 1} more` : '\u00A0'}
              </div>
            </div>
          </div>
          <div>
            <h3 className="font-semibold text-sm text-gray-700 mb-2">Status</h3>
            <Badge className={getBadgeClasses(status)}>
              {status}
            </Badge>
          </div>
        </div>
        
        <div className="mt-4 flex justify-start">
          <Button size="sm" className="text-xs" onClick={onConnect}>
            Connect
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

// Helper function to render multiple endpoint status cards in a 2-column grid
const renderEndpointStatusCardsGrid = (endpoints: Array<{modelName: string, status: ConnectionStatus, tests: string[]}>, onConnect: () => void) => {
  return (
    <div className="max-h-[400px] overflow-y-auto">
      <div className="grid grid-cols-2 gap-4">
        {endpoints.map((endpoint, index) => (
          <div key={index}>
            {renderEndpointStatusCard(endpoint.modelName, endpoint.status, endpoint.tests, onConnect)}
          </div>
        ))}
      </div>
    </div>
  );
};

export default function RequiredEndpointsCard() {
  const [isEditModelSheetOpen, setIsEditModelSheetOpen] = React.useState(false);
  
  // Get the first provider and model config from MockData
  const firstProvider = providers[0]; // OpenAI provider
  const firstModel = models[0]; // GPT-4 model
  
  const handleConnect = () => {
    setIsEditModelSheetOpen(true);
  };

  const endpoints = [
    {
      modelName: "together-llama-guard-8b-assistant",
      status: ConnectionStatus.CONNECTED,
      tests: ["MMLU2.0"]
    },
    {
      modelName: "another-model-example",
      status: ConnectionStatus.NOT_CONNECTED,
      tests: ["HellaSwag", "ARC"]
    },
    {
      modelName: "together-llama-guard-8b-assistant",
      status: ConnectionStatus.CONNECTED,
      tests: ["MMLU2.0"]
    },
    {
      modelName: "another-model-example",
      status: ConnectionStatus.NOT_CONNECTED,
      tests: ["HellaSwag", "ARC"]
    },
    {
      modelName: "together-llama-guard-8b-assistant",
      status: ConnectionStatus.CONNECTED,
      tests: ["MMLU2.0"]
    },
    {
      modelName: "another-model-example",
      status: ConnectionStatus.NOT_CONNECTED,
      tests: ["HellaSwag", "ARC","TriviaQA"]
    }
  ];

  return (
    <>
      <Card className="w-3xl mt-6 py-1">
        <Accordion type="single" collapsible>
          <AccordionItem value="item-1">
            <AccordionTrigger className="flex flex-row items-center hover:no-underline px-6 py-4">
              <div className="flex-1">
                <CardTitle data-testid="additional-card-title">Connect Required Endpoints</CardTitle>
                <CardDescription data-testid="additional-card-description">
                  Make sure you configure access to the required models to run selected recipes.
                </CardDescription>
              </div>
              {/* Status indicators */}
              <div className="flex items-center">
                <CircleCheckBig className="h-5 w-5 text-green-500" data-testid="required-endpoints-status-indicator" />
              </div>
            </AccordionTrigger>
            <AccordionContent>
              <CardContent>
                {renderEndpointStatusCardsGrid(endpoints, handleConnect)}
              </CardContent>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </Card>
      
      <EditModelSheet
        open={isEditModelSheetOpen}
        onOpenChange={setIsEditModelSheetOpen}
        editingModel={firstModel.id}
        providers={providers}
        models={models}
        isMetricEndpoint={true}
      />
    </>
  );
}

export { ConnectionStatus };

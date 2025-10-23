"use client"
import React, { useState } from 'react';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Card, CardContent, CardDescription, CardTitle } from '@/components/ui/card';
import { CircleCheckBig } from 'lucide-react';
import { useBundlesRedux } from '../../../hooks/useBundlesRedux';



interface BenchmarkSidebarProps {
  currentPage: 'bundle-selection' | 'model-selection';
}

interface AccordionTestData {
  id: string;
  title: string;
  status: 'pending' | 'completed';
}

interface BundleAccordionData {
  id: string;
  title: string;
  items: AccordionTestData[];
  get count(): string;
}

export default function BenchmarkSidebar({ currentPage }: BenchmarkSidebarProps) {
  const { bundles, loading, error } = useBundlesRedux();
  
  const [checkedItems, setCheckedItems] = useState({
    mmlu: false,
    singaporeTF: false,
    singaporeMCQ: false
  });

  const handleCheckChange = (key: keyof typeof checkedItems) => {
    setCheckedItems(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const createTestAccordionItem = (data: AccordionTestData) => (
    <Card key={data.id} className="w-full mt-2 py-1 rounded-sm">
      <Accordion type="single" collapsible>
        <AccordionItem value={data.id} className="border-none">
          <div className="flex items-center px-2 py-1">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <Checkbox 
                  checked={checkedItems[data.id as keyof typeof checkedItems]}
                  onCheckedChange={() => handleCheckChange(data.id as keyof typeof checkedItems)}
                  className="rounded-sm"
                />
                <CardTitle className="text-sm font-medium">{data.title}</CardTitle>
              </div>
            </div>
            {/* Status indicators */}
            <div className="flex items-center gap-2">
              <CircleCheckBig className={`h-5 w-5 ${
                data.status === 'completed' 
                  ? 'text-green-500' 
                  : 'text-gray-300'
              }`} />
              <AccordionTrigger className="hover:no-underline p-0">
                <span className="sr-only">Toggle {data.title} details</span>
              </AccordionTrigger>
            </div>
          </div>
          <AccordionContent>
            <CardContent className="px-6 py-4">
              <div className="space-y-3">
                {/* Content for this accordion item can go here */}
                <div className="text-sm text-gray-600">
                  Details for {data.title} will be displayed here when expanded.
                </div>
              </div>
            </CardContent>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </Card>
  );

  const createParentAccordion = (data: BundleAccordionData) => (
    <AccordionItem key={data.id} value={data.id} className="border-none">
      <div className="flex items-center">
        <Badge variant="outline" className="flex items-center gap-2 px-3 py-2">
          <Checkbox 
            checked={false}
            className="rounded-sm"
          />
          <span className="font-medium text-sm">{data.title} {data.count}</span>
        </Badge>
        <Separator orientation="horizontal" className="flex-1 mx-2" />
        <AccordionTrigger className="hover:no-underline">
          <span className="sr-only">Toggle {data.title} section</span>
        </AccordionTrigger>
      </div>
      {/* px4 causes the tab for the accordion content*/}
      <AccordionContent className="px-4">
        <div>
          {data.items.map((item) => createTestAccordionItem(item))}
        </div>
      </AccordionContent>
    </AccordionItem>
  );

  // Data for parent accordion with nested items
  const parentAccordionData: BundleAccordionData[] = [
    {
      id: 'hallucination',
      title: 'Hallucination',
      items: [
        {
          id: 'mmlu',
          title: 'MMLU 2.0',
          status: 'pending'
        },
        {
          id: 'singaporeTF',
          title: 'Facts about Singapore TF',
          status: 'completed'
        },
        {
          id: 'singaporeMCQ',
          title: 'Facts about Singapore MCQ',
          status: 'completed'
        }
      ],
      get count() {
        return `[${this.items.length}/${this.items.length}]`;
      }
    }
  ];

  return (
    <div 
      style={{
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-start',
        padding: '121px 24px 16px',
        gap: '8px',
        isolation: 'isolate',
        position: 'fixed',
        width: '385px',
        height: '100vh',
        right: '0px',
        top: '0px',
        background: '#F8FAFC',
        borderLeft: '1px solid #E2E8F0'
      }}
    >
      <div className="w-full max-w-md mx-auto p-1">
        <Accordion type="single" collapsible>
          {parentAccordionData.map((data) => createParentAccordion(data))}
        </Accordion>
      </div>
      {/* Sidebar content goes here */}
    </div>
  );
}

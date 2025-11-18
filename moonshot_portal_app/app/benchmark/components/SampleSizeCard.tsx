"use client"
import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { CircleCheckBig, CircleAlert } from 'lucide-react';
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { Button } from "@/components/ui/button";
import { Check, ChevronsUpDown } from "lucide-react";
import { cn } from "@/lib/utils";
import {
    Accordion,
    AccordionContent,
    AccordionItem,
    AccordionTrigger,
  } from "@/components/ui/accordion"
import { Toggle } from '@/components/ui/toggle';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { useAppSelector } from '@/hooks/reduxHooks';

const CONSTANTS = {
  MINIMUM_SAMPLE_SIZE: 5,
  DEFAULT_TOTAL_PROMPTS: 2952,
  DEFAULT_CONFIDENCE_LEVEL: 95,
  DEFAULT_MARGIN_OF_ERROR: 3,
  DEFAULT_EXPECTED_PROPORTION: 90
} as const;

/**
 * Calculate the required sample size for a proportion.
 * We are using the formula:
 * n = (Z² × p × (1-p)) / E²
 * where:
 * - Z is the Z-score for the confidence level
 * - p is the expected proportion
 * - E is the margin of error
 * - n is the sample size
 * 
 * @param confidenceLevel - Confidence level as a percentage (e.g., 95 for 95%)
 * @param marginOfError - Margin of error as a percentage (e.g., 5 for 5%)
 * @param expectedProportion - Expected proportion as a decimal between 0 and 1 (default: 0.5)
 * @returns Required sample size (rounded up)
 * 
 * @example
 * calculateSampleSize(95, 5, 0.5) // Returns 385
 */
export function calculateSampleSize(
    confidenceLevel: number,
    marginOfError: number,
    expectedProportion: number
  ): number {
    // Z-scores for common confidence levels
    const zScores: Record<number, number> = {
      50: 0.674,
      60: 0.842,
      70: 1.036,
      80: 1.282,
      90: 1.645,
      95: 1.96,
      99: 2.576
    };
  
    // Get Z-score
    const z = zScores[confidenceLevel];
    if (z === undefined) {
      throw new Error(
        `Confidence level ${confidenceLevel}% not supported. Use: ${Object.keys(zScores).join(', ')}`
      );
    }
  
    // Convert margin of error from percentage to decimal
    const e = marginOfError / 100;
  
    // Validate expected proportion
    if (expectedProportion < 0 || expectedProportion > 1) {
      throw new Error('Expected proportion must be between 0 and 1');
    }
  
    // Calculate sample size: n = (Z² × p × (1-p)) / E²
    const n = (Math.pow(z, 2) * expectedProportion * (1 - expectedProportion)) / Math.pow(e, 2);

    /*
    // Step 2: Apply finite population correction
    // Formula: n_finite = n_infinite / (1 + (n_infinite - 1) / N)
    // where N = population size
    const N = populationSize;
    const sampleSizeFinite = Math.ceil(sampleSizeInfinite / (1 + (sampleSizeInfinite - 1) / N));
    
    // Ensure sample size doesn't exceed population size
    const finalSampleSize = Math.min(sampleSizeFinite, populationSize);
    
    return finalSampleSize;
    */

    // Round up to nearest integer
    return Math.ceil(n);
  }

export default function SampleSizeCard() {
  const [populationMeanOpen, setPopulationMeanOpen] = React.useState(false);
  const [confidenceLevelOpen, setConfidenceLevelOpen] = React.useState(false);
  const [marginOfErrorOpen, setMarginOfErrorOpen] = React.useState(false);
  
  const [selectedPopulationMean, setSelectedPopulationMean] = React.useState(CONSTANTS.DEFAULT_EXPECTED_PROPORTION.toString());
  const [selectedConfidenceLevel, setSelectedConfidenceLevel] = React.useState(CONSTANTS.DEFAULT_CONFIDENCE_LEVEL.toString());
  const [selectedMarginOfError, setSelectedMarginOfError] = React.useState(CONSTANTS.DEFAULT_MARGIN_OF_ERROR.toString());
  const [selectedToggleValue, setSelectedToggleValue] = React.useState("recommended");

  // Get bundles and test selection to calculate total prompts
  const bundles = useAppSelector((state) => state.bundles.data);
  const testSelection = useAppSelector((state) => state.testSelection);

  // Calculate total number of prompts from selected tests
  const totalPromptsFromSelectedTests = React.useMemo(() => {
    let total = 0;
    bundles.forEach(bundle => {
      bundle.tests.forEach(test => {
        if (testSelection[test.name]) {
          total += test.dataset?.num_of_dataset_prompts ?? 0;
        }
      });
    });
    return total;
  }, [bundles, testSelection]);

  // Calculate number of selected tests
  const numberOfSelectedTests = React.useMemo(() => {
    return Object.values(testSelection).filter(isSelected => isSelected).length;
  }, [testSelection]);

  // Calculate recommended sample size based on selected values
  const calculateRecommendedSampleSize = () => {
    try {
      const confidenceLevel = parseInt(selectedConfidenceLevel);
      const marginOfError = parseInt(selectedMarginOfError);
      const populationMean = parseInt(selectedPopulationMean) / 100; // Convert to decimal
      
      return calculateSampleSize(confidenceLevel, marginOfError, populationMean);
    } catch (error) {
      return 0;
    }
  };

  const recommendedSampleSize = calculateRecommendedSampleSize();

  // Handle toggle selection
  const handleToggleChange = (value: string) => {
    setSelectedToggleValue(value);
  };

  const populationMeanOptions = [
    { value: "95", label: "95%" },
    { value: "90", label: "90% (Recommended)" },
    { value: "80", label: "80%" },
    { value: "70", label: "70%" },
    { value: "60", label: "60%" },
    { value: "50", label: "50%" }
  ];

  const confidenceLevelOptions = [
    { value: "99", label: "99%" },
    { value: "95", label: "95% (Recommended)" },
    { value: "90", label: "90%" }
  ];

  const marginOfErrorOptions = [
    { value: "5", label: "5%" },
    { value: "4", label: "4%" },
    { value: "3", label: "3% (Recommended)" },
    { value: "2", label: "2%" },
    { value: "1", label: "1%" }
  ];

  return (
    <>
      <Card className="w-3xl mt-6 py-1">
        <Accordion type="single" collapsible defaultValue="item-1">
          <AccordionItem value="item-1">
            <AccordionTrigger className="flex flex-row items-center hover:no-underline px-6 py-4">
              <div className="flex-1">
                <CardTitle data-testid="sample-size-card-title">Configure Sample Size</CardTitle>
                <CardDescription data-testid="sample-size-card-description">
                  Review and adjust the sample size for each test to ensure reliable results.
                </CardDescription>
              </div>
              {/* Status indicators */}
              <div className="flex items-center">
                {selectedToggleValue === "test" ? (
                  <CircleAlert className="h-5 w-5 text-orange-200" data-testid="sample-size-status-indicator" />
                ) : (
                  <CircleCheckBig className="h-5 w-5 text-green-500" data-testid="sample-size-status-indicator" />
                )}
              </div>
            </AccordionTrigger>
            <AccordionContent>
              <CardContent>
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="population-mean">Population Mean</Label>
                    <Popover open={populationMeanOpen} onOpenChange={setPopulationMeanOpen}>
                      <PopoverTrigger asChild>
                        <Button
                          variant="outline"
                          role="combobox"
                          aria-expanded={populationMeanOpen}
                          className="w-full justify-between"
                          data-testid="population-mean-combobox-trigger"
                        >
                          {selectedPopulationMean}%
                          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-full p-0" align="start">
                        <Command>
                          <CommandInput placeholder="Search population mean..." />
                          <CommandList>
                            <CommandEmpty>No option found.</CommandEmpty>
                            <CommandGroup>
                              {populationMeanOptions.map((option) => (
                                <CommandItem
                                  key={option.value}
                                  value={option.value}
                                  onSelect={(currentValue) => {
                                    setSelectedPopulationMean(currentValue);
                                    setPopulationMeanOpen(false);
                                  }}
                                  data-testid={`population-mean-option-${option.value}`}
                                >
                                  <Check
                                    className={cn(
                                      "mr-2 h-4 w-4",
                                      selectedPopulationMean === option.value ? "opacity-100" : "opacity-0"
                                    )}
                                  />
                                  {option.label}
                                </CommandItem>
                              ))}
                            </CommandGroup>
                          </CommandList>
                        </Command>
                      </PopoverContent>
                    </Popover>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="confidence-level">Confidence Level</Label>
                    <Popover open={confidenceLevelOpen} onOpenChange={setConfidenceLevelOpen}>
                      <PopoverTrigger asChild>
                        <Button
                          variant="outline"
                          role="combobox"
                          aria-expanded={confidenceLevelOpen}
                          className="w-full justify-between"
                          data-testid="confidence-level-combobox-trigger"
                        >
                          {selectedConfidenceLevel}%
                          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-full p-0" align="start">
                        <Command>
                          <CommandInput placeholder="Search confidence level..." />
                          <CommandList>
                            <CommandEmpty>No option found.</CommandEmpty>
                            <CommandGroup>
                              {confidenceLevelOptions.map((option) => (
                                <CommandItem
                                  key={option.value}
                                  value={option.value}
                                  onSelect={(currentValue) => {
                                    setSelectedConfidenceLevel(currentValue);
                                    setConfidenceLevelOpen(false);
                                  }}
                                  data-testid={`confidence-level-option-${option.value}`}
                                >
                                  <Check
                                    className={cn(
                                      "mr-2 h-4 w-4",
                                      selectedConfidenceLevel === option.value ? "opacity-100" : "opacity-0"
                                    )}
                                  />
                                  {option.label}
                                </CommandItem>
                              ))}
                            </CommandGroup>
                          </CommandList>
                        </Command>
                      </PopoverContent>
                    </Popover>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="margin-of-error">Margin of Error</Label>
                    <Popover open={marginOfErrorOpen} onOpenChange={setMarginOfErrorOpen}>
                      <PopoverTrigger asChild>
                        <Button
                          variant="outline"
                          role="combobox"
                          aria-expanded={marginOfErrorOpen}
                          className="w-full justify-between"
                          data-testid="margin-of-error-combobox-trigger"
                        >
                          {selectedMarginOfError}%
                          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-full p-0" align="start">
                        <Command>
                          <CommandInput placeholder="Search margin of error..." />
                          <CommandList>
                            <CommandEmpty>No option found.</CommandEmpty>
                            <CommandGroup>
                              {marginOfErrorOptions.map((option) => (
                                <CommandItem
                                  key={option.value}
                                  value={option.value}
                                  onSelect={(currentValue) => {
                                    setSelectedMarginOfError(currentValue);
                                    setMarginOfErrorOpen(false);
                                  }}
                                  data-testid={`margin-of-error-option-${option.value}`}
                                >
                                  <Check
                                    className={cn(
                                      "mr-2 h-4 w-4",
                                      selectedMarginOfError === option.value ? "opacity-100" : "opacity-0"
                                    )}
                                  />
                                  {option.label}
                                </CommandItem>
                              ))}
                            </CommandGroup>
                          </CommandList>
                        </Command>
                      </PopoverContent>
                    </Popover>
                  </div>
                </div>
                
                {/* Recommended Sample Size Alert */}
                <div className="mt-4">
                  <Alert className="border-blue-200 bg-blue-50">
                    <AlertDescription className="flex justify-between items-center">
                      <span>Recommended sample size: {recommendedSampleSize} prompts</span>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <span className="text-blue-600 hover:text-blue-800 cursor-pointer">How Is it Calculated?</span>
                        </TooltipTrigger>
                        <TooltipContent className="max-w-lg w-max px-3">
                          <div className="space-y-2">
                            <p className="font-bold">How is it calculated:</p>
                            <ul className="list-disc list-inside space-y-1">
                              <li>Sample size calculation assumes binomial distribution.</li>
                              <li>If the benchmark dataset contains fewer prompts than the recommended size, the full size of the dataset will be used instead.</li>
                            </ul>
                            <p className="font-bold">Actual confidence interval of the test results may differ due to the following:</p>
                            <ul className="list-disc list-inside space-y-1">
                              <li>Actual test score can be different from the population mean assumed.</li>
                              <li className="whitespace-nowrap">Margin of error will include additional measurement error due to non-determinism in LLM output.</li>
                            </ul>
                          </div>
                        </TooltipContent>
                      </Tooltip>
                    </AlertDescription>
                  </Alert>
                </div>

                <div className="flex items-center gap-3 mt-4">
                  <Label className="text-sm font-medium">Select:</Label>
                  <div className="flex gap-2">
                    {[
                      { value: "calculated", label: "Calculated", count: `(${recommendedSampleSize})` },
                      { value: "test", label: "Test Run", count: `(${numberOfSelectedTests})` },
                      { value: "all", label: "All prompts", count: `(${totalPromptsFromSelectedTests})` }
                    ].map((toggle) => (
                      <Toggle
                        key={toggle.value}
                        pressed={selectedToggleValue === toggle.value}
                        onPressedChange={(pressed) => {
                          if (pressed) {
                            handleToggleChange(toggle.value);
                          }
                        }}
                        variant="outline"
                        className={cn(
                          "transition-all duration-200",
                          selectedToggleValue === toggle.value 
                            ? "scale-100 px-3 py-2" 
                            : "scale-85 px-2 py-1.5"
                        )}
                      >
                        {toggle.label} <span className="text-muted-foreground">{toggle.count}</span>
                      </Toggle>
                    ))}
                  </div>
                </div>

                {/* Minimum Selection Alert - Only shows when minimum is selected */}
                {selectedToggleValue === "test" && (
                  <div className="mt-4">
                    <Alert className="border-orange-200 bg-orange-50">
                      <AlertDescription>
                        Your Sample size is smaller than recommended. This may generate unreliable test results. Proceed with caution.
                      </AlertDescription>
                    </Alert>
                  </div>
                )}
              </CardContent>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </Card>
    </>
  );
}


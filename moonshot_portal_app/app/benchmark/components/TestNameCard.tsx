"use client"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Card, CardContent, CardDescription, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { CircleAlert, CircleCheckBig } from "lucide-react";
import { useAppDispatch, useAppSelector } from "@/hooks/reduxHooks";
import { useTestNameValidation } from "@/hooks/useTestNameValidation";
import { setBenchmarkTestName } from "@/store";
import { useState } from "react";

export default function TestNameCard() {
  const dispatch = useAppDispatch();
  const testName = useAppSelector(state => state.modelSelection.testName);
  const { isTestNameValid, errorMessage, isChecking } = useTestNameValidation();
  const [hasBeenTouched, setHasBeenTouched] = useState(false);

  const handleTestNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setHasBeenTouched(true);
    dispatch(setBenchmarkTestName(e.target.value));
  };

  const showError = hasBeenTouched && !isChecking && Boolean(errorMessage);

  return (
    <>       
      <Card className="w-3xl mb-6 py-1" data-testid="test-name-card">
        <Accordion type="single" collapsible defaultValue="item-1">
          <AccordionItem value="item-1">
            <AccordionTrigger className="flex flex-row items-center hover:no-underline px-6 py-4">
              <div className="flex-1">
                <CardTitle data-testid="additional-card-title">Fill in Test Name</CardTitle>
                <CardDescription data-testid="additional-card-description">
                  Provide a name for your benchmark test.
                </CardDescription>
              </div>
              {/* Status indicators */}
              <div className="flex items-center">
                {!isTestNameValid && (
                  <CircleAlert className="h-5 w-5 text-red-500" data-testid="test-name-status-indicator" />
                )}
                {isTestNameValid && (
                  <CircleCheckBig className="h-5 w-5 text-green-500" data-testid="test-name-status-indicator" />
                )}
              </div>
            </AccordionTrigger>
            <AccordionContent>
              <CardContent>
                <div className="mb-2">
                  <Label htmlFor="test-name-input">Test Name *</Label>
                </div>
                <Input 
                  type="text" 
                  placeholder="Test Name" 
                  id="test-name-input"
                  data-testid="test-name-input"
                  value={testName}
                  onChange={handleTestNameChange}
                  aria-invalid={showError ? "true" : undefined}
                />
                {showError && errorMessage && (
                  <p className="text-sm text-red-600 mt-1" data-testid="test-name-error">
                    {errorMessage}
                  </p>
                )}
              </CardContent>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </Card>
    </>
  );
}

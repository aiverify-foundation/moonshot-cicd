"use client"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Card, CardContent, CardDescription, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { CircleAlert, CircleCheckBig } from "lucide-react";
import { useAppDispatch, useAppSelector } from "@/hooks/reduxHooks";
import { setTestNameFilled } from "@/store";
import { useState } from "react";

export default function TestNameAndDescriptionCard() {
  const dispatch = useAppDispatch();
  const isTestNameValid = useAppSelector(state => state.modelSelection.isTestNameValid);
  const [hasBeenTouched, setHasBeenTouched] = useState(false);

  const handleTestNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.trim();
    setHasBeenTouched(true);

    // dispatch(setTestNameFilled(value.length > 0));
    dispatch(setTestNameFilled(true));
  };

  // Only show error if field has been touched AND validation is invalid
  const showError = hasBeenTouched && !isTestNameValid;

  return (
    <>       
      <Card className="w-3xl mb-6 py-1" data-testid="test-name-and-description-card">
        <Accordion type="single" collapsible defaultValue="item-1">
          <AccordionItem value="item-1">
            <AccordionTrigger className="flex flex-row items-center hover:no-underline px-6 py-4">
              <div className="flex-1">
                <CardTitle data-testid="additional-card-title">Fill in Test Name and Description</CardTitle>
                <CardDescription data-testid="additional-card-description">
                  Provide a name and description for your benchmark test.
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
                  onChange={handleTestNameChange}
                  aria-invalid={showError ? "true" : undefined}
                />
                {showError && (
                  <p className="text-sm text-red-600 mt-1">This field has an error</p>
                )}
                <div className="mt-4 mb-2">
                  <Label htmlFor="test-description-input">Test Description</Label>
                </div>
                <Input type="text" placeholder="Test Description" id="test-description-input" data-testid="test-description-input" />
              </CardContent>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </Card>
    </>
  );
}


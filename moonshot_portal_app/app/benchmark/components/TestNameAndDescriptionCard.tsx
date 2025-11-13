"use client"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Card, CardContent, CardDescription, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { CircleAlert, CircleCheckBig } from "lucide-react";
import { useAppDispatch, useAppSelector } from "@/hooks/reduxHooks";
import { setTestNameFilled } from "@/store";

export default function TestNameAndDescriptionCard() {
  const dispatch = useAppDispatch();
  const isTestNameFilled = useAppSelector(state => state.modelSelection.isTestNameFilled);

  const handleTestNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.trim();
    dispatch(setTestNameFilled(value.length > 0));
  };

  return (
    <>       
      <Card className="w-3xl mb-6 py-1">
        <Accordion type="single" collapsible>
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
                {!isTestNameFilled && (
                  <CircleAlert className="h-5 w-5 text-red-500" data-testid="required-endpoints-status-indicator" />
                )}
                {isTestNameFilled && (
                  <CircleCheckBig className="h-5 w-5 text-green-500" data-testid="required-endpoints-status-indicator" />
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
                  data-testid="test-name-input"
                  onChange={handleTestNameChange}
                />
                <div className="mt-4 mb-2">
                  <Label htmlFor="test-description-input">Test Description</Label>
                </div>
                <Input type="text" placeholder="Test Description" data-testid="test-description-input" />
              </CardContent>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </Card>
    </>
  );
}


"use client"
import React from "react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  ApiError,
  fetchProviderLatestDetails,
  setLlmProviderApiKey,
  type LlmProviderDetailsDTO,
} from "../../../lib/api";
import { useAppDispatch } from "../../../hooks/reduxHooks";
import { setEndpointStatus } from "../../../store";
import type { Provider } from "../types/modelSelection";

/** Matches `ConnectionStatus.CONNECTED` in Redux `endpointStatus` slice. */
const ENDPOINT_STATUS_CONNECTED = "connected";

const TEST_POPOVER_TIMEOUT_MS = 3000;

const resolveSystemName = (provider: Provider | null): string => {
  if (!provider) return "";
  return (provider.system_name ?? provider.id).trim();
};

const resolveProviderIdNumeric = (
  details: LlmProviderDetailsDTO,
  provider: Provider
): number => {
  if (/^\d+$/.test(provider.id)) {
    return parseInt(provider.id, 10);
  }
  return parseInt(details.provider.id, 10);
};

export interface EditLlmAajProviderSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Resolved judge provider from `GET /api/providers` (same row as required-endpoints card). */
  provider: Provider | null;
  /** Redux `endpointStatus` key, e.g. `aaj:together_adapter`. */
  endpointStatusKey: string | null;
  onSaved?: () => void | Promise<void>;
}

/**
 * Minimal sheet for LLM-as-judge providers: set API token only.
 * Layout and provider/token behavior follow {@link EditModelSheet}.
 */
export default function EditLlmAajProviderSheet({
  open,
  onOpenChange,
  provider,
  endpointStatusKey,
  onSaved,
}: EditLlmAajProviderSheetProps) {
  const dispatch = useAppDispatch();
  const [tokenValue, setTokenValue] = React.useState("");
  const [apiKeyConfigured, setApiKeyConfigured] = React.useState(false);
  const [saving, setSaving] = React.useState(false);
  /** Test always succeeds when clicked (same pattern as {@link EditModelSheet}). */
  const [testResult, setTestResult] = React.useState<boolean | null>(null);
  const [popoverOpen, setPopoverOpen] = React.useState(false);
  const testPopoverTimeoutRef = React.useRef<NodeJS.Timeout | null>(null);

  React.useEffect(() => {
    if (!open) {
      setTokenValue("");
      setApiKeyConfigured(false);
      setTestResult(null);
      setPopoverOpen(false);
      return;
    }
    if (!provider) return;
    const systemName = resolveSystemName(provider);
    if (!systemName) return;
    let cancelled = false;
    void (async () => {
      try {
        const details = await fetchProviderLatestDetails(systemName);
        if (cancelled) return;
        setApiKeyConfigured(Boolean(details.api_key_configured));
      } catch {
        if (!cancelled) setApiKeyConfigured(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [open, provider]);

  React.useEffect(() => {
    if (open) {
      setTestResult(null);
    }
  }, [open]);

  React.useEffect(() => {
    return () => {
      if (testPopoverTimeoutRef.current) {
        clearTimeout(testPopoverTimeoutRef.current);
      }
    };
  }, []);

  const dispatchEndpointConnected = () => {
    const statusKey = endpointStatusKey?.trim();
    if (statusKey) {
      dispatch(
        setEndpointStatus({
          configId: statusKey,
          status: ENDPOINT_STATUS_CONNECTED,
        })
      );
    }
  };

  const handleTest = () => {
    setTestResult(true);
    dispatchEndpointConnected();

    setPopoverOpen(true);
    if (testPopoverTimeoutRef.current) {
      clearTimeout(testPopoverTimeoutRef.current);
    }
    testPopoverTimeoutRef.current = setTimeout(() => {
      setPopoverOpen(false);
    }, TEST_POPOVER_TIMEOUT_MS);
  };

  const handleSave = async () => {
    if (testResult !== true) return;
    if (!provider) {
      window.alert("No provider selected.");
      return;
    }
    const systemName = resolveSystemName(provider);
    if (!systemName) {
      window.alert("Missing provider system name.");
      return;
    }
    setSaving(true);
    try {
      const details = await fetchProviderLatestDetails(systemName);
      const providerId = resolveProviderIdNumeric(details, provider);
      const keyConfigured = Boolean(details.api_key_configured);
      const trimmedToken = tokenValue.trim();
      if (!keyConfigured && !trimmedToken) {
        window.alert(
          "Enter a token for this provider (no API key is stored yet)."
        );
        return;
      }
      if (trimmedToken) {
        await setLlmProviderApiKey(providerId, trimmedToken);
      }
      dispatchEndpointConnected();
      await onSaved?.();
      setTokenValue("");
      onOpenChange(false);
    } catch (e) {
      const msg =
        e instanceof ApiError
          ? e.message
          : e instanceof Error
            ? e.message
            : "Save failed";
      window.alert(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="w-[1400px] sm:max-w-[700px] ml-4 overflow-y-auto pl-6 pr-6"
      >
        <SheetHeader className="text-left space-y-1">
          <SheetTitle className="text-lg font-semibold">
            Add Provider Token
          </SheetTitle>
          <SheetDescription className="sr-only">
            Store or update the API token for the LLM-as-judge provider.
          </SheetDescription>
        </SheetHeader>

        <div className="flex flex-col mt-6">
          <div className="flex-1 space-y-6 pb-6">
            <Card className="py-0 gap-0">
              <CardContent className="p-4 space-y-4">
                <div className="space-y-2">
                  <Label className="text-sm font-medium">Model Provider*</Label>
                  <div className="text-sm px-3 py-2 rounded-md border text-gray-700 bg-gray-50">
                    {provider?.name || "No provider selected"}
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Label htmlFor="aaj-provider-token" className="text-sm font-medium">
                      {apiKeyConfigured ? "Token (optional)" : "Token*"}
                    </Label>
                  </div>
                  <Input
                    id="aaj-provider-token"
                    placeholder={
                      apiKeyConfigured && !tokenValue
                        ? "••••••••"
                        : "Enter token"
                    }
                    type="password"
                    value={tokenValue}
                    onChange={(e) => setTokenValue(e.target.value)}
                    autoComplete="off"
                  />
                  {apiKeyConfigured ? (
                    <p className="text-sm text-gray-600">
                      Your token has already been saved. No further action is
                      needed unless you would like to replace it with a new one.
                    </p>
                  ) : null}
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="mt-auto pt-6 pb-6 border-t">
            <div className="flex justify-between items-center">
              <Button
                variant="outline"
                onClick={() => {
                  setTokenValue("");
                  setTestResult(null);
                  onOpenChange(false);
                }}
              >
                Back
              </Button>
              <div className="flex gap-3">
                <Popover open={popoverOpen} onOpenChange={setPopoverOpen}>
                  <PopoverTrigger asChild>
                    <Button variant="outline" type="button" onClick={handleTest}>
                      Test_Placeholder
                    </Button>
                  </PopoverTrigger>
                  {testResult !== null && (
                    <PopoverContent className="bg-background border-2 border-gray-300 text-foreground shadow-lg w-auto max-w-fit p-2">
                      <p className={testResult ? "text-green-600" : "text-red-600"}>
                        {testResult ? "Test Passed" : "Test Failed"}
                      </p>
                    </PopoverContent>
                  )}
                </Popover>
                <Button
                  onClick={() => void handleSave()}
                  disabled={saving || testResult !== true}
                  className={
                    saving || testResult !== true
                      ? "opacity-50 bg-gray-100 text-gray-400"
                      : ""
                  }
                >
                  {saving ? "Saving…" : "Save"}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}

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
import {
  ApiError,
  fetchProviderLatestDetails,
  setLlmProviderApiKey,
  testLlmProviderConnection,
  type LlmProviderDetailsDTO,
} from "../../../lib/api";
import { useAppDispatch } from "../../../hooks/reduxHooks";
import { setEndpointStatus } from "../../../store";
import type { Provider } from "../types/modelSelection";

/** Matches `ConnectionStatus.CONNECTED` in Redux `endpointStatus` slice. */
const ENDPOINT_STATUS_CONNECTED = "connected";
/** Matches `ConnectionStatus.NOT_CONNECTED` in Redux `endpointStatus` slice. */
const ENDPOINT_STATUS_NOT_CONNECTED = "not connected";

export function buildAajConnectionTestFingerprint(token: string): string {
  return JSON.stringify({ token: token.trim() });
}

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
  const [testing, setTesting] = React.useState(false);
  const [testResult, setTestResult] = React.useState<boolean | null>(null);
  const [testError, setTestError] = React.useState<string | null>(null);
  const [testedFingerprint, setTestedFingerprint] = React.useState<string | null>(
    null
  );

  const currentFingerprint = buildAajConnectionTestFingerprint(tokenValue);
  const canSave =
    testedFingerprint !== null &&
    testedFingerprint === currentFingerprint;

  const clearConnectionTestSuccess = React.useCallback(() => {
    setTestResult(null);
    setTestError(null);
    setTestedFingerprint(null);
    const statusKey = endpointStatusKey?.trim();
    if (statusKey) {
      dispatch(
        setEndpointStatus({
          configId: statusKey,
          status: ENDPOINT_STATUS_NOT_CONNECTED,
        })
      );
    }
  }, [dispatch, endpointStatusKey]);

  React.useEffect(() => {
    if (!open) {
      setTokenValue("");
      setApiKeyConfigured(false);
      setTestResult(null);
      setTestError(null);
      setTestedFingerprint(null);
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
      setTestError(null);
      setTestedFingerprint(null);
    }
  }, [open]);

  React.useEffect(() => {
    if (testedFingerprint == null) return;
    if (testedFingerprint !== currentFingerprint) {
      clearConnectionTestSuccess();
    }
  }, [testedFingerprint, currentFingerprint, clearConnectionTestSuccess]);

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

  const handleTest = async () => {
    if (!provider) {
      window.alert("No provider selected.");
      return;
    }
    const systemName = resolveSystemName(provider);
    if (!systemName) {
      window.alert("Missing provider system name.");
      return;
    }
    const modelName = (provider.defaultModel || "").trim();
    if (!modelName) {
      window.alert("Provider has no default model to test against.");
      return;
    }
    const trimmedToken = tokenValue.trim();
    if (!apiKeyConfigured && !trimmedToken) {
      window.alert("Enter a token before testing the connection.");
      return;
    }

    const fingerprint = buildAajConnectionTestFingerprint(trimmedToken);
    setTesting(true);
    setTestResult(null);
    setTestError(null);
    setTestedFingerprint(null);
    try {
      const details = await fetchProviderLatestDetails(systemName);
      const providerId = resolveProviderIdNumeric(details, provider);
      const result = await testLlmProviderConnection({
        llm_provider_id: providerId,
        model_name: modelName,
        savedConfigPairs: {},
        api_key: trimmedToken || undefined,
      });
      setTestResult(result.success);
      setTestError(result.success ? null : result.error || "Connection test failed");
      setTestedFingerprint(fingerprint);
      if (result.success) {
        dispatchEndpointConnected();
      }
    } catch (e) {
      const msg =
        e instanceof ApiError
          ? e.message
          : e instanceof Error
            ? e.message
            : "Connection test failed";
      setTestResult(false);
      setTestError(msg);
      setTestedFingerprint(fingerprint);
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    if (!canSave) return;
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
      setTestedFingerprint(null);
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
        className="w-[1400px] sm:max-w-[700px] ml-4 pl-6 pr-6 flex flex-col overflow-hidden"
        data-testid="edit-aaj-provider-sheet"
      >
        <div className="flex flex-col flex-1 min-h-0">
          <div className="flex-1 min-h-0 overflow-y-auto space-y-6 pb-6">
            <SheetHeader className="text-left space-y-1 p-0">
              <SheetTitle
                className="text-lg font-semibold"
                data-testid="edit-aaj-provider-sheet-title"
              >
                Add Provider Token
              </SheetTitle>
              <SheetDescription className="sr-only">
                Store or update the API token for the LLM-as-judge provider.
              </SheetDescription>
            </SheetHeader>

            <Card className="py-0 gap-0">
              <CardContent className="p-4 space-y-4">
                <div className="space-y-2">
                  <Label className="text-sm font-medium">Model Provider*</Label>
                  <div
                    className="text-sm px-3 py-2 rounded-md border text-gray-700 bg-gray-50"
                    data-testid="edit-aaj-provider-display"
                  >
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

            {testResult !== null && (
              <div
                className="w-full max-h-[7.5rem] overflow-y-auto rounded-md border border-gray-200 bg-gray-50 p-3"
                data-testid="edit-aaj-test-result"
              >
                <p
                  className={`text-sm whitespace-pre-wrap break-words ${
                    testResult ? "text-green-600" : "text-red-600"
                  }`}
                >
                  {testResult
                    ? "Test Passed"
                    : testError
                      ? `Test Failed: ${testError}`
                      : "Test Failed"}
                </p>
              </div>
            )}
          </div>

          <div className="shrink-0 pt-6 pb-6 border-t">
            <div className="flex justify-between items-center">
              <Button
                variant="outline"
                data-testid="edit-aaj-back"
                onClick={() => {
                  setTokenValue("");
                  setTestResult(null);
                  setTestError(null);
                  setTestedFingerprint(null);
                  onOpenChange(false);
                }}
              >
                Back
              </Button>
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  type="button"
                  data-testid="edit-aaj-test-connection"
                  disabled={testing}
                  onClick={() => void handleTest()}
                >
                  {testing ? "Testing…" : "Test Connection"}
                </Button>
                <Button
                  data-testid="edit-aaj-save"
                  onClick={() => void handleSave()}
                  disabled={saving || testing || !canSave}
                  className={
                    saving || testing || !canSave
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

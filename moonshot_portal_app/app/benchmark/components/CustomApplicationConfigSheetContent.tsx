'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Trash2, Plus } from 'lucide-react';
import {
  DEFAULT_RESPONSE_PATH,
  PROMPT_PLACEHOLDER,
  API_KEY_AUTH_SCHEME_OPTIONS,
} from '../constants/customAppConfig';
import type { ApiKeyAuthScheme } from '../constants/customAppConfig';
import type { CustomApplicationConfigFormState } from './useCustomApplicationConfigForm';
import type { HeaderRow, ParameterRow } from './customApplicationSheetShared';

const API_TYPE_OPTIONS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'] as const;

export type CustomApplicationConfigSheetContentProps = {
  form: CustomApplicationConfigFormState;
  title: string;
  sheetDescription: string;
  applicationLabel?: string;
};

export default function CustomApplicationConfigSheetContent({
  form,
  title,
  sheetDescription,
  applicationLabel = 'Custom Application*',
}: CustomApplicationConfigSheetContentProps) {
  const {
    open,
    onOpenChange,
    showResponsePath,
    connectionTestMode,
    currentModelApp,
    configName,
    setConfigName,
    apiType,
    setApiType,
    apiUrl,
    setApiUrl,
    apiBody,
    setApiBody,
    responsePath,
    setResponsePath,
    secretValue,
    setSecretValue,
    apiKeyConfigured,
    apiKeyAuthScheme,
    setApiKeyAuthScheme,
    apiKeyAuthCustomHeader,
    setApiKeyAuthCustomHeader,
    saving,
    connectionTesting,
    connectionTestAttempted,
    connectionTestResult,
    parameters,
    headers,
    autosaveStatus,
    autosaveStatusLabel,
    resetForm,
    handleSave,
    handleTestConnection,
    addParameter,
    removeParameter,
    updateParameter,
    addHeader,
    removeHeader,
    updateHeader,
  } = form;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="w-[1400px] sm:max-w-[700px] ml-4 pl-6 pr-6 flex flex-col overflow-hidden"
      >
        <div className="flex flex-col flex-1 min-h-0">
          <div className="flex-1 min-h-0 overflow-y-auto space-y-6 pb-6">
            <SheetHeader className="p-0">
              <SheetTitle className="sr-only">{title}</SheetTitle>
              <SheetDescription className="sr-only">{sheetDescription}</SheetDescription>
            </SheetHeader>

            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">{title}</h2>
            </div>

            <div className="space-y-2">
              <Label htmlFor="configName" className="text-sm font-medium">
                Configuration Name*
              </Label>
              <Input
                id="configName"
                placeholder="Enter configuration name"
                value={configName}
                onChange={(e) => setConfigName(e.target.value)}
                tabIndex={-1}
              />
            </div>

            <Card className="py-0 gap-0">
              <CardContent className="p-4 space-y-4">
                <div className="space-y-2">
                  <Label className="text-sm font-medium">{applicationLabel}</Label>
                  <div className="text-sm px-3 py-2 rounded-md border text-gray-700 bg-gray-50">
                    {currentModelApp?.name || 'No application selected'}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="apiType" className="text-sm font-medium">
                    API Type*
                  </Label>
                  <select
                    id="apiType"
                    value={apiType}
                    onChange={(e) => setApiType(e.target.value)}
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs"
                    tabIndex={-1}
                  >
                    {API_TYPE_OPTIONS.map((method) => (
                      <option key={method} value={method}>
                        {method}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="apiUrl" className="text-sm font-medium">
                    URL*
                  </Label>
                  <Input
                    id="apiUrl"
                    placeholder="https://api.example.com/v1/chat"
                    value={apiUrl}
                    onChange={(e) => setApiUrl(e.target.value)}
                    tabIndex={-1}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="apiBody" className="text-sm font-medium">
                    Request Body*
                  </Label>
                  <Textarea
                    id="apiBody"
                    placeholder={'{"messages": [{"role": "user", "content": "{{prompt}}"}]}'}
                    value={apiBody}
                    onChange={(e) => setApiBody(e.target.value)}
                    className="min-h-[120px] font-mono text-sm"
                    tabIndex={-1}
                  />
                  <p className="text-sm text-gray-600">
                    Include {PROMPT_PLACEHOLDER} where the benchmark prompt should be inserted.
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="apiKeyAuthScheme" className="text-sm font-medium">
                    Authorization Type*
                  </Label>
                  <select
                    id="apiKeyAuthScheme"
                    value={apiKeyAuthScheme}
                    onChange={(e) => setApiKeyAuthScheme(e.target.value as ApiKeyAuthScheme)}
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs"
                    tabIndex={-1}
                  >
                    {API_KEY_AUTH_SCHEME_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  <p className="text-sm text-gray-600">
                    {apiKeyAuthScheme === 'bearer'
                      ? 'Sends Authorization: Bearer <secret>'
                      : apiKeyAuthScheme === 'authorization_api_key'
                        ? 'Sends Authorization: ApiKey <secret>'
                        : apiKeyAuthScheme === 'x_api_key'
                          ? 'Sends X-API-Key: <secret>'
                          : apiKeyAuthScheme === 'x_api_key_lower'
                            ? 'Sends x-api-key: <secret>'
                            : 'Enter a custom header name below; the secret is sent as the header value.'}
                  </p>
                </div>

                {apiKeyAuthScheme === 'custom' ? (
                  <div className="space-y-2">
                    <Label htmlFor="apiKeyAuthCustomHeader" className="text-sm font-medium">
                      Custom Header*
                    </Label>
                    <Input
                      id="apiKeyAuthCustomHeader"
                      placeholder="e.g. X-API-Key:"
                      value={apiKeyAuthCustomHeader}
                      onChange={(e) => setApiKeyAuthCustomHeader(e.target.value)}
                      tabIndex={-1}
                    />
                  </div>
                ) : null}

                <div className="space-y-2">
                  <Label htmlFor="apiSecret" className="text-sm font-medium">
                    {apiKeyConfigured ? 'Authorization Secret (optional)' : 'Authorization Secret*'}
                  </Label>
                  <Input
                    id="apiSecret"
                    placeholder={
                      apiKeyConfigured && !secretValue
                        ? '••••••••'
                        : 'Enter Authorization secret'
                    }
                    type="password"
                    value={secretValue}
                    onChange={(e) => setSecretValue(e.target.value)}
                    tabIndex={-1}
                  />
                  {apiKeyConfigured ? (
                    <p className="text-sm text-gray-600">
                      Your secret has already been saved. No further action is needed unless you
                      would like to replace it with a new one.
                    </p>
                  ) : null}
                </div>
              </CardContent>
            </Card>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Parameters</h3>
                {autosaveStatusLabel ? (
                  <span
                    className={
                      autosaveStatus === 'error'
                        ? 'text-sm text-red-600'
                        : 'text-sm text-gray-500'
                    }
                  >
                    {autosaveStatusLabel}
                  </span>
                ) : null}
              </div>

              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="flex-1">
                    <Label className="text-sm font-medium text-gray-600">Parameter</Label>
                  </div>
                  <div className="flex-1">
                    <Label className="text-sm font-medium text-gray-600">Value</Label>
                  </div>
                  <div className="w-16"></div>
                </div>

                {parameters.map((param: ParameterRow, index: number) => (
                  <div key={index} className="flex items-center gap-3">
                    <div className="flex-1">
                      <Input
                        value={param.parameter}
                        onChange={(e) => updateParameter(index, 'parameter', e.target.value)}
                        tabIndex={-1}
                      />
                    </div>
                    <div className="flex-1">
                      <Input
                        value={param.value}
                        onChange={(e) => updateParameter(index, 'value', e.target.value)}
                        tabIndex={-1}
                      />
                    </div>
                    <div className="flex items-center gap-1 w-16">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeParameter(index)}
                        className="h-8 w-8 p-0"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                      {index === parameters.length - 1 && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={addParameter}
                          className="h-8 w-8 p-0"
                        >
                          <Plus className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                ))}

                {parameters.length === 0 && (
                  <div className="flex items-center gap-3">
                    <div className="flex-1"></div>
                    <div className="flex-1"></div>
                    <div className="flex items-center gap-1 w-16">
                      <div className="h-8 w-8"></div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={addParameter}
                        className="h-8 w-8 p-0"
                      >
                        <Plus className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Headers</h3>
              </div>

              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="flex-1">
                    <Label className="text-sm font-medium text-gray-600">Header</Label>
                  </div>
                  <div className="flex-1">
                    <Label className="text-sm font-medium text-gray-600">Value</Label>
                  </div>
                  <div className="w-16"></div>
                </div>

                {headers.map((row: HeaderRow, index: number) => (
                  <div key={index} className="flex items-center gap-3">
                    <div className="flex-1">
                      <Input
                        value={row.header}
                        onChange={(e) => updateHeader(index, 'header', e.target.value)}
                        tabIndex={-1}
                      />
                    </div>
                    <div className="flex-1">
                      <Input
                        value={row.value}
                        onChange={(e) => updateHeader(index, 'value', e.target.value)}
                        tabIndex={-1}
                      />
                    </div>
                    <div className="flex items-center gap-1 w-16">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeHeader(index)}
                        className="h-8 w-8 p-0"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                      {index === headers.length - 1 && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={addHeader}
                          className="h-8 w-8 p-0"
                        >
                          <Plus className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                ))}

                {headers.length === 0 && (
                  <div className="flex items-center gap-3">
                    <div className="flex-1"></div>
                    <div className="flex-1"></div>
                    <div className="flex items-center gap-1 w-16">
                      <div className="h-8 w-8"></div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={addHeader}
                        className="h-8 w-8 p-0"
                      >
                        <Plus className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-sm font-medium">Connection test response</Label>
              {connectionTestResult ? (
                <>
                  <p
                    className={
                      connectionTestResult.success
                        ? 'text-sm text-green-600'
                        : 'text-sm text-red-600'
                    }
                  >
                    {connectionTestResult.success
                      ? `Connection succeeded (HTTP ${connectionTestResult.status_code ?? '—'})`
                      : connectionTestResult.error ||
                        `Connection failed (HTTP ${connectionTestResult.status_code ?? '—'})`}
                  </p>
                  {connectionTestMode === 'bedrock_auto_parse' ? (
                    <p className="text-sm text-gray-600">
                      Bedrock Converse and OpenAI Responses replies are parsed automatically
                      (final text only; reasoning blocks are ignored).
                    </p>
                  ) : connectionTestResult.response_is_json &&
                    (connectionTestResult.response_leaves?.length ?? 0) > 0 ? (
                    <div className="max-h-48 overflow-y-auto rounded-md border bg-gray-50 p-3">
                      <div className="space-y-2">
                        <div className="flex items-start gap-3">
                          <div className="flex-1">
                            <Label className="text-xs font-medium text-gray-600">Path</Label>
                          </div>
                          <div className="flex-1">
                            <Label className="text-xs font-medium text-gray-600">Value</Label>
                          </div>
                        </div>
                        <p className="text-xs text-gray-600">
                          Click a path to set Response Path.
                        </p>
                        {connectionTestResult.response_leaves?.map((leaf, index) => (
                          <div key={index} className="flex items-start gap-3">
                            <div className="flex-1">
                              <button
                                type="button"
                                className="w-full text-left text-xs font-mono break-words text-gray-800 hover:bg-gray-100 hover:underline rounded px-1 py-0.5"
                                title="Click to use as Response Path"
                                onClick={() => setResponsePath(leaf.path)}
                              >
                                {leaf.path}
                              </button>
                            </div>
                            <div className="flex-1 text-xs font-mono break-words text-gray-800">
                              {leaf.value}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : connectionTestResult.response_is_json === false ? (
                    <>
                      <p className="text-sm text-gray-600">
                        Response is not JSON; showing raw body below.
                      </p>
                      <div className="max-h-48 overflow-y-auto rounded-md border bg-gray-50 p-3">
                        <pre className="text-xs font-mono whitespace-pre-wrap break-words">
                          {connectionTestResult.response_body ||
                            connectionTestResult.error ||
                            ''}
                        </pre>
                      </div>
                    </>
                  ) : (
                    <p className="text-sm text-gray-600">No scalar fields found.</p>
                  )}
                </>
              ) : (
                <p className="text-sm text-gray-600">
                  Run Test Connection to send a live request with the current form values.
                </p>
              )}
            </div>

            {showResponsePath && (
              <div className="space-y-2">
                <Label htmlFor="responsePath" className="text-sm font-medium">
                  Response Path*
                </Label>
                <Input
                  id="responsePath"
                  placeholder={DEFAULT_RESPONSE_PATH}
                  value={responsePath}
                  onChange={(e) => setResponsePath(e.target.value)}
                  className="font-mono text-sm"
                  tabIndex={-1}
                />
                <p className="text-sm text-gray-600">
                  JSONPath used to read the model reply from the API response.
                </p>
              </div>
            )}
          </div>

          <div className="shrink-0 pt-6 pb-6 border-t">
            <div className="flex justify-between items-center">
              <Button
                variant="outline"
                onClick={() => {
                  resetForm();
                  onOpenChange(false);
                }}
              >
                Back
              </Button>
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={() => void handleTestConnection()}
                  disabled={connectionTesting}
                >
                  {connectionTesting ? 'Testing…' : 'Test Connection'}
                </Button>
                <Button
                  onClick={() => void handleSave()}
                  disabled={!connectionTestAttempted || saving}
                  className={
                    !connectionTestAttempted ? 'opacity-50 bg-gray-100 text-gray-400' : ''
                  }
                >
                  {saving ? 'Saving…' : 'Save'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}

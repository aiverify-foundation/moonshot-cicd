import { fireEvent } from "@testing-library/react";
import { render, screen, waitFor } from "@/tests/utils/test-utils";
import TestResultApp from "@/app/test_result/components/TestResultApp";
import React from "react";
import { FeatureFlagNames } from "@/lib/featureFlags";
import { ApiError, adapterNotFoundMessage, ADAPTER_NOT_FOUND_CODE } from "@/lib/api";

const mockFetchBenchmarkRunResults = jest.fn();
const mockDownloadResults = jest.fn();
const mockStartRegenerateFailed = jest.fn();
const mockFetchRegenerateProgress = jest.fn();

jest.mock("@/app/test_result/components/TestResultOverview", () => ({
  __esModule: true,
  default: () => <div data-testid="overview-mock" />,
}));

jest.mock("@/app/test_result/components/TestResultBundle", () => ({
  __esModule: true,
  default: () => null,
}));

jest.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams("runId=12"),
}));

jest.mock("@/hooks/useFeatureFlags", () => ({
  useFeatureFlags: () => ({
    flags: {},
    loading: false,
    isEnabled: (name: string) => name === FeatureFlagNames.AIVET_OCT2026_MOON793,
  }),
}));

jest.mock("@/lib/api", () => {
  const actual = jest.requireActual("@/lib/api") as Record<string, unknown>;
  return {
    ...actual,
    fetchBenchmarkRunResults: (...args: unknown[]) =>
      mockFetchBenchmarkRunResults(...args),
    downloadBenchmarkRunResults: (...args: unknown[]) =>
      mockDownloadResults(...args),
    startRegenerateFailedBenchmarkRunPrompts: (...args: unknown[]) =>
      mockStartRegenerateFailed(...args),
    fetchRegenerateFailedPromptsProgress: (...args: unknown[]) =>
      mockFetchRegenerateProgress(...args),
  };
});

function adapterError(action: string) {
  return new ApiError(
    adapterNotFoundMessage(
      { adapter_type: "metric", adapter_name: "gone_metric" },
      action
    ),
    409,
    "Conflict",
    ADAPTER_NOT_FOUND_CODE,
    { type: "metric", name: "gone_metric" }
  );
}

describe("TestResultApp adapter-not-found errors", () => {
  beforeEach(() => {
    mockFetchBenchmarkRunResults.mockResolvedValue({
      run: {
        id: 12,
        name: "Acme run",
        status: "completed",
        endpoint_type: "openai",
        endpoint_config_name: "gpt-4",
      },
      bundles: [],
      prompts: [
        {
          id: 1,
          run_test_id: 1,
          prompt_id: 1,
          status: "error",
          test_id: 101,
          test_name: "Hate",
          score: 0,
          error_source: "metric",
        },
      ],
      test_margin_of_error: [],
      test_run_status: [],
    });
    mockFetchRegenerateProgress.mockResolvedValue({
      run_id: 12,
      status: "idle",
      total: 0,
      done: 0,
      failed: 0,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("shows the friendly message when export fails because an adapter is missing", async () => {
    mockDownloadResults.mockRejectedValue(adapterError("exporting results"));
    render(<TestResultApp />);

    fireEvent.click(await screen.findByTestId("download-results-button"));

    expect(
      await screen.findByText(/no longer installed on the server, so exporting results/)
    ).toBeInTheDocument();
  });

  it("shows the friendly message when a bulk rerun fails because an adapter is missing", async () => {
    mockStartRegenerateFailed.mockRejectedValue(
      adapterError("re-running failed prompts")
    );
    render(<TestResultApp />);

    fireEvent.click(await screen.findByTestId("regenerate-failed-prompts-button"));

    await waitFor(() => {
      expect(
        screen.getByText(/so re-running failed prompts is unavailable/)
      ).toBeInTheDocument();
    });
  });
});

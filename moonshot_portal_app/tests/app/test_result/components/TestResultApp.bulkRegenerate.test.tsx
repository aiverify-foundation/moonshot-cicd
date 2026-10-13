import { render, screen, waitFor } from "@/tests/utils/test-utils";
import TestResultApp from "@/app/test_result/components/TestResultApp";
import React from "react";
import { FeatureFlagNames } from "@/lib/featureFlags";

const mockFetchBenchmarkRunResults = jest.fn();
const mockStartRegenerateFailed = jest.fn();
const mockFetchRegenerateProgress = jest.fn();
const mockIsEnabled = jest.fn();

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
    isEnabled: (name: string) => mockIsEnabled(name),
  }),
}));

jest.mock("@/lib/api", () => {
  const actual = jest.requireActual("@/lib/api") as Record<string, unknown>;
  return {
    ...actual,
    fetchBenchmarkRunResults: (...args: unknown[]) =>
      mockFetchBenchmarkRunResults(...args),
    downloadBenchmarkRunResults: jest.fn(),
    startRegenerateFailedBenchmarkRunPrompts: (...args: unknown[]) =>
      mockStartRegenerateFailed(...args),
    fetchRegenerateFailedPromptsProgress: (...args: unknown[]) =>
      mockFetchRegenerateProgress(...args),
  };
});

function completedRunWithPrompts(
  prompts: Array<Record<string, unknown>>
) {
  return {
    run: {
      id: 12,
      name: "Acme run",
      status: "completed",
      endpoint_type: "openai",
      endpoint_config_name: "gpt-4",
    },
    bundles: [],
    prompts,
    test_margin_of_error: [],
    test_run_status: [],
  };
}

describe("TestResultApp bulk regenerate failed prompts", () => {
  beforeEach(() => {
    mockIsEnabled.mockImplementation(
      (name: string) => name === FeatureFlagNames.AIVET_OCT2026_MOON793
    );
    mockStartRegenerateFailed.mockResolvedValue({
      message: "Regeneration started.",
      total: 2,
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

  it("hides the button when the feature flag is off", async () => {
    mockIsEnabled.mockReturnValue(false);
    mockFetchBenchmarkRunResults.mockResolvedValue(
      completedRunWithPrompts([
        {
          id: 1,
          run_test_id: 1,
          prompt_id: 1,
          status: "error",
          test_id: 101,
          test_name: "Hate",
          score: 0,
        },
      ])
    );

    render(<TestResultApp />);

    await waitFor(() => {
      expect(screen.getByTestId("test-result-report-name")).toHaveTextContent(
        "Acme run"
      );
    });

    expect(
      screen.queryByTestId("regenerate-failed-prompts-button")
    ).not.toBeInTheDocument();
  });

  it("hides the button when there are no errored prompts", async () => {
    mockFetchBenchmarkRunResults.mockResolvedValue(
      completedRunWithPrompts([
        {
          id: 1,
          run_test_id: 1,
          prompt_id: 1,
          status: "completed",
          test_id: 101,
          test_name: "Hate",
          score: 0.9,
        },
      ])
    );

    render(<TestResultApp />);

    await waitFor(() => {
      expect(screen.getByTestId("test-result-report-name")).toHaveTextContent(
        "Acme run"
      );
    });

    expect(
      screen.queryByTestId("regenerate-failed-prompts-button")
    ).not.toBeInTheDocument();
  });

  it("shows the button when the flag is on and prompts have errors", async () => {
    mockFetchBenchmarkRunResults.mockResolvedValue(
      completedRunWithPrompts([
        {
          id: 1,
          run_test_id: 1,
          prompt_id: 1,
          status: "error",
          test_id: 101,
          test_name: "Hate",
          score: 0,
          error_source: "connector",
        },
        {
          id: 2,
          run_test_id: 1,
          prompt_id: 2,
          status: "error",
          test_id: 101,
          test_name: "Hate",
          score: 0,
          error_source: "metric",
        },
      ])
    );

    render(<TestResultApp />);

    await waitFor(() => {
      expect(
        screen.getByTestId("regenerate-failed-prompts-button")
      ).toBeInTheDocument();
    });

    expect(
      screen.getByTestId("regenerate-failed-prompts-button")
    ).toHaveTextContent("Regenerate failed prompts");
  });
});

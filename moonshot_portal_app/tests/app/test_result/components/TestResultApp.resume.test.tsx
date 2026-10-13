import { render, screen, waitFor } from "@/tests/utils/test-utils";
import userEvent from "@testing-library/user-event";
import TestResultApp from "@/app/test_result/components/TestResultApp";
import React from "react";
import { FeatureFlagNames } from "@/lib/featureFlags";

const mockFetchBenchmarkRunResults = jest.fn();
const mockResumeBenchmarkRun = jest.fn();
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
    resumeBenchmarkRun: (...args: unknown[]) => mockResumeBenchmarkRun(...args),
    startRegenerateFailedBenchmarkRunPrompts: jest.fn(),
    fetchRegenerateFailedPromptsProgress: jest.fn(),
  };
});

function runPayload(overrides: {
  status?: string;
  prompts?: Array<Record<string, unknown>>;
  test_run_status?: Array<Record<string, unknown>>;
}) {
  return {
    run: {
      id: 12,
      name: "Acme run",
      status: overrides.status ?? "failed",
      endpoint_type: "openai",
      endpoint_config_name: "gpt-4",
    },
    bundles: [],
    prompts: overrides.prompts ?? [],
    test_margin_of_error: [],
    test_run_status: overrides.test_run_status ?? [],
  };
}

describe("TestResultApp resume incomplete run", () => {
  beforeEach(() => {
    mockIsEnabled.mockImplementation(
      (name: string) => name === FeatureFlagNames.AIVET_OCT2026_MOON796
    );
    mockResumeBenchmarkRun.mockResolvedValue({
      message: "Benchmark run resume started.",
      run_id: 12,
      resumed_test_count: 1,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("hides the button when the feature flag is off", async () => {
    mockIsEnabled.mockReturnValue(false);
    mockFetchBenchmarkRunResults.mockResolvedValue(
      runPayload({
        prompts: [
          {
            id: 1,
            run_test_id: 1,
            prompt_id: 1,
            status: "pending",
            test_id: 101,
            test_name: "Hate",
          },
        ],
      })
    );

    render(<TestResultApp />);

    await waitFor(() => {
      expect(screen.getByTestId("test-result-report-name")).toHaveTextContent(
        "Acme run"
      );
    });

    expect(screen.queryByTestId("resume-run-button")).not.toBeInTheDocument();
  });

  it("hides the button when there is no incomplete work", async () => {
    mockFetchBenchmarkRunResults.mockResolvedValue(
      runPayload({
        status: "completed",
        prompts: [
          {
            id: 1,
            run_test_id: 1,
            prompt_id: 1,
            status: "completed",
            test_id: 101,
            test_name: "Hate",
            score: 0.9,
          },
        ],
        test_run_status: [
          { id: 1, run_id: 12, test_id: 101, status: "completed" },
        ],
      })
    );

    render(<TestResultApp />);

    await waitFor(() => {
      expect(screen.getByTestId("test-result-report-name")).toHaveTextContent(
        "Acme run"
      );
    });

    expect(screen.queryByTestId("resume-run-button")).not.toBeInTheDocument();
  });

  it("shows the button when the flag is on and prompts are pending", async () => {
    mockFetchBenchmarkRunResults.mockResolvedValue(
      runPayload({
        prompts: [
          {
            id: 1,
            run_test_id: 1,
            prompt_id: 1,
            status: "pending",
            test_id: 101,
            test_name: "Hate",
          },
        ],
        test_run_status: [
          { id: 1, run_id: 12, test_id: 101, status: "in_progress" },
        ],
      })
    );

    render(<TestResultApp />);

    await waitFor(() => {
      expect(screen.getByTestId("resume-run-button")).toBeInTheDocument();
    });

    expect(screen.getByTestId("resume-run-button")).toHaveTextContent("Resume");
  });

  it("calls resume API and flips status to running", async () => {
    const user = userEvent.setup();
    mockFetchBenchmarkRunResults
      .mockResolvedValueOnce(
        runPayload({
          status: "failed",
          prompts: [
            {
              id: 1,
              run_test_id: 1,
              prompt_id: 1,
              status: "pending",
              test_id: 101,
              test_name: "Hate",
            },
          ],
          test_run_status: [
            { id: 1, run_id: 12, test_id: 101, status: "in_progress" },
          ],
        })
      )
      .mockResolvedValue(
        runPayload({
          status: "running",
          prompts: [
            {
              id: 1,
              run_test_id: 1,
              prompt_id: 1,
              status: "pending",
              test_id: 101,
              test_name: "Hate",
            },
          ],
          test_run_status: [
            { id: 1, run_id: 12, test_id: 101, status: "not_started" },
          ],
        })
      );

    render(<TestResultApp />);

    const resumeButton = await screen.findByTestId("resume-run-button");
    await user.click(resumeButton);

    await waitFor(() => {
      expect(mockResumeBenchmarkRun).toHaveBeenCalledWith(12);
    });

    await waitFor(() => {
      expect(screen.getByTestId("test-result-status-badge")).toHaveTextContent(
        "In Progress"
      );
    });
  });
});

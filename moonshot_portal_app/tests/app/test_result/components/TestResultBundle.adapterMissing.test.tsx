import { render, screen, waitFor } from "@/tests/utils/test-utils";
import TestResultBundle from "@/app/test_result/components/TestResultBundle";
import type { BenchmarkRunTestPrompt } from "@/lib/api";
import React from "react";

const mockFetchMetricScoreResultNames = jest.fn();

jest.mock("@/app/test_result/components/BundleChart", () => ({
  __esModule: true,
  default: () => <div data-testid="bundle-chart-mock" />,
}));

jest.mock("@/app/test_result/components/TestResultTable", () => ({
  __esModule: true,
  default: () => <div data-testid="result-table-mock" />,
}));

jest.mock("@/lib/api", () => {
  const actual = jest.requireActual("@/lib/api") as Record<string, unknown>;
  return {
    ...actual,
    fetchMetricScoreResultNames: (...args: unknown[]) =>
      mockFetchMetricScoreResultNames(...args),
  };
});

function prompt(metricName: string): BenchmarkRunTestPrompt {
  return {
    id: 1,
    run_test_id: 1,
    prompt_id: 1,
    status: "completed",
    test_id: 101,
    test_name: "Hate",
    metric_name: metricName,
    score: 1,
  };
}

describe("TestResultBundle missing metric adapter notice", () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it("shows the notice when the metric adapter is missing on the server", async () => {
    mockFetchMetricScoreResultNames.mockResolvedValue({
      metric_name: "gone_metric",
      result_pass: "True",
      result_fail: "False",
      adapter_missing: true,
    });

    render(<TestResultBundle apiPrompts={[prompt("gone_metric")]} />);

    const notice = await screen.findByTestId("metric-adapter-missing-notice");
    expect(notice).toHaveTextContent("gone_metric");
    expect(notice).toHaveTextContent("no longer installed on the server");
  });

  it("does not show the notice when the metric labels load normally", async () => {
    mockFetchMetricScoreResultNames.mockResolvedValue({
      metric_name: "good_metric",
      result_pass: "safe",
      result_fail: "unsafe",
    });

    render(<TestResultBundle apiPrompts={[prompt("good_metric")]} />);

    await waitFor(() => {
      expect(mockFetchMetricScoreResultNames).toHaveBeenCalledWith("good_metric");
    });
    expect(
      screen.queryByTestId("metric-adapter-missing-notice")
    ).not.toBeInTheDocument();
  });

  it("does not look up labels or show the notice when the run has several metrics", async () => {
    render(
      <TestResultBundle
        apiPrompts={[
          prompt("metric_a"),
          { ...prompt("metric_b"), id: 2, prompt_id: 2, test_id: 102 },
        ]}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId("bundle-chart-mock")).toBeInTheDocument();
    });
    expect(mockFetchMetricScoreResultNames).not.toHaveBeenCalled();
    expect(
      screen.queryByTestId("metric-adapter-missing-notice")
    ).not.toBeInTheDocument();
  });
});

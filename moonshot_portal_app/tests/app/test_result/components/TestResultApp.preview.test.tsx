import { render, screen, waitFor } from "@/tests/utils/test-utils";
import TestResultApp from "@/app/test_result/components/TestResultApp";
import React from "react";

const mockFetchBenchmarkRunResults = jest.fn();

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

jest.mock("@/lib/api", () => {
  const actual = jest.requireActual("@/lib/api") as Record<string, unknown>;
  return {
    ...actual,
    fetchBenchmarkRunResults: (...args: unknown[]) =>
      mockFetchBenchmarkRunResults(...args),
    downloadBenchmarkRunResults: jest.fn(),
  };
});

describe("TestResultApp PDF preview link", () => {
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
          run_test_id: 1,
          prompt_id: 1,
          status: "completed",
          test_id: 101,
          test_name: "Hate",
          score: 0.9,
        },
      ],
      test_margin_of_error: [],
      test_run_status: [],
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("links Preview PDF to the preview page for a completed run", async () => {
    render(<TestResultApp />);

    await waitFor(() => {
      expect(screen.getByTestId("preview-pdf-button")).toBeInTheDocument();
    });

    const link = screen.getByTestId("preview-pdf-button");
    expect(link).toHaveAttribute("href", "/test_result/preview/?runId=12");
    expect(link).toHaveTextContent("Preview PDF");
  });
});

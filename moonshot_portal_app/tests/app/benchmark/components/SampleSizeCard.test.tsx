import userEvent from '@testing-library/user-event';
import { render, screen } from '@/tests/utils/test-utils';
import SampleSizeCard, {
  buildSampleSizeInterpretation,
  calculateSampleSize,
  getConfidenceIntervalBounds,
} from '@/app/benchmark/components/SampleSizeCard';
import type { Bundle } from '@/lib/api';

const mockBundles: Bundle[] = [
  {
    id: 'safety-bundle',
    name: 'Safety Bundle',
    description: 'Bundle description',
    category: 'Safety',
    tests: [
      {
        name: 'Test One',
        dataset: {
          id: 'ds-1',
          name: 'ds-1',
          description: '',
          num_of_dataset_prompts: 42,
        },
      },
    ],
    prompt_count: 42,
  },
];

const mockBundlesMultiTest: Bundle[] = [
  {
    id: 'safety-bundle',
    name: 'Safety Bundle',
    description: 'Bundle description',
    category: 'Safety',
    tests: [
      {
        name: 'Test One',
        dataset: {
          id: 'ds-1',
          name: 'ds-1',
          description: '',
          num_of_dataset_prompts: 42,
        },
      },
      {
        name: 'Test Two',
        dataset: {
          id: 'ds-2',
          name: 'ds-2',
          description: '',
          num_of_dataset_prompts: 58,
        },
      },
    ],
    prompt_count: 100,
  },
];

describe('calculateSampleSize', () => {
  it('returns rounded-up sample size for 95% confidence, 5% margin, p=0.5', () => {
    expect(calculateSampleSize(95, 5, 0.5)).toBe(385);
  });
});

describe('getConfidenceIntervalBounds', () => {
  it('returns bounds for a typical test score and margin', () => {
    expect(getConfidenceIntervalBounds(90, 3)).toEqual({ lower: 87, upper: 93 });
  });

  it('clamps lower bound to 0', () => {
    expect(getConfidenceIntervalBounds(2, 3)).toEqual({ lower: 0, upper: 5 });
  });
});

describe('buildSampleSizeInterpretation', () => {
  it('builds default interpretation copy for a single test', () => {
    expect(
      buildSampleSizeInterpretation({
        testScorePct: 90,
        perTestSampleSize: 385,
        confidenceLevelPct: 95,
        lower: 87,
        upper: 93,
        numberOfSelectedTests: 1,
      })
    ).toBe(
      'How to interpret: For a test score of 90%, 385 or more prompts are needed to have a confidence level of 95% that the real value is 87%-93%'
    );
  });

  it('includes per test wording when multiple tests are selected', () => {
    expect(
      buildSampleSizeInterpretation({
        testScorePct: 90,
        perTestSampleSize: 385,
        confidenceLevelPct: 95,
        lower: 87,
        upper: 93,
        numberOfSelectedTests: 2,
      })
    ).toContain('385 or more prompts per test');
  });
});

describe('SampleSizeCard', () => {
  beforeAll(() => {
    global.ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
    Element.prototype.scrollIntoView = jest.fn();
  });

  it('defaults to All prompts, hides Test Run, and disables Calculated', async () => {
    render(<SampleSizeCard />, {
      preloadedState: {
        bundles: { data: mockBundles, loading: false, error: null },
        bundleSelection: { 'safety-bundle': true },
        testSelection: { 'safety-bundle': { 'Test One': true } },
      },
    });

    expect(screen.queryByRole('button', { name: /Test Run/i })).not.toBeInTheDocument();

    const calculatedToggle = screen.getByRole('button', {
      name: /Calculated — under development/i,
    });
    const allPromptsToggle = screen.getByRole('button', { name: /All prompts/i });

    expect(calculatedToggle).toBeDisabled();
    expect(allPromptsToggle).toHaveAttribute('data-state', 'on');
    expect(calculatedToggle).toHaveAttribute('data-state', 'off');

    await userEvent.click(calculatedToggle);
    expect(allPromptsToggle).toHaveAttribute('data-state', 'on');
  });

  it('shows default interpretation text for one selected test', () => {
    render(<SampleSizeCard />, {
      preloadedState: {
        bundles: { data: mockBundles, loading: false, error: null },
        bundleSelection: { 'safety-bundle': true },
        testSelection: { 'safety-bundle': { 'Test One': true } },
      },
    });

    const interpretation = screen.getByTestId('sample-size-interpretation');
    expect(interpretation).toHaveTextContent(
      'How to interpret: For a test score of 90%, 385 or more prompts are needed to have a confidence level of 95% that the real value is 87%-93%'
    );
    expect(screen.getByText(/Recommended sample size: 385 prompts/i)).toBeInTheDocument();
  });

  it('updates interpretation when margin of error changes', async () => {
    const user = userEvent.setup();

    render(<SampleSizeCard />, {
      preloadedState: {
        bundles: { data: mockBundles, loading: false, error: null },
        bundleSelection: { 'safety-bundle': true },
        testSelection: { 'safety-bundle': { 'Test One': true } },
      },
    });

    await user.click(screen.getByTestId('margin-of-error-combobox-trigger'));
    await user.click(screen.getByTestId('margin-of-error-option-5'));

    const interpretation = screen.getByTestId('sample-size-interpretation');
    expect(interpretation).toHaveTextContent('that the real value is 85%-95%');
    expect(interpretation).not.toHaveTextContent('87%-93%');
  });

  it('shows per-test wording and total recommended size for multiple tests', () => {
    render(<SampleSizeCard />, {
      preloadedState: {
        bundles: { data: mockBundlesMultiTest, loading: false, error: null },
        bundleSelection: { 'safety-bundle': true },
        testSelection: {
          'safety-bundle': { 'Test One': true, 'Test Two': true },
        },
      },
    });

    expect(screen.getByTestId('sample-size-interpretation')).toHaveTextContent(
      '385 or more prompts per test'
    );
    expect(screen.getByText(/Recommended sample size: 770 prompts/i)).toBeInTheDocument();
  });
});

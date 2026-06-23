import userEvent from '@testing-library/user-event';
import { render, screen } from '@/tests/utils/test-utils';
import SampleSizeCard, {
  buildSampleSizeInterpretation,
  calculateAdjustedSampleSize,
  calculateSampleSize,
  getConfidenceIntervalBounds,
  hasTestsWithInsufficientPrompts,
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

const mockBundlesSufficientPrompts: Bundle[] = [
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
          num_of_dataset_prompts: 500,
        },
      },
    ],
    prompt_count: 500,
  },
];

const mockBundlesMixedPrompts: Bundle[] = [
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
          num_of_dataset_prompts: 500,
        },
      },
    ],
    prompt_count: 542,
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

describe('calculateAdjustedSampleSize', () => {
  it('uses full dataset size for tests below the per-test recommendation', () => {
    expect(calculateAdjustedSampleSize(385, [42, 500])).toBe(427);
  });

  it('caps each test at the per-test recommendation when datasets are large enough', () => {
    expect(calculateAdjustedSampleSize(385, [500, 600])).toBe(770);
  });
});

describe('hasTestsWithInsufficientPrompts', () => {
  it('returns true when any test has fewer prompts than recommended', () => {
    expect(hasTestsWithInsufficientPrompts(385, [42])).toBe(true);
  });

  it('returns false when all tests meet the recommended per-test size', () => {
    expect(hasTestsWithInsufficientPrompts(385, [500])).toBe(false);
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

  it('shows warning and adjusted calculated count when a test has insufficient prompts', () => {
    render(<SampleSizeCard />, {
      preloadedState: {
        bundles: { data: mockBundles, loading: false, error: null },
        bundleSelection: { 'safety-bundle': true },
        testSelection: { 'safety-bundle': { 'Test One': true } },
      },
    });

    expect(screen.getByTestId('sample-size-insufficient-prompts-warning')).toHaveTextContent(
      'Some test(s) contain fewer prompts than recommended. If you proceed, the full prompt dataset for the affected test(s) will be used.'
    );
    expect(screen.getByText(/Recommended sample size: 385 prompts/i)).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /Calculated — under development \(42\)/i })
    ).toBeInTheDocument();
  });

  it('does not show warning when all selected tests have enough prompts', () => {
    render(<SampleSizeCard />, {
      preloadedState: {
        bundles: { data: mockBundlesSufficientPrompts, loading: false, error: null },
        bundleSelection: { 'safety-bundle': true },
        testSelection: { 'safety-bundle': { 'Test One': true } },
      },
    });

    expect(screen.queryByTestId('sample-size-insufficient-prompts-warning')).not.toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /Calculated — under development \(385\)/i })
    ).toBeInTheDocument();
  });

  it('shows warning and mixed calculated total for multiple tests with mixed prompt counts', () => {
    render(<SampleSizeCard />, {
      preloadedState: {
        bundles: { data: mockBundlesMixedPrompts, loading: false, error: null },
        bundleSelection: { 'safety-bundle': true },
        testSelection: {
          'safety-bundle': { 'Test One': true, 'Test Two': true },
        },
      },
    });

    expect(screen.getByTestId('sample-size-insufficient-prompts-warning')).toBeInTheDocument();
    expect(screen.getByText(/Recommended sample size: 770 prompts/i)).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /Calculated — under development \(427\)/i })
    ).toBeInTheDocument();
  });
});
